from machine import Pin
import time

switch = Pin(25, Pin.IN, Pin.PULL_DOWN)

# def switch_handler(pin):
#   print(pin)

# switch.irq(trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, handler=switch_handler)

while True:
    if switch.value() == True:
        print("Switch is pressed!")
    else:
        print("Switch is released!")
    time.sleep(0.1)
