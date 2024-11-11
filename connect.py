import asyncio
from bleak import BleakClient, BleakScanner

# Replace these with your ESP32's UUIDs for the service and characteristics
SERVICE_UUID = "0000180F-0000-1000-8000-00805F9B34FB"
WIFI_SSID_CHAR_UUID = "00002A19-0000-1000-8000-00805F9B34FB"
WIFI_PASS_CHAR_UUID = "00002A1A-0000-1000-8000-00805F9B34FB"

ESP32_DEVICE_NAME = "ESP32_Device"  # The name you gave your ESP32's Bluetooth GAP

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

        # Write SSID and password to respective characteristics
        try:
            print("Sending Wi-Fi SSID...")
            await client.write_gatt_char(WIFI_SSID_CHAR_UUID, ssid.encode("utf-8"))
            
            print("Sending Wi-Fi password...")
            await client.write_gatt_char(WIFI_PASS_CHAR_UUID, password.encode("utf-8"))
            
            print("Credentials sent successfully!")
        except Exception as e:
            print(f"An error occurred: {e}")

# Define the SSID and password
wifi_ssid = "Nest Router"       # Replace with your Wi-Fi SSID
wifi_password = "ACRES-let-neat" # Replace with your Wi-Fi password

# Run the BLE connection and send credentials
asyncio.run(connect_and_send_wifi_credentials(wifi_ssid, wifi_password))
