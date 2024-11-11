# Application Overview

This is a MicroPython application designed for ESP32 devices that implements a WiFi provisioning system using Bluetooth Low Energy (BLE). Here's how it works:

## Core Functionality

1. **WiFi Connection Management**
   - Attempts to connect using stored WiFi credentials if they exist
   - If connection fails or no credentials exist, enters a Bluetooth pairing mode
   - Credentials are stored persistently in a JSON file

2. **Bluetooth Pairing Mode**
   - Advertises itself as a BLE device (default name "ESP32_Device")
   - Waits for a mobile app to connect and send WiFi credentials
   - Provides real-time connection status feedback through BLE notifications
   - Uses chunked data transfer to handle larger credential payloads

3. **Visual Feedback**
   - Uses a PWM-controlled LED that fades in/out during pairing mode
   - LED fading indicates the device is ready to receive WiFi credentials

4. **Factory Reset**
   - Includes a physical button for factory reset functionality
   - Holding the button for >1 second triggers a factory reset
   - Reset clears stored WiFi credentials

## Component Breakdown

- `Application`: Main controller class that orchestrates the overall flow
- `BLEDevice`: Handles BLE communication and credential reception
- `WifiConnection`: Manages WiFi connectivity and credential storage
- `LEDFader`: Controls LED animations for visual feedback
- `Button`: Handles button input and duration-based actions
- `Config`: Centralizes configuration settings

## Current State

The application has the basic infrastructure for WiFi provisioning, but the main application logic is still a placeholder:

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
