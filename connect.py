# This script is used to connect to the ESP32 device and send the WiFi credentials.
# It simulates what the mobile application would do when first setting up the device.

import asyncio
from bleak import BleakClient, BleakScanner

# Replace these with your ESP32's UUIDs for the service and characteristics
SERVICE_UUID = "0000180F-0000-1000-8000-00805F9B34FB"
WIFI_CREDENTIALS_UUID = "00002A1A-0000-1000-8000-00805F9B34FB"
WIFI_STATUS_UUID = "00002A1B-0000-1000-8000-00805F9B34FB"  # New UUID for status

ESP32_DEVICE_NAME = "ESP32_Device"  # The name you gave your ESP32's Bluetooth GAP

# Add notification callback
def notification_handler(sender: int, data: bytearray):
    status = data.decode()
    print(f"WiFi Status Update: {status}")

async def connect_and_send_wifi_credentials(ssid: str, password: str):
    # Discover devices
    print("Searching for ESP32 device...")
    devices = await BleakScanner.discover()
    esp32_device = None
    for device in devices:
        if device.name == ESP32_DEVICE_NAME:
            esp32_device = device
            break

    if not esp32_device:
        print(f"Device with name {ESP32_DEVICE_NAME} not found.")
        return

    # Connect to the ESP32 device
    async with BleakClient(esp32_device.address) as client:
        print(f"Connected to {ESP32_DEVICE_NAME}")

        # Subscribe to notifications
        await client.start_notify(WIFI_STATUS_UUID, notification_handler)

        # Get the MTU size
        mtu = client.mtu_size - 3  # Subtract 3 for ATT header
        print(f"MTU size: {mtu}")

        # Prepare the data
        data = f"{ssid}|{password}".encode("utf-8")
        chunks = [data[i:i+mtu] for i in range(0, len(data), mtu)]

        try:
            print("Sending Wi-Fi credentials in chunks...")
            for i, chunk in enumerate(chunks):
                await client.write_gatt_char(WIFI_CREDENTIALS_UUID, chunk)
                print(f"Sent chunk {i+1}/{len(chunks)}")
            
            # Send an "END" marker
            await client.write_gatt_char(WIFI_CREDENTIALS_UUID, b"END")
            print("Credentials sent successfully!")
        except Exception as e:
            print(f"An error occurred: {e}")

        # Wait a bit to receive status updates
        print("Waiting for WiFi connection status...")
        await asyncio.sleep(15)  # Wait up to 15 seconds for status updates

        # Unsubscribe from notifications
        if client.is_connected:
            try:
                await client.stop_notify(WIFI_STATUS_UUID)
                print("Stopped WiFi status notifications.")
            except Exception as e:
                print(f"An error occurred while stopping notifications: {e}")
        else:
            print("Disconnected before stopping notifications.")

# Define the SSID and password
wifi_ssid = "Nest Router"       # Replace with your Wi-Fi SSID
wifi_password = "ACRES-let-neat" # Replace with your Wi-Fi password

# Run the BLE connection and send credentials
asyncio.run(connect_and_send_wifi_credentials(wifi_ssid, wifi_password))
