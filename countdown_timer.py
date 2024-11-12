import time
from config import Config
from api import API
from event_bus import event_bus, Events
import utime

class CountdownTimer:
    def __init__(self, device_id):
        self.device_id = device_id
        self.api = API()
        self.timer_data = None
        self.abort = False
        self.__fetch_timer_settings()
        self.__subscribe()

    def start(self):
        """Start the timer"""
        print("Starting timer")
        while True:
            if self.abort:
                print("Timer aborted")
                self.__unsubscribe()
                break

            if not self.timer_data:
                # Attempt to fetch timer settings from API every minute if no timer data is
                # associated with this device
                self.__fetch_timer_settings()
                time.sleep(60)
            
            if self.timer_data:
                end_time = self.__get_end_time()
                current_time = utime.localtime()
                current_timestamp = utime.mktime(current_time)

                elapsed_seconds = end_time - current_timestamp

                days = elapsed_seconds // 86400
                hours = (elapsed_seconds % 86400) // 3600
                minutes = (elapsed_seconds % 3600) // 60
                seconds = elapsed_seconds % 60

                event_bus.publish(Events.TIME_CHANGED, {
                    "days": days,
                    "hours": hours,
                    "minutes": minutes,
                    "seconds": seconds
                })
                time.sleep(1)


    def __subscribe(self):
        event_bus.subscribe(Events.WIFI_RESET, self.__abort_timer)
        event_bus.subscribe(Events.TIME_CHANGED, self.__on_time_changed)

    def __unsubscribe(self):
        event_bus.unsubscribe(Events.WIFI_RESET, self.__abort_timer)
        event_bus.unsubscribe(Events.TIME_CHANGED, self.__on_time_changed)

    def __fetch_timer_settings(self):
        """
        Fetch timer settings from the online API or local cache.
        Returns True if timer settings were successfully loaded from either source.
        """
        # First try to get from API
        self.timer_data = self.api.get_timer_for_device(self.device_id)
        
        # If API call failed, try to get from cache
        if self.timer_data is None:
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

    def __on_time_changed(self, time_data):
        """Show the time left on the display"""
        print(f"Time changed: {time_data}")

    def __get_end_time(self):
        """Return the start time of the timer. Parsed from the timer data."""
        if self.timer_data:
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

        
