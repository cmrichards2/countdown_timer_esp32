# Application

[Enter description here]

[ ] The app should allow the wifi connection to be setup via a bluetooth connection from a mobile device
[ ] ....

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


## Notes

The ble_advertising.py file is a helper for generating the advertising payload for the ESP32.  It is taken from the MicroPython Bluetooth library and modified to work with the ESP32.
