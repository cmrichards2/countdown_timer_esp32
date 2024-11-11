# import machine
# import time

# pin = 2
# led = machine.Pin(pin, machine.Pin.OUT)  # Use GPIO 2 for the built-in LED
# led.value(1)

# while True:
#   time.sleep(1)
#     print("LED ON", pin)
#     time.sleep_ms(100)
# led.on()

import ubluetooth
import ble_advertising
import network
import time

class BLEDevice:
    def __init__(self):
        print("BLEDevice init")
        self.ble = ubluetooth.BLE()
        self.ble.active(True)
        self.ble.irq(self.on_ble_event)
        
        # Define UUIDs and characteristics for Wi-Fi credentials
        SERVICE_UUID = ubluetooth.UUID("0000180F-0000-1000-8000-00805F9B34FB")
        WIFI_SSID_CHAR_UUID = ubluetooth.UUID("00002A19-0000-1000-8000-00805F9B34FB")
        WIFI_PASS_CHAR_UUID = ubluetooth.UUID("00002A1A-0000-1000-8000-00805F9B34FB")

        self.ble.config(gap_name="ESP32_Device")

        self.service = (SERVICE_UUID, ((WIFI_SSID_CHAR_UUID, ubluetooth.FLAG_WRITE), (WIFI_PASS_CHAR_UUID, ubluetooth.FLAG_WRITE),))
        self.ble.gatts_register_services((self.service,))
        
        self.start_advertising()
        
        self.wifi_ssid = None
        self.wifi_pass = None
    
    def start_advertising(self):
        adv_data = ble_advertising.advertising_payload(name="ESP32_Device") #, services=[self.service[0]])
        self.ble.gap_advertise(100, adv_data)  # 100ms interval
        print("Advertising as 'ESP32_Device'")        

    def on_ble_event(self, event, data):
        if event == 1:  # BLE connect event
            print("BLE connected")
        elif event == 2:  # BLE disconnect event
            print("BLE disconnected")
        elif event == 3:  # Write request
            handle, value = data
            if handle == self.ble.gatts_find_service(self.service)[1][0]:  # SSID characteristic handle
                self.wifi_ssid = value.decode("utf-8")
            elif handle == self.ble.gatts_find_service(self.service)[1][1]:  # Password characteristic handle
                self.wifi_pass = value.decode("utf-8")
                self.connect_to_wifi()

    def connect_to_wifi(self):
        if self.wifi_ssid and self.wifi_pass:
            wlan = network.WLAN(network.STA_IF)
            wlan.active(True)
            wlan.connect(self.wifi_ssid, self.wifi_pass)
            while not wlan.isconnected():
                time.sleep(1)
            print("Connected to WiFi:", wlan.ifconfig())


print("Hello")
time.sleep(10)
print("BLEDevice init")
ble_device = BLEDevice()

while True:
    time.sleep(2)
    print("BLEDevice loop")


