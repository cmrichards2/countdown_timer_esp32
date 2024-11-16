import time
from ble_device import BLEDevice
from button import Button
from wifi_connection import WifiConnection
from config import Config
from led_controller import LedController
from event_bus import event_bus, Events
from countdown_timer import CountdownTimer
from device_id import DeviceID
from api import API
from soft_ap_provisioning import SoftAPProvisioning
import gc

class Application:
    """
    This class is the controller for the application that connects the major components together.
    """

    def __init__(self):
        self.button = Button(Config.BUTTON_PIN, self.on_button_pressed)
        self.wifi = WifiConnection(Config.WIFI_CREDENTIALS_FILE)
        self.led_controller = LedController()
        self.provisioning_mode = Config.DEFAULT_PROVISIONING_MODE
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
            gc.collect()

    def on_button_pressed(self, duration):
        if duration > Config.FACTORY_RESET_DURATION_MS:
            print("[APP] Button is pressed! Factory reset! Entering Bluetooth provisioning mode")
            self.provisioning_mode = Config.PROVISIONING_MODE_BLE
            event_bus.publish(Events.FACTORY_RESET_BUTTON_PRESSED)
            return

        if duration > Config.SOFT_RESET_DURATION_MS:
            print("[APP] Button is pressed! Soft reset! Entering SoftAP/Wifi provisioning mode")
            self.provisioning_mode = Config.PROVISIONING_MODE_SOFTAP
            event_bus.publish(Events.SOFT_RESET_BUTTON_PRESSED)
            return

        if duration < Config.BUTTON_TAP_DURATION_MS:
            event_bus.publish(Events.BUTTON_TAPPED)

    def start_countdown_timer(self):
        countdown_timer = CountdownTimer(DeviceID.get_id())
        countdown_timer.start()

    def enter_wifi_provisioning_mode(self):
        """
        Enter WiFi provisioning mode using either BLE or SoftAP.
        In provisioning mode, an external device can connect to the ESP32 and provide WiFi credentials and a short code.
        """
        if Config.DEFAULT_PROVISIONING_MODE == Config.PROVISIONING_MODE_BLE:
            ble_device = BLEDevice(Config.BLE_NAME_PREFIX, self.try_wifi_credentials)
            ble_device.await_wifi_credentials_then_disconnect()
        else:
            ap_provisioning = SoftAPProvisioning(self.try_wifi_credentials)
            ap_provisioning.start()

    def try_wifi_credentials(self, wifi_ssid, wifi_pass, short_code, notify_wifi_status):
        """
        Try to connect to WiFi using the provided credentials provided over the Wifi connection.
        If the connection is successful and the device registration using the short code is successful,
        the device will be registered and the wifi credentials will be saved.
        
        Args:
          wifi_ssid (str): The WiFi network SSID
          wifi_pass (str): The WiFi password
          short_code (str): The short code to register the device with (This comes from the online app)
          notify_wifi_status (callable): Callback to notify status changes
      
        Returns:
          bool: True if the connection was successful, False otherwise
        """
        notify_wifi_status(b"CONNECTING")
        
        if self.wifi.connect(wifi_ssid, wifi_pass):
            notify_wifi_status(b"WIFI CONNECTED")
            if API().register_device(DeviceID.get_id(), short_code):
                self.wifi.save_credentials()
                return True
            else:
                notify_wifi_status(b"FAILED - INVALID SHORT CODE")
                return False
        else:
            notify_wifi_status(b"FAILED")
            return False
    
    def _factory_reset(self):
        CountdownTimer.clear_data()
