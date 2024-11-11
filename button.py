from machine import Pin
import time

class Button:
    # This class is used to handle a button on the ESP32.
    # There is an on press event that only triggers once, using debouncing to ensure it only triggers once.
    def __init__(self, pin, on_press):
        self.pin = Pin(pin, Pin.IN, Pin.PULL_DOWN)
        self.pin.irq(trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, handler=self.button_handler)
        self.on_press = on_press
        self.last_press_time = 0
        self.debounce_delay = 200  # 200ms debounce delay
        self.is_pressed = False

    def button_handler(self, pin):
        current_time = time.ticks_ms()
        if pin.value() == True and not self.is_pressed:
            # Check if enough time has passed since last press
            if time.ticks_diff(current_time, self.last_press_time) > self.debounce_delay:
                self.on_press()
                self.last_press_time = current_time
                self.is_pressed = True
        elif pin.value() == False:
            self.is_pressed = False
