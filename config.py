class Config:
    # Development mode
    DEVELOPMENT_MODE = True

    # API settings
    API_BASE_URL = "https://timer.christopher-richards.net" if not DEVELOPMENT_MODE else "https://terrier-arriving-foal.ngrok-free.app"
    
    # WiFi settings
    WIFI_RETRY_COUNT = 10
    WIFI_RETRY_DELAY_SEC = 1
    WIFI_CREDENTIALS_FILE = "wifi_credentials.json"
    
    # BLE settings
    BLE_NAME_PREFIX = "ESP32_Device"
    BLE_SERVICE_UUID = "0000180F-0000-1000-8000-00805F9B34FB"
    BLE_WIFI_CREDENTIALS_UUID = "00002A1A-0000-1000-8000-00805F9B34FB"
    BLE_WIFI_STATUS_UUID = "00002A1B-0000-1000-8000-00805F9B34FB"
    BLE_ADVERTISING_INTERVAL_MS = 100
    BLE_DEVICE_ID_UUID = "00002A1C-0000-1000-8000-00805F9B34FB"
    PROVISIONING_BUTTON_CONFIRMATION_DURATION_MS = 10000

    # Device ID settings
    DEVICE_ID_FILE = "dev_id.json"

    # API settings
    TIMER_JSON_FILE = "timer.json"
    
    # Pin configurations
    LED_PIN = 13
    BUTTON_PIN = 25
    
    # LED settings
    LED_MIN_BRIGHTNESS = 0
    LED_MAX_BRIGHTNESS = 1023
    LED_FADE_INCREMENT = 50
    LED_FADE_PERIOD_MS = 20
    LED_PWM_FREQ = 1000
    
    # Button settings
    FACTORY_RESET_DURATION_MS = 6000 
    SOFT_RESET_DURATION_MS = 3000
    BUTTON_TAP_DURATION_MS = 1000

    # SoftAP settings
    SOFTAP_IP = "192.168.4.1"
    SOFTAP_SUBNET = "255.255.255.0"
    
    # Provisioning mode selection
    PROVISIONING_MODE_BLE = "ble"
    PROVISIONING_MODE_SOFTAP = "softap"
    DEFAULT_PROVISIONING_MODE = PROVISIONING_MODE_SOFTAP

    # Add new setting for offline presses file
    OFFLINE_PRESSES_FILE = "offline_presses.json"
