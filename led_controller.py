from led_fader import LEDFader
from config import Config
from event_bus import event_bus, Events

class LedController:
    def __init__(self):
        self.led_fader = None
        event_bus.subscribe(Events.ENTERING_PAIRING_MODE, self.entering_pairing_mode)
        event_bus.subscribe(Events.EXITING_PAIRING_MODE, self.stopping_pairing_mode)
        
    def entering_pairing_mode(self):
        """Start the LED fading pattern for pairing mode"""
        if self.led_fader:
            self.led_fader.stop()
        self.led_fader = LEDFader(Config.LED_PIN)
        
    def stopping_pairing_mode(self):
        """Stop any active LED patterns"""
        if self.led_fader:
            self.led_fader.stop()
            self.led_fader = None
