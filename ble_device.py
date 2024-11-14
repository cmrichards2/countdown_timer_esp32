import ubluetooth
import ble_advertising
import time
import sys
from config import Config
from device_id import DeviceID
from event_bus import event_bus, Events
from machine import Timer
from micropython import const
from wifi_credential_handler import WifiCredentialHandler

class BLEDevice:
    def __init__(self, name, handle_wifi_credentials):
        self.name = name
        self.handle_wifi_credentials = handle_wifi_credentials
        self.wifi_connected = False
        self.wlan = None
        self.wifi_ssid = None
        self.wifi_pass = None
        self.received_data = bytearray()
        self.device_id = DeviceID.get_id()
        self.wifi_handler = WifiCredentialHandler(self.notify_wifi_status)
        
        event_bus.publish(Events.ENTERING_PAIRING_MODE)

        self.__subscribe()
        self.setup_bluetooth_service()
        self.start_bluetooth_advertising()

    def __subscribe(self):
        # After sending wifi credentials, the user must tap the button to confirm within 10 seconds
        event_bus.subscribe(Events.BUTTON_TAPPED, self._handle_button_tap)

    def __unsubscribe(self):
        event_bus.unsubscribe(Events.BUTTON_TAPPED, self._handle_button_tap)
    
    def await_wifi_credentials_then_disconnect(self):
        while not self.wifi_connected:
            time.sleep(3)
            self.show_status()
        print("[BLE] wifi connection established, disconnecting bluetooth...")
        time.sleep(1)
        self.disconnect()
    
    def disconnect(self):
        print("[BLE] disconneting")
        self.__unsubscribe()
        self._deactivate_bluetooth()
        self.wifi_handler.cancel_confirmation()
        event_bus.publish(Events.EXITING_PAIRING_MODE)
        print("[BLE] disconnected")

    def _handle_button_tap(self):
        if self.wifi_handler.handle_button_tap(self.handle_wifi_credentials):
            self.wifi_connected = True
        self.received_data = bytearray()
    
    def setup_bluetooth_service(self):
        # BLE operates using Services and Characteristics:
        # - A Service is a collection of data and behaviors for a particular purpose
        # - Characteristics are data values that can be read, written, or notified within a Service
        
        # UUIDs (Universal Unique Identifiers) are used to identify Services and Characteristics
        # Standard UUIDs exist for common services (e.g., battery service)
        # Here we're using custom UUIDs defined in our config
        SERVICE_UUID = ubluetooth.UUID(Config.BLE_SERVICE_UUID)
        WIFI_CREDENTIALS_UUID = ubluetooth.UUID(Config.BLE_WIFI_CREDENTIALS_UUID)
        WIFI_STATUS_UUID = ubluetooth.UUID(Config.BLE_WIFI_STATUS_UUID)
        DEVICE_ID_UUID = ubluetooth.UUID(Config.BLE_DEVICE_ID_UUID)

        # Initialize BLE radio and set it to active
        self.ble = ubluetooth.BLE()
        self.ble.active(True)
        
        # Register callback for BLE events (connect, disconnect, data received)
        self.ble.irq(self.on_ble_event)
        
        # Set the device name that will appear to other devices
        self.ble.config(gap_name=self.name)

        # Define our custom service structure:
        # - First tuple element is the Service UUID
        # - Second element is a tuple of Characteristics, each containing:
        #   * Characteristic UUID
        #   * Flags that define what operations are allowed:
        #     - FLAG_WRITE: Allows clients to write values
        #     - FLAG_READ: Allows clients to read values
        #     - FLAG_NOTIFY: Allows server to push updates to connected clients
        self.service = (
            SERVICE_UUID, 
            (
                (WIFI_CREDENTIALS_UUID, ubluetooth.FLAG_WRITE),  # Clients can write WiFi credentials
                (WIFI_STATUS_UUID, ubluetooth.FLAG_NOTIFY),      # We can notify clients about WiFi status
                (DEVICE_ID_UUID, ubluetooth.FLAG_READ),  # New characteristic
            )
        )
        
        # Register the service with the BLE stack
        # This returns handles (unique identifiers) that we'll use to reference 
        # specific characteristics when reading/writing/notifying
        ((self.wifi_credentials_handle, self.wifi_status_handle, self.device_id_handle),) = self.ble.gatts_register_services((self.service,))
        
        # Set the initial device ID value
        self.ble.gatts_write(self.device_id_handle, self.device_id.encode())

    def _deactivate_bluetooth(self):
        print("[BLE] deactivating bluetooth service")
        self.ble.gap_advertise(0, None)
        self.ble.active(False)
        self.ble = None

    def start_bluetooth_advertising(self):
        adv_data = ble_advertising.advertising_payload(name=self.name)
        self.ble.gap_advertise(Config.BLE_ADVERTISING_INTERVAL_MS, adv_data)
        print(f"[BLE] advertising bluetooth device as '{self.name}'")        
    
    def notify_wifi_status(self, status):
        """Notify connected clients about WiFi connection status changes"""
        self.ble.gatts_notify(0, self.wifi_status_handle, status)

    def on_ble_event(self, event, data):
        BLE_CONNECT = 1
        BLE_DISCONNECT = 2
        BLE_WRITE = 3

        if event == BLE_CONNECT:
            print("BLE: connected")
            self.received_data = bytearray()  # Reset received data on new connection
            return

        if event == BLE_DISCONNECT:
            print("BLE: disconnected")
            self.received_data = bytearray()
            self.wifi_handler.cancel_confirmation()
            if not self.wifi_connected:
                self.start_bluetooth_advertising()
            return

        if event == BLE_WRITE:
            print("BLE: client is writing wifi credentials")
            self._handle_write_wifi_credentials_event()

    def _handle_write_wifi_credentials_event(self):
        """Handle incoming data chunks and process complete WiFi credentials"""
        buffer = self.ble.gatts_read(self.wifi_credentials_handle)
        if not buffer:
            return

        try:
            if buffer == b"END":
                decoded = self.received_data.decode("utf-8")
                self.wifi_handler.process_credentials(decoded)
                self.received_data = bytearray()
            else:
                self.received_data.extend(buffer)
                print(f"Received chunk, current length: {len(self.received_data)}")
        except Exception as e:
            print(f"Error processing data: {e}")
            sys.print_exception(e)

    def _waiting_for_button_status(self):
        return self.wifi_handler.is_waiting_for_confirmation()

    def show_status(self):
        output = ""
        if self.ble.active():
            output += "BLE: is connected"
        else:
            output += "BLE: is disconnected"
        if self.wlan is not None and self.wlan.isconnected():
            output += "WiFi connected. "
        if self._waiting_for_button_status():
            output += "Waiting for button confirmation. "
        if self.wlan and self.wlan.isconnected():   
            output += f"WiFi credentails: {self.wifi_ssid}, {self.wifi_pass}. "
        print(output)

        
