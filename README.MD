# Timer Device Application

This is a smart timer device that helps users track and manage time periods. When completed, it will:

- Allow users to perform the initial setup of the hardware device via their mobile phone using Bluetooth
- Connect to WiFi to sync with an online account and timer settings
- Display a countdown timer that can go into negative time
- Provide visual feedback through color changes:
  - Glows green as the timer approaches zero
  - Glows red when time goes past zero
- Detect motion to "wake up" when users walk by
- Allow users to reset the timer with a physical button press
- Sync all timer events with an online service
- Associate each device with a user's online account during setup
- Use an external Real-Time Clock (RTC) Module to keep the timer in sync with the online service

# Application Overview

This is a MicroPython application designed for ESP32 devices that implements a WiFi-connected countdown timer with Bluetooth Low Energy (BLE) provisioning. The system allows users to set up their device via Bluetooth, connect it to WiFi, and sync with an online timer service.

## Core Functionality (implemented)

1. **WiFi Connection Management**
   - Attempts to connect using stored WiFi credentials if they exist
   - If connection fails or no credentials exist, enters a Bluetooth pairing mode
   - Credentials are stored persistently in a JSON file

2. **Bluetooth Pairing Mode**
   - Advertises itself as a BLE device (default name "ESP32_Device")
   - Waits for a mobile app to connect and send WiFi credentials
   - Provides real-time connection status feedback through BLE notifications
   - Uses chunked data transfer to handle larger credential payloads
   - Exposes device ID via BLE for device identification during setup

3. **Timer Functionality**
   - Syncs with an online timer service to fetch countdown settings
   - Maintains local cache of timer data for offline operation
   - Updates countdown in real-time
   - Broadcasts time changes via event system for display and LED updates

4. **Visual Feedback**
   - Uses a PWM-controlled LED that fades in/out during pairing mode
   - LED fading indicates the device is ready to receive WiFi credentials

5. **Factory Reset**
   - Includes a physical button for factory reset functionality
   - Holding the button for >1 second triggers a factory reset
   - Reset clears stored WiFi credentials
   - Short button press triggers timer reset events

6. **Event System**
   - Implements a publish-subscribe event bus
   - Components communicate through events for loose coupling
   - Handles system events like pairing mode, WiFi reset, time changes

## Component Breakdown

- `Application`: Main controller class that orchestrates the overall flow
- `BLEDevice`: Handles BLE communication, device identification, and credential reception
- `WifiConnection`: Manages WiFi connectivity and credential storage
- `CountdownTimer`: Manages timer state and synchronization with online service
- `API`: Handles communication with the online timer service
- `LEDController`: Manages LED animations and visual feedback
- `LEDFader`: Controls PWM-based LED fading effects
- `Button`: Handles button input and duration-based actions
- `EventBus`: Provides publish-subscribe event system
- `Config`: Centralizes configuration settings
- `DeviceID`: Manages unique device identification

## Current State

The application has the basic infrastructure for WiFi provisioning, but the main application logic is still a placeholder.

## Todo 

- [] The app should allow the wifi connection to be setup via a bluetooth connection from a mobile device (like the NEST smoke alarm)
- [] During setup, associate the device with the user in their online account
- [] Fetch the timer associated with the device online (if one has been associated). The online timer and device timer should always be in sync
- [] Display the timer on the screen - the timer should count down and go below zero
- [] Allow the user to reset the timer by pressing the button - this will be recorded via the Rails API
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
