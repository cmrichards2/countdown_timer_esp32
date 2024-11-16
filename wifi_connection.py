import network
import time
import json
import os
from config import Config
from event_bus import event_bus, Events
from machine import Timer

class WifiConnection:
    def __init__(self, credentials_file):
        self.credentials_file = credentials_file
        self.wlan = None
        self.wifi_ssid = None 
        self.wifi_pass = None
        self.reconnect_timer = None
        self.__subscribe()

    def __subscribe(self):
        event_bus.subscribe(Events.FACTORY_RESET_BUTTON_PRESSED, self.reset)
        event_bus.subscribe(Events.SOFT_RESET_BUTTON_PRESSED, self.reset)

    def reset(self):
        """Reset the WiFi connection and clear credentials file"""
        self.disconnect()
        self.wifi_ssid = None
        self.wifi_pass = None
        try:
            os.remove(self.credentials_file)
        except:
            pass
        event_bus.publish(Events.WIFI_RESET)

    def has_saved_credentials(self):
        try:
            os.stat(self.credentials_file)
            return True
        except OSError:
            return False

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

    def connect_and_monitor_connection(self):
        self.load_credentials()
        self.connect()
        self._monitor_connection()

    def _monitor_connection(self):
        """ Start a periodic timer to check if the WiFi connection is lost and attempt to reconnect """
        self.reconnect_timer = Timer(1)
        self.reconnect_timer.init(period=30000, mode=Timer.PERIODIC, callback=self._try_reconnect)

    def _try_reconnect(self, timer):
        """Attempt to reconnect to WiFi if disconnected"""
        if not self.is_connected() and self.wifi_ssid and self.wifi_pass:
            print("[WIFI] Wifi has been disconnected, attempting to reconnect...")
            if self.connect():
                event_bus.publish(Events.WIFI_CONNECTED)

    def connect(self, ssid=None, password=None):
        if ssid:
            self.wifi_ssid = ssid
            self.wifi_pass = password
            
        if not self.wifi_ssid or not self.wifi_pass:
            return False

        print(f"[WIFI] Connecting to WiFi with SSID: {self.wifi_ssid} and password: {self.wifi_pass}")

        if self.wlan and self.wlan.isconnected():
            return True
            
        try:
            self.wlan = network.WLAN(network.STA_IF)
            self.wlan.active(True)
            self.wlan.connect(self.wifi_ssid, self.wifi_pass)
            
            # Wait for connection with timeout
            retry_count = 0
            while not self.wlan.isconnected() and retry_count < Config.WIFI_RETRY_COUNT:
                time.sleep(Config.WIFI_RETRY_DELAY_SEC)
                retry_count += 1
            
            if self.wlan.isconnected():
                print(f"[WIFI] Connected to WiFi: {self.wlan.ifconfig()}")
                event_bus.publish(Events.WIFI_CONNECTED)
                return True
            else:
                print("[WIFI] Failed to connect to WiFi")
                self.wlan = None
                return False
        except Exception as e:
            print(f"[WIFI] Error connecting to WiFi: {e}")
            self.wlan = None
            return False

    def disconnect(self):
        if self.reconnect_timer:
            self.reconnect_timer.deinit()
        if self.wlan:
            self.wlan.disconnect()
            self.wlan = None

    def is_connected(self):
        """Check if there is an active WiFi connection"""
        return self.wlan is not None and self.wlan.isconnected()
