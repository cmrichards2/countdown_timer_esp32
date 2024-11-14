import ubluetooth
import ble_advertising
import time
import sys
from config import Config
from device_id import DeviceID
from event_bus import event_bus, Events
from machine import Timer
from micropython import const

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
        self.pending_credentials = None
        self.waiting_for_button = False
        self.timer = None
        
        self.__subscribe()

        self.setup_bluetooth_service()
        self.start_bluetooth_advertising()

    def __subscribe(self):
        # After sending wifi credentials, the user must tap the button to confirm within 10 seconds
        event_bus.subscribe(Events.BUTTON_TAPPED, self._handle_button_tap)

    def __unsubscribe(self):
        event_bus.unsubscribe(Events.BUTTON_TAPPED, self._handle_button_tap)
    
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
        self.__unsubscribe()
        if self.timer:
            self.timer.deinit()
        self.ble.gap_advertise(0, None)
        self.ble.active(False)
        self.ble = None
        event_bus.publish(Events.EXITING_PAIRING_MODE)
        print("Disconnected ble")
    
    def await_wifi_credentials_then_disconnect(self):
        while not self.wifi_connected:
            time.sleep(3)
            self.show_status()
        time.sleep(1)
        print("Disconnecting.. wifi connected")
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
            print("BLE: connected")
            self.received_data = bytearray()  # Reset received data on new connection
            return

        if event == BLE_DISCONNECT:
            print("BLE: disconnected")
            self.received_data = bytearray()
            self.pending_credentials = None
            self.waiting_for_button = False
            if self.timer:
                self.timer.deinit()
            self.start_bluetooth_advertising()
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
                # Instead of processing immediately, store credentials and wait for button
                decoded = self.received_data.decode("utf-8")
                print("Received credentials. Waiting for button tap confirmation...")
                self.notify_wifi_status(b"WAITING_CONFIRMATION")
                
                self.pending_credentials = decoded
                self.waiting_for_button = True
                
                # Start a 10-second timer
                self.confirmation_start_time = time.ticks_ms()
                self.timer = Timer(-1)
                self.timer.init(
                    period=Config.PROVISIONING_BUTTON_CONFIRMATION_DURATION_MS, 
                    mode=Timer.ONE_SHOT, 
                    callback=self._stop_waiting_for_confirmation
                )
            else:
                # Append the chunk to received_data
                self.received_data.extend(buffer)
                print(f"Received chunk, current length: {len(self.received_data)}")
        except Exception as e:
            print(f"Error processing data: {e}")
            sys.print_exception(e)

    def _stop_waiting_for_confirmation(self, timer):
        print("Stop waiting for confirmation")
        timer.deinit()
        if self.waiting_for_button:
            self.waiting_for_button = False
            self.pending_credentials = None
            self.received_data = bytearray()

    def _handle_button_tap(self):
        print("tapped")
        if not self.waiting_for_button or not self.pending_credentials:
            print("No pending credentials or not waiting for button confirmation")
            return
            
        # Check if we're still within the 10-second window
        if time.ticks_diff(time.ticks_ms(), self.confirmation_start_time) > Config.PROVISIONING_BUTTON_CONFIRMATION_DURATION_MS:
            print("Confirmation timeout - credentials rejected")
            self.notify_wifi_status(b"TIMEOUT")
            self.pending_credentials = None
            self.waiting_for_button = False
            self.received_data = bytearray()
            return

        print("Button tapped - processing credentials")
        decoded = self.pending_credentials
        creds = decoded.split("|")
        if len(creds) != 2:
            print("Invalid credential format")
            self.notify_wifi_status(b"INVALID_FORMAT")
            self.pending_credentials = None
            self.waiting_for_button = False
            self.received_data = bytearray()
            return

        self.wifi_ssid, self.wifi_pass = creds
        print(f"SSID: {self.wifi_ssid}, Password: {self.wifi_pass}")
        
        if self.handle_wifi_credentials(self.wifi_ssid, self.wifi_pass, self.notify_wifi_status):
            self.wifi_connected = True
        
        self.pending_credentials = None
        self.waiting_for_button = False
        self.received_data = bytearray()

    def _waiting_for_button_status(self):
        return self.waiting_for_button and time.ticks_diff(time.ticks_ms(), self.confirmation_start_time) < Config.PROVISIONING_BUTTON_CONFIRMATION_DURATION_MS

    def show_status(self):
        output = ""
        if self.ble.active():
            output += "BLE connected. "
        else:
            output += "BLE disconnected. "
        if self.wlan is not None and self.wlan.isconnected():
            output += "WiFi connected. "
        if self._waiting_for_button_status():
            output += "Waiting for button confirmation. "
        if self.wlan and self.wlan.isconnected():   
            output += f"WiFi credentails: {self.wifi_ssid}, {self.wifi_pass}. "
        print(output)

        
