from machine import Pin, PWM, Timer

class LEDFader:
    MIN_BRIGHTNESS = 0
    MAX_BRIGHTNESS = 1023
    FADE_INCREMENT = 50
    FADE_PERIOD_MS = 20
    PWM_FREQ = 1000

    def __init__(self, led_pin_number):
        self.led_pin = Pin(led_pin_number, Pin.OUT)
        self.brightness = self.MIN_BRIGHTNESS
        self.increment = self.FADE_INCREMENT
        self.pwm = PWM(self.led_pin, freq=self.PWM_FREQ)
        self.fade_timer = Timer(0)
        self.stopped = False
        self.fade_timer.init(period=self.FADE_PERIOD_MS,
                           mode=Timer.PERIODIC,
                           callback=self._fade_led)

    def _fade_led(self, timer):
        if self.stopped:
            return
        
        self.pwm.duty(self.brightness)
        self.brightness += self.increment
        
        # Check bounds and reverse direction if needed
        if self.brightness >= self.MAX_BRIGHTNESS:
            self.brightness = self.MAX_BRIGHTNESS
            self.increment = -self.FADE_INCREMENT
        elif self.brightness <= self.MIN_BRIGHTNESS:
            self.brightness = self.MIN_BRIGHTNESS 
            self.increment = self.FADE_INCREMENT

    def stop(self):
        self.stopped = True
        self.fade_timer.deinit()
        self.pwm.deinit()
