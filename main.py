import network
import time
from ble_device import BLEDevice
from button import Button

class Application:
    def __init__(self, name = "ESP32_Device"):
        self.name = name
        self.switch = Button(25, self.switch_handler)
        self.wlan = None
        self.wifi_ssid = None
        self.wifi_pass = None
        self.ble_device = None
    
    def start(self):
        time.sleep(4)

        if self.wlan is None:
            self.enter_paring_mode()
        else: 
            print("Wifi connected, starting main loop")
            self.start_main_loop()

        self.start()

    def enter_paring_mode(self):
        self.ble_device = BLEDevice(self.name, self.handle_wifi_credentials)
        self.ble_device.await_credentials();
        self.ble_device = None
    
    def start_main_loop(self):
        print("Main loop started")
        while True:
            time.sleep(1)
            print("Main loop")
            if self.wlan is None:
                print("Wifi connection lost, entering pairing mode")
                break

    def switch_handler(self):
        if self.wlan is not None:
            self.wlan.disconnect()
            self.wlan = None
            print("Switch is pressed! Factory reset")

    # self.wlan is set to None if the wifi connection fails
    def handle_wifi_credentials(self, wifi_ssid, wifi_pass, notify_wifi_status):
        self.wifi_ssid = wifi_ssid
        self.wifi_pass = wifi_pass
        if self.wifi_ssid and self.wifi_pass:
            try:
                self.wlan = network.WLAN(network.STA_IF)
                self.wlan.active(True)
                notify_wifi_status(b"CONNECTING")
                
                self.wlan.connect(self.wifi_ssid, self.wifi_pass)
                
                # Wait for connection with timeout
                retry_count = 0
                while not self.wlan.isconnected() and retry_count < 10:
                    time.sleep(1)
                    retry_count += 1
                
                if self.wlan.isconnected():
                    print("Connected to WiFi:", self.wlan.ifconfig())
                    notify_wifi_status(b"CONNECTED")
                else:
                    print("Failed to connect to WiFi")
                    notify_wifi_status(b"FAILED")
                    self.wlan = None
            except Exception as e:
                print(f"Error connecting to WiFi: {e}")
                # Send error status
                notify_wifi_status(f"ERROR:{str(e)}".encode())
                self.wlan = None

app = Application()
app.start()
