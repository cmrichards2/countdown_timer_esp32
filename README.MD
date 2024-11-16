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

# Notes:

- Could use WifiManager for WiFi provisioning: https://github.com/tzapu/WiFiManager ?

# Application Overview

This is a MicroPython application designed for ESP32 devices that implements a WiFi-connected countdown timer with Bluetooth Low Energy (BLE) provisioning. The system allows users to set up their device via Bluetooth, connect it to WiFi, and sync with an online timer service.

## Core Functionality (implemented)

1. **WiFi Connection Management**
   - Attempts to connect using stored WiFi credentials if they exist
   - If connection fails or no credentials exist, enters a Bluetooth pairing mode
   - Credentials are stored persistently in a JSON file

2. **WiFi Provisioning**
   - Allows the user to provision the device with WiFi credentials via a softAP. SoftAP is where the device creates its own WiFi network.
   - The user connects to the softAP using their mobile device and enters the SSID, password and device code through a web page served by the device. The device code is a unique code that the user enters to associate the device with their account - it comes from the online application.
   - The device will then attempt to connect to the WiFi network using the provided credentials

2. **Bluetooth Pairing Mode - currently disabled**
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

- [x] The app should allow the wifi connection to be setup via a bluetooth connection from a mobile device (like the NEST smoke alarm). Update: not using BLE for provisioning anymore
- [x] The wifi credentials for this app can can be provisioned via a softAP
- [x] During setup, associate the device with the user in their online account
- [x] Fetch the timer associated with the device online (if one has been associated). The online timer and device timer should always be in sync
- [] Display the timer on the screen - the timer should count down and go below zero
- [x] Allow the user to reset the timer by pressing the button - this will be recorded via the Rails API
- [] The device will glow green as it approaches zero,  and glow red when it goes past zero
- [] The device will come alive when a user walks past the device as detected by the motion sensor

## Notes

The ble_advertising.py file is a helper for generating the advertising payload for the ESP32.  It is taken from the MicroPython Bluetooth library and modified to work with the ESP32.

log.txt contains a log of the device running and connecting to the internet.

## Event bus communication

```
This section was generated by AI using the following prompt:
Prompt used:
In the "event bus communication" section of the README.MD, add a concise list of all the events that this app publishes from the codebase and which objects respond to those publishings.   Only show the events that this app actually publishes
```

The following events are currently published and handled in the application:

1. **FACTORY_RESET_BUTTON_PRESSED**
   - Published by: `Application#on_button_pressed` (when button held > 10 seconds)
   - Handled by:
     - `WifiConnection.reset` - Clears WiFi credentials
     - `CountdownTimer._factory_reset` - Clears timer data

2. **SOFT_RESET_BUTTON_PRESSED**
   - Published by: `Application#on_button_pressed` (when button held > 5 seconds)
   - Handled by:
     - `WifiConnection.reset` - Clears WiFi credentials

3. **BUTTON_TAPPED**
   - Published by: `Application#on_button_pressed` (when button pressed < 200ms)
   - Currently no handlers

4. **ENTERING_PAIRING_MODE**
   - Published by: `BLEDevice.setup_bluetooth_service`
   - Handled by:
     - `LedController.entering_pairing_mode` - Starts LED fading pattern

5. **EXITING_PAIRING_MODE**
   - Published by: `BLEDevice.disconnect`
   - Handled by:
     - `LedController.stopping_pairing_mode` - Stops LED fading

6. **WIFI_RESET**
   - Published by: `WifiConnection.reset`
   - Handled by:
     - `CountdownTimer.__abort_timer` - Stops the timer

7. **TIME_CHANGED**
   - Published by: `CountdownTimer.start`
   - Handled by:
     - `CountdownTimer.__on_time_changed` - Updates time display

8. **WIFI_CONNECTED**
   - Published by: 
     - `WifiConnection.connect`
     - `WifiConnection._try_reconnect`
   - Currently no handlers

# ESP 32 Setup Information (Ubuntu)

Verify that the ESP32 is connected:

```
ls /dev/ttyUSB*
```

## Ubuntu Setup

```
sudo apt update
sudo apt install git wget flex bison gperf python3 python3-pip python3-setuptools cmake ninja-build ccache libffi-dev libssl-dev dfu-util
sudo apt install python3.10-venv
```

## Install ESP-IDF

```
mkdir -p ~/esp
cd ~/esp
git clone --recursive https://github.com/espressif/esp-idf.git
cd esp-idf
./install.sh
```

```
Also run this on new terminals when pushing new code to the device:
setup environment variables:
. $HOME/esp/esp-idf/export.sh
```

```
/esp-idf/tools/idf.py
idf.py set-target esp32 
idf.py menuconfig
```

## Flashing the device

```
Erase flash:
esptool.py --port /dev/ttyUSB0 erase_flash
```

## Flashing with micro python firmware

Download: https://micropython.org/download/ESP32_GENERIC/
```
pip install esptool
esptool.py --chip esp32 --port /dev/ttyUSB0 write_flash -z 0x1000 ESP32_GENERIC-20241025-v1.24.0.bin 
```

After flashing MicroPython, you can interact with the ESP32 using `mpremote`:

**Install `mpremote`**:

```
`pip install mpremote`
```

**Connect to the ESP32**:

`mpremote connect /dev/ttyUSB0`

## Deploying the application

To copy the python files to the ESP32 run:
```
./deploy.sh ; mpremote connect /dev/ttyUSB0
```

To connect to the ESP32 to view the script running, run:
```
mpremote connect /dev/ttyUSB0 
```

## Running the test connection script

[Bluetooth is not currently the way we want to provision the device. So this script is not currently used and may be out of date]
To connect to the ESP32 and send WiFi credentials over bluetooth (BLE), run:
```
python3 connect.py
```
This simulates what the mobile application would do when the user is first setting up the device.

