import time
from config import Config
from api import API
from event_bus import event_bus, Events
import utime
import sys

class CountdownTimer:
    def __init__(self, device_id):
        self.device_id = device_id
        self.api = API()
        self.timer_data = self.api.get_cached_timer()
        self.abort = False
        self.__fetch_timer_settings()
        self.__subscribe()

    @staticmethod
    def clear_data():
        """Clear the timer data from the API"""
        API.clear_cache()

    def display_timer(self, time_data):
        """Show the time left on the LED display (todo)"""
        print(f"Time left: {time_data}")

    def start(self):
        print("Starting timer")
        iteration = 0
        max_iterations = 10
        while True:
            if self.abort:
                print("Timer aborted")
                self.__unsubscribe()
                break

            if not self.timer_data or "end_time" not in self.timer_data:
                # Attempt to fetch timer settings from API every minute if no timer data is
                # associated with this device
                self.__fetch_timer_settings()
                time.sleep(60)
            
            if self.timer_data and "end_time" in self.timer_data:
                self._tick()

                # Fetch updated timer settings every 10 ticks
                # It's possible that the online timer settings have changed
                iteration += 1
                if iteration > max_iterations:
                    iteration = 0
                    self.__fetch_timer_settings()

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
        pass

    def __subscribe(self):
        event_bus.subscribe(Events.TIME_CHANGED, self.display_timer)
        event_bus.subscribe(Events.WIFI_RESET, self.__abort_timer)
        event_bus.subscribe(Events.BUTTON_TAPPED, self.__restart_timer)

    def __unsubscribe(self):
        event_bus.unsubscribe(Events.TIME_CHANGED, self.display_timer)
        event_bus.unsubscribe(Events.WIFI_RESET, self.__abort_timer)
        event_bus.unsubscribe(Events.BUTTON_TAPPED, self.__restart_timer)

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
            print("No timer data found, trying cache")
            self.timer_data = self.api.get_cached_timer()
            
        if self.timer_data:
            print(f"Timer loaded for device {self.device_id}")
            print(self.timer_data)
            return True
        else:
            print(f"No timer found for device {self.device_id}")
            return False
            
    def __abort_timer(self):
        """Abort the timer"""
        self.abort = True

    def __get_end_time(self):
        """Return the start time of the timer. Parsed from the timer data."""
        if self.timer_data and "end_time" in self.timer_data:
            end_time_str = self.timer_data["end_time"]
            print(f"End time string: {end_time_str}")
            year = int(end_time_str[0:4])
            month = int(end_time_str[5:7])
            day = int(end_time_str[8:10])
            hour = int(end_time_str[11:13])
            minute = int(end_time_str[14:16])
            second = int(end_time_str[17:19])

            timestamp = utime.mktime((year, month, day, hour, minute, second, 0, 0))

            print(f"End time: {timestamp}")
            return timestamp
        else:
            return None

        
