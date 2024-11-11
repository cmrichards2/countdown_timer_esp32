#! /bin/bash

for file in *.py; do
    mpremote connect /dev/ttyUSB0 cp "$file" :
done
