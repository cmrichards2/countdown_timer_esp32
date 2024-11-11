import network
import time
import json
import os

class WifiConnection:
    def __init__(self, credentials_file="wifi_credentials.json"):
        self.credentials_file = credentials_file
        self.wlan = None
        self.wifi_ssid = None 
        self.wifi_pass = None

    def load_credentials(self):
        try:
            with open(self.credentials_file, 'r') as f:
                creds = json.load(f)
                self.wifi_ssid = creds['ssid']
                self.wifi_pass = creds['password']
                return True
        except:
            return False

    def save_credentials(self):
        try:
            with open(self.credentials_file, 'w') as f:
                json.dump({
                    'ssid': self.wifi_ssid,
                    'password': self.wifi_pass
                }, f)
        except Exception as e:
            print(f"Error saving credentials: {e}")

    def connect(self, ssid=None, password=None):
        if ssid:
            self.wifi_ssid = ssid
            self.wifi_pass = password
            
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

    def disconnect(self):
        if self.wlan:
            self.wlan.disconnect()
            self.wlan = None

    def is_connected(self):
        return self.wlan is not None and self.wlan.isconnected()

    def reset(self):
        self.disconnect()
        try:
            os.remove(self.credentials_file)
        except:
            pass
