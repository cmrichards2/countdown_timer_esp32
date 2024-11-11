from application import Application
from config import Config

app = Application(bluetooth_name=Config.BLE_NAME_PREFIX)
app.start()
