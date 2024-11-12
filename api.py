import urequests
import json
import utime
import os
from config import Config
import ntptime

class API:
    def __init__(self):
        self.base_url = "https://api.example.com"
        self.timer_cache_file = Config.TIMER_JSON_FILE
    
    def get_timer_for_device(self, device_id):
        """
        Fetch timer details from the API for the given device ID.
        Returns the timer data if successful, None if no timer exists or on error.

        The API returns a JSON object with the following structure:
        {
            "timer_id": 42,
            "start_time": "2024-11-12T09:15:30Z",
            "end_time": "2024-11-13T10:15:30Z"
        }
        """
        if not self._sync_time():
            print("No internet connection - cannot fetch timer")
            return None
            
        try:
            response = urequests.get(self.__full_url(device_id))
            
            if response.status_code == 200:
                timer_data = response.json()
                # Cache the successful response
                self._cache_timer_data(timer_data)
                return timer_data
            elif response.status_code == 404:
                return None
            else:
                print(f"API error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Error fetching timer data: {e}")
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
            print(f"Failed to sync time: {e}")
            return False
    
    def __full_url(self, device_id):
        return "https://run.mocky.io/v3/6124103e-30cf-4330-bff5-bd617c63dac3"
        # return f"{self.base_url}/{path}/{device_id}"
        
    def _cache_timer_data(self, timer_data):
        """Store timer data in local cache file"""
        try:
            with open(self.timer_cache_file, 'w') as f:
                json.dump(timer_data, f)
        except Exception as e:
            print(f"Error caching timer data: {e}")
    
    def get_cached_timer(self):
        """Retrieve timer data from local cache"""
        try:
            with open(self.timer_cache_file, 'r') as f:
                return json.load(f)
        except:
            return None 
