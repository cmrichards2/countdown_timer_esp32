import time
from config import Config
from api import API
from event_bus import event_bus, Events
import utime
import sys
from timer_display import TimerDisplay

class CountdownTimer:
    def __init__(self, device_id):
        self.device_id = device_id
        self.api = API()
        self.display = TimerDisplay()
        self.timer_data = self.api.get_cached_timer()
        self.abort = False
        self.last_fetched_timer_data_from_api = 0  
        self.__fetch_timer_settings()
        self.__subscribe()

    def __subscribe(self):
        event_bus.subscribe(Events.TIME_CHANGED, self.__update_display)
        event_bus.subscribe(Events.WIFI_RESET, self.__abort_timer)
        event_bus.subscribe(Events.BUTTON_TAPPED, self.__restart_timer)

    def __unsubscribe(self):
        event_bus.unsubscribe(Events.TIME_CHANGED, self.__update_display)
        event_bus.unsubscribe(Events.WIFI_RESET, self.__abort_timer)
        event_bus.unsubscribe(Events.BUTTON_TAPPED, self.__restart_timer)

    @staticmethod
    def clear_data():
        """Clear the timer data from the API - used during a factory reset"""
        API.clear_cache()

    def start(self):
        """Start the countdown timer"""
        print("[Timer] Starting")
        
        while True:
            current_time = utime.time()

            if self.abort:
                print("[Timer] Aborted")
                self.__unsubscribe()
                break
            
            if "end_time" not in self.timer_data:
                # The timer data has never been successfully loaded from the API,
                # not even once. Try again every minute.
                self.__fetch_timer_settings()
                time.sleep(60) 
                continue
            
            # Check if it's time to update settings
            if current_time - self.last_fetched_timer_data_from_api >= Config.FETCH_TIMER_DATA_FROM_API_INTERVAL:
                print("[Timer] Fetching timer data from API")
                self.__fetch_timer_settings()
                self.last_fetched_timer_data_from_api = current_time
            
            self._tick()

    def _tick(self):
        """Tick the timer"""
        end_time = self.__get_end_time()
        current_time = utime.localtime()
        current_timestamp = utime.mktime(current_time)

        elapsed_seconds = end_time - current_timestamp
        time_type = "until" if elapsed_seconds > 0 else "since"
        
        # Take absolute value if elapsed_seconds is negative
        elapsed_seconds = abs(elapsed_seconds)

        days = elapsed_seconds // 86400
        hours = (elapsed_seconds % 86400) // 3600
        minutes = (elapsed_seconds % 3600) // 60
        seconds = elapsed_seconds % 60

        event_bus.publish(Events.TIME_CHANGED, {
            "days": days,
            "hours": hours,
            "minutes": minutes,
            "seconds": seconds,
            "type": time_type
        })
        time.sleep(1)

    def __update_display(self, time_data):
        self.display.update_time(time_data)

    def __restart_timer(self):
        """Restart the timer"""
        if self.timer_data and "short_code" in self.timer_data:
            self.api.timer_pressed(self.timer_data["short_code"])
            self.__fetch_timer_settings()

    def __fetch_timer_settings(self):
        """
        Fetch timer settings from the online API or local cache.
        Returns True if timer settings were successfully loaded from either source.
        """

        # Get short code if it exists in timer data
        if 'short_code' in self.timer_data:
            short_code = self.timer_data["short_code"]
            self.timer_data = self.api.get_timer_for_device(self.device_id, short_code)
        else:
            self.timer_data = None
        
        # If API call failed, try to get from cache
        if self.timer_data is None:
            print("[Timer] No timer data found, trying cache")
            self.timer_data = self.api.get_cached_timer()
            
        if self.timer_data:
            print(f"[Timer] Timer loaded for device {self.device_id}")
            print(f"[Timer] Timer data: {self.timer_data}")
            return True
        else:
            print(f"[Timer] No timer found for device {self.device_id}")
            return False
            
    def __abort_timer(self):
        """Abort the timer"""
        self.abort = True

    def __get_end_time(self):
        """Return the start time of the timer. Parsed from the timer data."""
        if self.timer_data and "end_time" in self.timer_data:
            end_time_str = self.timer_data["end_time"]
            year = int(end_time_str[0:4])
            month = int(end_time_str[5:7])
            day = int(end_time_str[8:10])
            hour = int(end_time_str[11:13])
            minute = int(end_time_str[14:16])
            second = int(end_time_str[17:19])

            timestamp = utime.mktime((year, month, day, hour, minute, second, 0, 0))

            return timestamp
        else:
            return None

        
