from request import get, post
import json
import utime
import time
import os
import sys
from config import Config
import ntptime

class API:
    def __init__(self):
        self.base_url = Config.API_BASE_URL
        self.timer_cache_file = Config.TIMER_JSON_FILE
        self.offline_presses_file = Config.OFFLINE_PRESSES_FILE

    def register_device(self, device_id, short_code):
        """
        Register a device with the API using a short code.
        Returns True if registration successful, False otherwise.
        """
        # Save the short code to the file
        self.save_timer_data({"short_code": short_code}, preserve_token=False)
        return True

    @staticmethod
    def clear_cache():
        """Clear the timer data from the API"""
        try:
            os.remove(Config.TIMER_JSON_FILE)
        except:
            pass

    def timer_pressed(self, short_code):
        """Handle timer press events, storing offline if no connection"""
        try:    
            print(f"[API] Timer pressed for {short_code}")
            
            # Check if we have internet connection
            if not self._sync_time():
                print("[API] No internet connection - storing press offline")
                self._store_offline_press()
                
                # Update local timer data
                current_timer = self.get_cached_timer() or {}
                current_timer['start_time'] = time.time()
                self.save_timer_data(current_timer, preserve_token=True)
                return
                
            # If we have connection, process normally
            url = f"{self.base_url}/api/device/restart/{short_code.upper()}"
            print(f"[API] URL: {url}")
            response = get(url)
            print(f"Response: {response.text}")
            
        except Exception as e:
            print(f"[API] Error handling timer press: {e}")
            sys.print_exception(e)

    def _store_offline_press(self):
        """Store the current time in the offline presses file"""
        try:
            current_time = time.time()
            offline_presses = self._load_offline_presses()
            offline_presses.append(current_time)
            
            with open(self.offline_presses_file, 'w') as f:
                json.dump(offline_presses, f)
                
        except Exception as e:
            print(f"[API] Error storing offline press: {e}")
            sys.print_exception(e)

    def _load_offline_presses(self):
        """Load the list of offline presses from file"""
        try:
            with open(self.offline_presses_file, 'r') as f:
                return json.load(f)
        except:
            return []

    def _sync_offline_presses(self, short_code):
        """Sync any stored offline presses with the API"""
        try:
            if not os.stat(self.offline_presses_file):
                return
        except OSError:
            return False
        
        try:
            offline_presses = self._load_offline_presses()
            if not offline_presses:
                return
                
            print(f"[API] Syncing {len(offline_presses)} offline presses")
            
            for press_time in offline_presses:
                url = f"{self.base_url}/api/device/restart/{short_code}?time={press_time}"
                print(f"[API] Syncing offline press: {url}")
                response = get(url)
                if response.status_code != 200:
                    print(f"[API] Error syncing offline press: {response.text}")
                    return False
                    
            # All presses synced successfully, remove the file
            os.remove(self.offline_presses_file)
            return True
            
        except Exception as e:
            print(f"[API] Error syncing offline presses: {e}")
            sys.print_exception(e)
            return False

    def get_timer_for_device(self, device_id, short_code):
        """
        Fetch timer details from the API for the given device ID.
        First syncs any offline presses if there's a connection.
        """
        print(f"[API] Fetching timer for device {short_code}")
        if not self._sync_time():
            print("[API] No internet connection - cannot fetch timer")
            return None
            
        try:
            # First sync any offline presses
            self._sync_offline_presses(short_code)
            
            url = f"{self.base_url}/api/device/{short_code.upper()}?device_id={device_id}"
            print(f"[API] URL: {url}")
            response = get(url)
            
            if response.status_code == 200:
                timer_data = response.json()
                print(f"[API] JSON response: {timer_data}")
                self.save_timer_data(timer_data, preserve_token=True)
                return timer_data
            elif response.status_code == 404:
                return None
            else:
                print(f"[API] API error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"[API] Error fetching timer data: {e}")
            return None
    
    def _sync_time(self):
        """
        Synchronize ESP32's time with NTP server.
        Returns True if successful, False if failed.
        """
        try:
            ntptime.settime()
            return True
        except Exception as e:
            print(f"[API] Failed to sync time: {e}")
            return False
    
    def __full_url(self, device_id):
        return "https://timer.christopher-richards.net/api/device/2c0a9af10ef918efb6ac98bf452549f7"
        # return "https://run.mocky.io/v3/5a483c3b-3e68-4a5c-80d0-9dcf41343b2d"
        # return f"{self.base_url}/{path}/{device_id}"
        
    def save_timer_data(self, timer_data, preserve_token=False):
        """
        Store timer data in local cache file
        If preserve_token is True, existing token will be preserved
        """
        try:
            if preserve_token:
                existing_data = self.get_cached_timer() or {}
                if 'short_code' in existing_data:
                    timer_data['short_code'] = existing_data['short_code']

            print(f"[API] Saving timer data: {timer_data}")
                
            with open(self.timer_cache_file, 'w') as f:
                json.dump(timer_data, f)
        except Exception as e:
            print(f"[API] Error caching timer data: {e}")
    
    def get_cached_timer(self):
        """Retrieve timer data from local cache"""
        try:
            with open(self.timer_cache_file, 'r') as f:
                return json.load(f)
        except:
            return None 
