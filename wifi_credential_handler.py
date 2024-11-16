import time
from machine import Timer
from config import Config

class WifiCredentialHandler:
    def __init__(self, notify_status_callback):
        """
        Initialize the WiFi credential handler
        
        Args:
            notify_status_callback (callable): Function to notify BLE clients of status changes
        """
        self.notify_status = notify_status_callback
        self.pending_credentials = None
        self.waiting_for_button = False
        self.confirmation_start_time = None
        self.confirmation_timer = None
        
    def process_credentials(self, credentials_str):
        """
        Process received WiFi credentials string and start confirmation timer
        
        Args:
            credentials_str (str): String in format "ssid|password"
        """
        print(f"[CREDENTIALS] Received credentials. Waiting for button tap confirmation...")
        self.notify_status(b"WAITING_CONFIRMATION")
        
        self.pending_credentials = credentials_str
        self.waiting_for_button = True
        self.confirmation_start_time = time.ticks_ms()
        
        # Start confirmation timer
        self.confirmation_timer = Timer(-1)
        self.confirmation_timer.init(
            period=Config.PROVISIONING_BUTTON_CONFIRMATION_DURATION_MS,
            mode=Timer.ONE_SHOT,
            callback=lambda t: self.cancel_confirmation()
        )

    def handle_button_tap(self, wifi_connection_callback):
        """
        Handle button tap confirmation for pending credentials
        
        Args:
            wifi_connection_callback (callable): Callback function to handle WiFi connection
            
        Returns:
            bool: True if connection was successful, False otherwise
        """
        if not self._can_process_button_tap():
            return False
            
        print(f"[CREDENTIALS] Button tapped - processing credentials")
        creds = self._parse_credentials()
        if not creds:
            return False
            
        ssid, password = creds
        print(f"[CREDENTIALS] SSID: {ssid}, Password: {password}")
        
        success = wifi_connection_callback(ssid, password, self.notify_status)
        self._reset_state()
        return success

    def _can_process_button_tap(self):
        """
        Check if button tap can be processed
        
        Returns:
            bool: True if credentials can be processed, False otherwise
        """
        if not self.waiting_for_button or not self.pending_credentials:
            print(f"[CREDENTIALS] No pending credentials or not waiting for button confirmation")
            return False
            
        if time.ticks_diff(time.ticks_ms(), self.confirmation_start_time) > Config.PROVISIONING_BUTTON_CONFIRMATION_DURATION_MS:
            print(f"[CREDENTIALS] Confirmation timeout - credentials rejected")
            self.notify_status(b"TIMEOUT")
            self._reset_state()
            return False
            
        return True

    def _parse_credentials(self):
        """
        Parse and validate credentials format
        
        Returns:
            tuple: (ssid, password)
        """
        creds = self.pending_credentials.split("|")
        return creds

    def _reset_state(self):
        """Reset internal state and cleanup timer"""
        self.pending_credentials = None
        self.waiting_for_button = False
        self.confirmation_start_time = None
        if self.confirmation_timer:
            self.confirmation_timer.deinit()
            self.confirmation_timer = None

    def is_waiting_for_confirmation(self):
        """
        Check if handler is waiting for button confirmation
        
        Returns:
            bool: True if waiting for confirmation and within time window
        """
        if not self.waiting_for_button:
            return False
        return time.ticks_diff(time.ticks_ms(), self.confirmation_start_time) < Config.PROVISIONING_BUTTON_CONFIRMATION_DURATION_MS

    def cancel_confirmation(self):
        """Cancel any pending confirmation and cleanup"""
        self._reset_state() 
