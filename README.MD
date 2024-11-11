# Application

[Enter description here]

- [] The app should allow the wifi connection to be setup via a bluetooth connection from a mobile device (like the NEST smoke alarm)
- [] During setup, associate the device with the user in their online account
- [] Fetch the timer associated with the device online (if one has been associated). The online timer and device timer should match
- [] Display the timer on the screen - the timer should count down and go below zero
- [] Allow the user to reset the timer by pressing a button - this will be recorded via the Rails API
- [] The device will glow green as it approaches zero,  and glow red when it goes past zero
- [] The device will come alive when a user walks past the device as detected by the motion sensor

# Code

The application starts running on the ESP32 from the main.py file

## Deploying the application

To copy the python files to the ESP32 run:
```
./deploy.sh
```

To connect to the ESP32 to view the script running, run:
```
mpremote connect /dev/ttyUSB0 
```

## Running the test connection script

To connect to the ESP32 and send WiFi credentials over bluetooth (BLE), run:
```
python3 connect.py
```
This simulates what the mobile application would do when the user is first setting up the device.


## Notes

The ble_advertising.py file is a helper for generating the advertising payload for the ESP32.  It is taken from the MicroPython Bluetooth library and modified to work with the ESP32.
