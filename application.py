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
# It handles entering provisioning mode, connecting to WiFi, and starting the main application logic.

class Application:
    def __init__(self):
        self.button = Button(Config.BUTTON_PIN, self.on_button_pressed)
        self.wifi = WifiConnection(Config.WIFI_CREDENTIALS_FILE)
        self.led_controller = LedController()
        self.__subscribe()
    
    def __subscribe(self):
        event_bus.subscribe(Events.FACTORY_RESET_BUTTON_PRESSED, self._factory_reset)
    
    def start(self):
        """
        Main entry point that handles the application's connection flow:
        
        1. Check if WiFi credentials exist
        2. If credentials exist, attempt connection and start main loop regardless of result
        3. If no credentials exist, enter provisioning mode
        """
        while True:
            if self.wifi.has_saved_credentials():
                self.wifi.connect_and_monitor_connection()
                self.start_countdown_timer()
            else:
                self.enter_wifi_provisioning_mode()

    def on_button_pressed(self, duration):
        if duration > Config.FACTORY_RESET_DURATION_MS:
            print("Button is pressed! Factory reset!")
            event_bus.publish(Events.FACTORY_RESET_BUTTON_PRESSED)
            return

        if duration > Config.SOFT_RESET_DURATION_MS:
            print("Button is pressed! Soft reset!")
            event_bus.publish(Events.SOFT_RESET_BUTTON_PRESSED)
            return

        if duration < Config.BUTTON_TAP_DURATION_MS:
            event_bus.publish(Events.BUTTON_TAPPED)

    # Todo: add main application logic here
    def start_countdown_timer(self):
        countdown_timer = CountdownTimer(DeviceID.get_id())
        countdown_timer.start()

    def enter_wifi_provisioning_mode(self):
        ble_device = BLEDevice(Config.BLE_NAME_PREFIX, self.try_wifi_credentials)
        ble_device.await_wifi_credentials_then_disconnect()

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
    
    def _factory_reset(self):
        CountdownTimer.clear_data()
