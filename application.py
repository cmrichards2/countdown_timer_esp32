import time
from ble_device import BLEDevice
from button import Button
from wifi_connection import WifiConnection
from config import Config

# This application class is the main entry point for the application.
# It handles entering pairing mode, connecting to WiFi, and starting the main application loop.

class Application:
    def __init__(self, bluetooth_name):
        self.bluetooth_name = bluetooth_name
        self.button = Button(Config.BUTTON_PIN, self.on_button_pressed)
        self.wifi = WifiConnection(Config.WIFI_CREDENTIALS_FILE)
        self.ble_device = None
    
    def start(self):
        """
        Main entry point that handles the application's connection flow:
        
        1. First attempts to connect using stored WiFi credentials if they exist
        2. If connected successfully, enters the main application loop
        3. If connection fails or no credentials exist, enters Bluetooth pairing mode where 
           the device will wait for the mobile app to send WiFi credentials
        4. This cycle repeats indefinitely until a successful WiFi connection is maintained
        """
        while True:
            if self.wifi.is_connected() or (self.wifi.load_credentials() and self.wifi.connect()):
                print("Connected to WiFi")
                self.start_main_loop()
            else:
                print("No stored credentials or connection failed")
                self.enter_pairing_mode()

    # When the button is held for the factory reset duration, the WiFi credentials are reset which
    # will make the device enter pairing mode again.
    def on_button_pressed(self, duration):
        if self.wifi.is_connected() and duration > Config.FACTORY_RESET_DURATION_MS:
            print("Button is pressed! Factory reset!")
            self.wifi.reset()

    # Todo: add main application logic here
    def start_main_loop(self):
        while True:
            time.sleep(1)
            print("Main loop - ToDo: main application logic here")
            if not self.wifi.is_connected():
                print("Wifi connection lost, entering pairing mode")
                break

    def enter_pairing_mode(self):
        self.ble_device = BLEDevice(self.bluetooth_name, self.handle_wifi_credentials)
        self.ble_device.await_credentials_then_disconnect()
        self.ble_device = None

    def handle_wifi_credentials(self, wifi_ssid, wifi_pass, notify_wifi_status):
        """
        Handle WiFi credentials received from BLE device.
        
        Args:
          wifi_ssid (str): The WiFi network SSID
          wifi_pass (str): The WiFi password
          notify_wifi_status (callable): Callback to notify status changes
      
        Returns:
            None
        """
        notify_wifi_status(b"CONNECTING")
        
        if self.wifi.connect(wifi_ssid, wifi_pass):
            notify_wifi_status(b"CONNECTED")
            self.wifi.save_credentials()
        else:
            notify_wifi_status(b"FAILED")
