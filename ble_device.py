import ubluetooth
import ble_advertising
import time
from config import Config
from device_id import DeviceID
from event_bus import event_bus, Events

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

        self.setup_bluetooth_service()
        self.start_bluetooth_advertising()

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
        event_bus.publish(Events.ENTERING_PAIRING_MODE)
    
    def disconnect(self):
        self.ble.gap_advertise(0, None)
        self.ble.active(False)
        self.ble = None
        event_bus.publish(Events.EXITING_PAIRING_MODE)
    
    def await_wifi_credentials_then_disconnect(self):
        while not self.wifi_connected:
            time.sleep(3)
            self.show_status()
        time.sleep(1)
        self.disconnect()

    def start_bluetooth_advertising(self):
        adv_data = ble_advertising.advertising_payload(name=self.name)
        self.ble.gap_advertise(Config.BLE_ADVERTISING_INTERVAL_MS, adv_data)
        print(f"Advertising as '{self.name}'")        
    
    def notify_wifi_status(self, status):
        """Notify connected clients about WiFi connection status changes"""
        self.ble.gatts_notify(0, self.wifi_status_handle, status)

    def on_ble_event(self, event, data):
        BLE_CONNECT = 1
        BLE_DISCONNECT = 2
        BLE_WRITE = 3

        if event == BLE_CONNECT:
            print("BLE connected")
            self.received_data = bytearray()  # Reset received data on new connection
            return

        if event == BLE_DISCONNECT:
            print("BLE disconnected")
            return

        if event == BLE_WRITE:
            self._handle_write_wifi_credentials_event()

    def _handle_write_wifi_credentials_event(self):
        """Handle incoming data chunks and process complete WiFi credentials"""
        buffer = self.ble.gatts_read(self.wifi_credentials_handle)
        if not buffer:
            return

        try:
            if buffer == b"END":
                self._process_complete_credentials()
            else:
                # Append the chunk to received_data
                self.received_data.extend(buffer)
                print(f"Received chunk, current length: {len(self.received_data)}")
        except Exception as e:
            print(f"Error processing data: {e}")

    def _process_complete_credentials(self):
        """
        Process the complete WiFi credentials once END marker is received
        
        The credentials are expected to be in the format "SSID|PASSWORD"
        """
        decoded = self.received_data.decode("utf-8")
        print(f"Received complete data: {decoded}")
        
        creds = decoded.split("|")
        if len(creds) != 2:
            print("Invalid credential format")
            self.received_data = bytearray()
            return

        self.wifi_ssid, self.wifi_pass = creds
        print(f"SSID: {self.wifi_ssid}, Password: {self.wifi_pass}")
        
        if self.handle_wifi_credentials(self.wifi_ssid, self.wifi_pass, self.notify_wifi_status):
            self.wifi_connected = True
        
        self.received_data = bytearray()

    def show_status(self):
        if self.wlan:
            if self.wlan.isconnected():
                print(f"WiFi credentails: {self.wifi_ssid}, {self.wifi_pass}")
            else:
                print("Not connected to WiFi")
        else:
            print("No WiFi credentials set")
