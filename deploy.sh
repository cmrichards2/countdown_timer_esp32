#! /bin/bash
# This script is used to deploy the code to the ESP32.
# It will copy the code to the device and reset it.

# Copy all the python files to the device
for file in *.py; do
    echo "Copying $file to device..."
    mpremote connect /dev/ttyUSB0 cp "$file" : || echo "Failed to copy $file"
done

echo "Resetting device..."
mpremote connect /dev/ttyUSB0 reset || echo "Failed to reset device"
