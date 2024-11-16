class TimerDisplay:
    """Handles the display of the timer on the screen (todo)"""

    def __init__(self):
        self.timer_data = None

    def update_time(self, time_data):
        self.timer_data = time_data
        self.display_timer()

    def display_timer(self):
        """Show the time left on the LED display (todo)"""
        print(f"[DISPLAY] Time left: {self.timer_data}")



