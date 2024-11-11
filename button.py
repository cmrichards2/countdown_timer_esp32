from machine import Pin
import time

class Button:
    # This class is used to handle a button on the ESP32.
    # The on_press handler triggers when button is released, passing the duration held.
    def __init__(self, pin, on_press):
        self.pin = Pin(pin, Pin.IN, Pin.PULL_DOWN)
        self.pin.irq(trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, handler=self.button_handler)
        self.on_press = on_press
        self.press_start_time = 0
        self.is_pressed = False

    def button_handler(self, pin):
        current_time = time.ticks_ms()
        if pin.value() == True and not self.is_pressed:
            self.press_start_time = current_time
            self.is_pressed = True
        elif pin.value() == False and self.is_pressed:
            # Button released - calculate duration and trigger handler
            duration = time.ticks_diff(current_time, self.press_start_time)
            self.on_press(duration)
            self.last_press_time = current_time
            self.is_pressed = False
