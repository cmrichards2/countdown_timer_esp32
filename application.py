import time
from ble_device import BLEDevice
from button import Button
from wifi_connection import WifiConnection

# This application class is the main entry point for the application.
# It handles entering pairing mode, connecting to WiFi, and starting the main application loop.
class Application:
    # Duration in milliseconds that the switch must be held to trigger factory reset (resetting wifi credentials)
    FACTORY_RESET_DURATION_MS = 1000

    def __init__(self, bluetooth_name = "ESP32_Device"):
        self.bluetooth_name = bluetooth_name
        self.button = Button(25, self.on_button_pressed)
        self.wifi = WifiConnection()
        self.ble_device = None
    
    def start(self):
        if self.wifi.is_connected() or (self.wifi.load_credentials() and self.wifi.connect()):
            print("Connected to WiFi")
            self.start_main_loop()
        else:
            print("No stored credentials or connection failed")
            self.enter_paring_mode()

        self.start()

    # When the button is held for the factory reset duration, the WiFi credentials are reset which
    # will make the device enter pairing mode again.
    def on_button_pressed(self, duration):
        if self.wifi.is_connected() and duration > self.FACTORY_RESET_DURATION_MS:
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

    def enter_paring_mode(self):
        self.ble_device = BLEDevice(self.bluetooth_name, self.handle_wifi_credentials)
        self.ble_device.await_credentials();
        self.ble_device.disconnect()
        self.ble_device = None

    def handle_wifi_credentials(self, wifi_ssid, wifi_pass, notify_wifi_status):
        notify_wifi_status(b"CONNECTING")
        
        if self.wifi.connect(wifi_ssid, wifi_pass):
            notify_wifi_status(b"CONNECTED")
            self.wifi.save_credentials()
        else:
            notify_wifi_status(b"FAILED")
