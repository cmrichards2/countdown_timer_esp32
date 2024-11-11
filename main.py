import ubluetooth
import ble_advertising
import network
import time
from button import Button
from machine import Pin


class Application:
    def __init__(self):
        self.name = "ESP32_Device"
    
    def start(self):
        self.switch = Button(25, self.switch_handler)

        time.sleep(8)

        print("BLEDevice init")
        ble_device = BLEDevice()

        while True:
            time.sleep(3)
            ble_device.ping_for_wifi_credentials()
            print("BLEDevice loop")

    def switch_handler(self):
        print("Switch is pressed!")

class BLEDevice:
    def __init__(self):
        print("BLEDevice init")
        self.ble = ubluetooth.BLE()
        self.ble.active(True)
        self.ble.irq(self.on_ble_event)
        
        # Define UUIDs and characteristics for Wi-Fi credentials
        SERVICE_UUID = ubluetooth.UUID("0000180F-0000-1000-8000-00805F9B34FB")
        WIFI_CREDENTIALS_UUID = ubluetooth.UUID("00002A1A-0000-1000-8000-00805F9B34FB")
        WIFI_STATUS_UUID = ubluetooth.UUID("00002A1B-0000-1000-8000-00805F9B34FB")  # New UUID for status

        self.ble.config(gap_name="ESP32_Device")

        self.service = (
            SERVICE_UUID, 
            (
                (WIFI_CREDENTIALS_UUID, ubluetooth.FLAG_WRITE),
                (WIFI_STATUS_UUID, ubluetooth.FLAG_NOTIFY),  # New characteristic
            )
        )
        ((self.characteristic_handle, self.status_handle),) = self.ble.gatts_register_services((self.service,))
        
        self.start_advertising()

        self.wlan = None
        self.wifi_ssid = None
        self.wifi_pass = None
        self.received_data = bytearray()  # Add this line to store received chunks
    
    def start_advertising(self):
        adv_data = ble_advertising.advertising_payload(name="ESP32_Device")
        self.ble.gap_advertise(100, adv_data)  # 100ms interval
        print("Advertising as 'ESP32_Device'")        

    def on_ble_event(self, event, data):
        if event == 1:  # BLE connect event
            print("BLE connected")
            self.received_data = bytearray()  # Reset received data on new connection
        elif event == 2:  # BLE disconnect event
            print("BLE disconnected")
            self.start_advertising()
        elif event == 3:  # Write request
            buffer = self.ble.gatts_read(self.characteristic_handle)
            if buffer:
                try:
                    # Check if this is the END marker
                    if buffer == b"END":
                        # Process complete data
                        decoded = self.received_data.decode("utf-8")
                        print(f"Received complete data: {decoded}")
                        creds = decoded.split("|")
                        if len(creds) == 2:
                            self.wifi_ssid = creds[0]
                            self.wifi_pass = creds[1]
                            print(f"SSID: {self.wifi_ssid}, Password: {self.wifi_pass}")
                            self.connect_to_wifi()
                        else:
                            print("Invalid credential format")
                        # Reset the buffer
                        self.received_data = bytearray()
                    else:
                        # Append the chunk to received_data
                        self.received_data.extend(buffer)
                        print(f"Received chunk, current length: {len(self.received_data)}")
                except Exception as e:
                    print(f"Error processing data: {e}")

    def connect_to_wifi(self):
        if self.wifi_ssid and self.wifi_pass:
            try:
                self.wlan = network.WLAN(network.STA_IF)
                self.wlan.active(True)
                # Send "connecting" status
                self.ble.gatts_notify(0, self.status_handle, b"CONNECTING")
                
                self.wlan.connect(self.wifi_ssid, self.wifi_pass)
                
                # Wait for connection with timeout
                retry_count = 0
                while not self.wlan.isconnected() and retry_count < 10:
                    time.sleep(1)
                    retry_count += 1
                
                if self.wlan.isconnected():
                    print("Connected to WiFi:", self.wlan.ifconfig())
                    # Send success status
                    self.ble.gatts_notify(0, self.status_handle, b"CONNECTED")
                else:
                    print("Failed to connect to WiFi")
                    # Send failure status
                    self.ble.gatts_notify(0, self.status_handle, b"FAILED")
            except Exception as e:
                print(f"Error connecting to WiFi: {e}")
                # Send error status
                self.ble.gatts_notify(0, self.status_handle, f"ERROR:{str(e)}".encode())

    def ping_for_wifi_credentials(self):
        if self.wlan:
            if self.wlan.isconnected():
                print(f"WiFi credentails: {self.wifi_ssid}, {self.wifi_pass}")
            else:
                print("Not connected to WiFi")
        else:
            print("No WiFi credentials set")


app = Application()
app.start()
