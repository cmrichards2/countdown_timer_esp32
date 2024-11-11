import network
import time
import json
import os
from ble_device import BLEDevice
from button import Button

class Application:
    # Duration in milliseconds that the switch must be held to trigger factory reset (resetting wifi credentials)
    FACTORY_RESET_DURATION_MS = 1000
    CREDENTIALS_FILE = "wifi_credentials.json"

    def __init__(self, name = "ESP32_Device"):
        self.name = name
        self.switch = Button(25, self.switch_handler)
        self.wlan = None
        self.wifi_ssid = None
        self.wifi_pass = None
        self.ble_device = None
    
    def start(self):
        time.sleep(4)
        
        if self.wlan or (self.load_wifi_credentials() and self.connect_wifi()):
            print("Connected with stored credentials")
            self.start_main_loop()
        else:
            print("No stored credentials or connection failed")
            self.enter_paring_mode()

        self.start()
    
    def start_main_loop(self):
        print("Main loop started - do the main application logic here")
        while True:
            time.sleep(1)
            print("Main loop")
            if self.wlan is None:
                print("Wifi connection lost, entering pairing mode")
                break

    def load_wifi_credentials(self):
        try:
            with open(self.CREDENTIALS_FILE, 'r') as f:
                creds = json.load(f)
                self.wifi_ssid = creds['ssid']
                self.wifi_pass = creds['password']
                return True
        except:
            return False

    def save_wifi_credentials(self):
        try:
            with open(self.CREDENTIALS_FILE, 'w') as f:
                json.dump({
                    'ssid': self.wifi_ssid,
                    'password': self.wifi_pass
                }, f)
        except Exception as e:
            print(f"Error saving credentials: {e}")

    def enter_paring_mode(self):
        self.ble_device = BLEDevice(self.name, self.handle_wifi_credentials)
        self.ble_device.await_credentials();
        self.ble_device.disconnect()
        self.ble_device = None

    def switch_handler(self, duration):
        if self.wlan is not None and duration > self.FACTORY_RESET_DURATION_MS:
            self.wlan.disconnect()
            self.wlan = None
            try:
                os.remove(self.CREDENTIALS_FILE)
            except:
                pass
            print("Switch is pressed! Factory reset")

    def connect_wifi(self):
        if not self.wifi_ssid or not self.wifi_pass:
            return False
            
        try:
            self.wlan = network.WLAN(network.STA_IF)
            self.wlan.active(True)
            
            self.wlan.connect(self.wifi_ssid, self.wifi_pass)
            
            # Wait for connection with timeout
            retry_count = 0
            while not self.wlan.isconnected() and retry_count < 10:
                time.sleep(1)
                retry_count += 1
            
            if self.wlan.isconnected():
                print("Connected to WiFi:", self.wlan.ifconfig())
                return True
            else:
                print("Failed to connect to WiFi")
                self.wlan = None
                return False
        except Exception as e:
            print(f"Error connecting to WiFi: {e}")
            self.wlan = None
            return False

    def handle_wifi_credentials(self, wifi_ssid, wifi_pass, notify_wifi_status):
        self.wifi_ssid = wifi_ssid
        self.wifi_pass = wifi_pass
        
        notify_wifi_status(b"CONNECTING")
        
        if self.connect_wifi():
            notify_wifi_status(b"CONNECTED")
            self.save_wifi_credentials()
        else:
            notify_wifi_status(b"FAILED")

app = Application()
app.start()
