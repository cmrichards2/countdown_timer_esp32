import ubluetooth
import ble_advertising
import time
from led_fader import LEDFader
from config import PIN_CONFIG, BLE_CONFIG

class BLEDevice:
    def __init__(self, name, handle_wifi_credentials):
        self.name = name
        self.handle_wifi_credentials = handle_wifi_credentials
        self.wifi_connected = False
        self.wlan = None
        self.wifi_ssid = None
        self.wifi_pass = None
        self.received_data = bytearray()

        self.led_fader = LEDFader(PIN_CONFIG["STATUS_LED"])
        self.setup_bluetooth_service()
        self.start_bluetooth_advertising()

    def setup_bluetooth_service(self):
        # Use UUIDs from config
        SERVICE_UUID = ubluetooth.UUID(BLE_CONFIG["SERVICE_UUID"])
        WIFI_CREDENTIALS_UUID = ubluetooth.UUID(BLE_CONFIG["WIFI_CREDENTIALS_UUID"])
        WIFI_STATUS_UUID = ubluetooth.UUID(BLE_CONFIG["WIFI_STATUS_UUID"])

        self.ble = ubluetooth.BLE()
        self.ble.active(True)
        self.ble.irq(self.on_ble_event)
        self.ble.config(gap_name=self.name)
        self.service = (
            SERVICE_UUID, 
            (
                (WIFI_CREDENTIALS_UUID, ubluetooth.FLAG_WRITE),
                (WIFI_STATUS_UUID, ubluetooth.FLAG_NOTIFY),
            )
        )
        ((self.characteristic_handle, self.status_handle),) = self.ble.gatts_register_services((self.service,))

    def disconnect(self):
        self.ble.gap_advertise(0, None)
        self.ble.active(False)
        self.led_fader.stop()
        self.ble = None
    
    def await_credentials(self):
        while not self.wifi_connected:
            time.sleep(3)
            self.show_status()

    def start_bluetooth_advertising(self):
        adv_data = ble_advertising.advertising_payload(name=self.name)
        self.ble.gap_advertise(BLE_CONFIG["ADVERTISING_INTERVAL_MS"], adv_data)
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

    def show_status(self):
        if self.wlan:
            if self.wlan.isconnected():
                print(f"WiFi credentails: {self.wifi_ssid}, {self.wifi_pass}")
            else:
                print("Not connected to WiFi")
        else:
            print("No WiFi credentials set")
