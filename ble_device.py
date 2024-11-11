import ubluetooth
import ble_advertising
import time

class BLEDevice:
    def __init__(self, name, handle_wifi_credentials):
        print("BLEDevice init")
        self.name = name
        self.handle_wifi_credentials = handle_wifi_credentials
        self.ble = ubluetooth.BLE()
        self.ble.active(True)
        self.ble.irq(self.on_ble_event)
        self.wifi_connected = False
        
        # Define UUIDs and characteristics for Wi-Fi credentials
        SERVICE_UUID = ubluetooth.UUID("0000180F-0000-1000-8000-00805F9B34FB")
        WIFI_CREDENTIALS_UUID = ubluetooth.UUID("00002A1A-0000-1000-8000-00805F9B34FB")
        WIFI_STATUS_UUID = ubluetooth.UUID("00002A1B-0000-1000-8000-00805F9B34FB")  # New UUID for status

        self.ble.config(gap_name=name)

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
    
    def disconnect(self):
        self.ble.gap_advertise(0, None)
        self.ble.active(False)
        self.ble = None
    
    def await_credentials(self):
        while not self.wifi_connected:
            time.sleep(3)
            self.ping_for_wifi_credentials()
    
    def start_advertising(self):
        adv_data = ble_advertising.advertising_payload(name=self.name)
        self.ble.gap_advertise(100, adv_data)  # 100ms interval
        print(f"Advertising as '{self.name}'")        
    
    def notify_wifi_status(self, status):
        self.ble.gatts_notify(0, self.status_handle, status)
        if status == b"CONNECTED":
            self.wifi_connected = True

    def on_ble_event(self, event, data):
        if event == 1:  # BLE connect event
            print("BLE connected")
            self.received_data = bytearray()  # Reset received data on new connection
        elif event == 2:  # BLE disconnect event
            print("BLE disconnected")
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
                            self.handle_wifi_credentials(self.wifi_ssid, self.wifi_pass, self.notify_wifi_status)
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


    def ping_for_wifi_credentials(self):
        if self.wlan:
            if self.wlan.isconnected():
                print(f"WiFi credentails: {self.wifi_ssid}, {self.wifi_pass}")
            else:
                print("Not connected to WiFi")
        else:
            print("No WiFi credentials set")
