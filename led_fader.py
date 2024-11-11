from machine import Pin, PWM, Timer
from config import Config

class LEDFader:
    def __init__(self, led_pin_number):
        self.led_pin = Pin(led_pin_number, Pin.OUT)
        self.brightness = Config.LED_MIN_BRIGHTNESS
        self.increment = Config.LED_FADE_INCREMENT
        self.pwm = PWM(self.led_pin, freq=Config.LED_PWM_FREQ)
        self.fade_timer = Timer(0)
        self.stopped = False
        self.fade_timer.init(period=Config.LED_FADE_PERIOD_MS,
                           mode=Timer.PERIODIC,
                           callback=self._fade_led)

    def _fade_led(self, timer):
        if self.stopped:
            return
        
        self.pwm.duty(self.brightness)
        self.brightness += self.increment
        
        if self.brightness >= Config.LED_MAX_BRIGHTNESS:
            self.brightness = Config.LED_MAX_BRIGHTNESS
            self.increment = -Config.LED_FADE_INCREMENT
        elif self.brightness <= Config.LED_MIN_BRIGHTNESS:
            self.brightness = Config.LED_MIN_BRIGHTNESS 
            self.increment = Config.LED_FADE_INCREMENT

    def stop(self):
        self.stopped = True
        self.fade_timer.deinit()
        self.pwm.deinit()
