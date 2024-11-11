#! /bin/bash

for file in *.py; do
    echo "Copying $file..."
    mpremote connect /dev/ttyUSB0 cp "$file" : || echo "Failed to copy $file"
done

echo "Resetting device..."
mpremote connect /dev/ttyUSB0 reset || echo "Failed to reset device"
