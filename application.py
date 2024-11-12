import time
from ble_device import BLEDevice
from button import Button
from wifi_connection import WifiConnection
from config import Config
from led_controller import LedController
from event_bus import event_bus, Events
from countdown_timer import CountdownTimer
from device_id import DeviceID

# This application class is the main entry point for the application.
# It handles entering pairing mode, connecting to WiFi, and starting the main application loop.

class Application:
    def __init__(self, bluetooth_name):
        self.bluetooth_name = bluetooth_name
        self.button = Button(Config.BUTTON_PIN, self.on_button_pressed)
        self.wifi = WifiConnection(Config.WIFI_CREDENTIALS_FILE)
        self.ble_device = None
        self.led_controller = LedController()
    
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
        self.countdown_timer = CountdownTimer(DeviceID.get_id())
        self.countdown_timer.start()
        self.countdown_timer = None

    def enter_pairing_mode(self):
        event_bus.publish(Events.ENTERING_PAIRING_MODE)
        
        self.ble_device = BLEDevice(self.bluetooth_name, self.try_wifi_credentials)
        self.ble_device.await_wifi_credentials_then_disconnect()
        
        event_bus.publish(Events.EXITING_PAIRING_MODE)
        self.ble_device = None

    def try_wifi_credentials(self, wifi_ssid, wifi_pass, notify_wifi_status):
        """
        Try to connect to WiFi using the provided credentials provided over the bluetooth BLE connection.
        
        Args:
          wifi_ssid (str): The WiFi network SSID
          wifi_pass (str): The WiFi password
          notify_wifi_status (callable): Callback to notify status changes
      
        Returns:
          bool: True if the connection was successful, False otherwise
        """
        notify_wifi_status(b"CONNECTING")
        
        if self.wifi.connect(wifi_ssid, wifi_pass):
            notify_wifi_status(b"CONNECTED")
            self.wifi.save_credentials()
            return True
        else:
            notify_wifi_status(b"FAILED")
            return False
