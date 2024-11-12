import json
import machine
import time
import random
from config import Config

class DeviceID:
    @staticmethod
    def get_id():
        """Get the device ID, generating and saving a new one if it doesn't exist"""
        try:
            with open(Config.DEVICE_ID_FILE, 'r') as f:
                data = json.load(f)
                return data['device_id']
        except:
            # Generate new UUID if file doesn't exist or is invalid
            device_id = str(machine.unique_id().hex() + str(time.time() + random.randint(0, 10000000)))
            DeviceID.save_id(device_id)
            return device_id
    
    @staticmethod
    def save_id(device_id):
        """Save the device ID to persistent storage"""
        with open(Config.DEVICE_ID_FILE, 'w') as f:
            json.dump({'device_id': device_id}, f) 
