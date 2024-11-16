import network
import socket
import sys
import json
import select
import time
from config import Config
from device_id import DeviceID
from event_bus import event_bus, Events

class SoftAPProvisioning:
    def __init__(self, handle_wifi_credentials):
        self.handle_wifi_credentials = handle_wifi_credentials
        # First deactivate any existing WiFi interfaces
        sta_if = network.WLAN(network.STA_IF)
        sta_if.active(False)
        
        self.ap = network.WLAN(network.AP_IF)
        self.ap.active(False)  # Deactivate AP interface first
        time.sleep(1)  # Give it a moment to clean up
        
        self.web_server = None
        self.dns_server = None
        self.ssid = f"ESP32_Setup_{DeviceID.get_id()[:6]}"
        self.connected = False
        event_bus.publish(Events.ENTERING_PAIRING_MODE)
        
        # Now configure and activate AP
        self.ap.active(True)
        self.ap.config(essid=self.ssid, authmode=network.AUTH_OPEN)
        self.ap.ifconfig(('192.168.4.1', '255.255.255.0', '192.168.4.1', '192.168.4.1'))

    def start(self):
        """Start the SoftAP and web server"""
        self._setup_ap()
        self._start_web_server()
        self.await_credentials_then_disconnect()

    def _setup_ap(self):
        """Configure and start the access point"""
        self.ap.active(True)
        self.ap.config(essid=self.ssid)
        print(f"[SoftAP] Access Point started. SSID: {self.ssid}")
        print(f"[SoftAP] Connect to {self.ssid} and visit http://192.168.4.1")

    def _start_web_server(self):
        """Start the web server and DNS server for the captive portal"""
        self.web_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.web_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.web_server.bind(('0.0.0.0', 80))
        self.web_server.listen(1)
        
        self.dns_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.dns_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.dns_server.bind(('0.0.0.0', 53))
        print("[SoftAP] Web and DNS servers started")

    def await_credentials_then_disconnect(self):
        """Wait for WiFi credentials to be submitted, then shut down AP mode"""
        while not self.connected:
            r, w, err = select.select([self.web_server, self.dns_server], [], [], 1)
            
            for sock in r:
                if sock is self.web_server:
                    self._handle_web_client()
                elif sock is self.dns_server:
                    self._handle_dns_request()

        self.disconnect()

    def disconnect(self):
        """Clean up and shut down AP mode"""
        if self.web_server:
            self.web_server.close()
        if self.dns_server:
            self.dns_server.close()
        
        # Make sure to deactivate AP
        self.ap.active(False)
        time.sleep(1)  # Give it time to clean up
        
        event_bus.publish(Events.EXITING_PAIRING_MODE)
        print("[SoftAP] SoftAP provisioning completed and shut down")

    def _handle_web_client(self):
        """Handle incoming web requests"""
        try:
            client, addr = self.web_server.accept()
            request = client.recv(1024).decode()
            
            if "POST /configure" in request:
                # Extract credentials from POST data
                content_length = int(request.split("Content-Length: ")[1].split("\r\n")[0])
                post_data = request.split("\r\n\r\n")[1][:content_length]
                credentials = self._parse_credentials(post_data)
                
                if credentials:
                    success = self._try_connection(credentials, client)
                    if success:
                        self.connected = True
            else:
                # Serve the configuration page
                self._serve_config_page(client)
            
            client.close()
            
        except Exception as e:
            print(f"[SoftAP] Error handling web client: {e}")
            sys.print_exception(e)

    def _handle_dns_request(self):
        """Handle DNS queries with a redirect to our IP"""
        try:
            data, addr = self.dns_server.recvfrom(1024)
            # Simple DNS response pointing all requests to 192.168.4.1
            response = (
                data[:2]  # Transaction ID
                + b'\x81\x80'  # Flags (Standard response)
                + data[4:6]  # Questions
                + data[4:6]  # Answer RRs
                + b'\x00\x00'  # Authority RRs
                + b'\x00\x00'  # Additional RRs
                + data[12:]    # Original query
                + b'\xc0\x0c'  # Pointer to domain name
                + b'\x00\x01'  # Type A
                + b'\x00\x01'  # Class IN
                + b'\x00\x00\x00\x3c'  # TTL (60 seconds)
                + b'\x00\x04'  # Data length
                + bytes(map(int, '192.168.4.1'.split('.')))  # IP address
            )
            self.dns_server.sendto(response, addr)
        except Exception as e:
            print(f"[SoftAP] Error handling DNS request: {e}")

    def _parse_credentials(self, post_data):
        """Parse the POST data to extract WiFi credentials"""
        try:
            params = {}
            for param in post_data.split("&"):
                key, value = param.split("=")
                params[key] = value.replace("+", " ")
            return {
                "ssid": params.get("ssid", ""),
                "password": params.get("password", ""),
                "setup_code": params.get("setup_code", "")
            }
        except:
            return None

    def _try_connection(self, credentials, client):
        """Attempt to connect to WiFi with provided credentials"""
        # Close the servers temporarily before making the API call
        self.web_server.close()
        self.dns_server.close()
        time.sleep(1)  # Give time for sockets to close properly
        
        # Pass an empty callback since we'll show the result page instead
        success = self.handle_wifi_credentials(
            credentials["ssid"],
            credentials["password"],
            credentials["setup_code"],
            lambda status: None  # Empty callback
        )
        
        # Reopen the servers if connection failed
        if not success:
            self._start_web_server()
            self._serve_error_page(client)
        else:
            self._serve_success_page(client)
        
        time.sleep(2)
        return success


    def _serve_success_page(self, client):
        """Serve a success page when WiFi connection is established"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>WiFi Connected</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                {self._get_common_styles()}
            </style>
        </head>
        <body>
            <div class="container">
                <h1 class="success">Successfully Connected!</h1>
                <p class="message">
                    Your device is now connected to WiFi.<br>
                    You can close this page and start using your device.
                </p>
            </div>
        </body>
        </html>
        """
        response = f"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n{html}"
        client.send(response.encode())

    def _serve_error_page(self, client):
        """Serve an error page when WiFi connection fails"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Connection Failed</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                {self._get_common_styles()}
            </style>
        </head>
        <body>
            <div class="container">
                <h1 class="error">Connection Failed</h1>
                <p class="message">Unable to connect to the WiFi network.<br>Please check your credentials.</p>
                <button onclick="window.history.back()">Try Again</button>
            </div>
        </body>
        </html>
        """
        response = f"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n{html}"
        client.send(response.encode())

    def _serve_config_page(self, client):
        """Serve the WiFi configuration page"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>ESP32 WiFi Setup</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                {self._get_common_styles()}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Connect <span class="device-name">{self.ssid}</span> to WiFi</h1>
                <form method="POST" action="/configure">
                    <div class="form-group">
                        <label for="setup-code">Device Setup Code</label>
                        <input type="text" id="setup-code" name="setup_code" 
                               class="setup-code" maxlength="4" 
                               placeholder="Enter 4-character code" required>
                    </div>
                    <div class="form-group">
                        <label for="ssid">WiFi Network Name</label>
                        <input type="text" id="ssid" name="ssid" placeholder="Enter WiFi name" required value="Nest Router">
                    </div>
                    <div class="form-group">
                        <label for="password">WiFi Password</label>
                        <input type="password" id="password" name="password" placeholder="Enter WiFi password" required value="ACRES-let-nea">
                    </div>
                    <button type="submit">Connect</button>
                </form>
            </div>
        </body>
        </html>
        """
        response = f"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n{html}"
        client.send(response.encode())
    def _get_common_styles(self):
        """Return common CSS styles used across all pages"""
        return """
            body {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                margin: 0;
                padding: 20px;
                background: #f5f5f7;
                color: #1d1d1f;
            }
            .container {
                max-width: 400px;
                margin: 0 auto;
                background: white;
                padding: 25px;
                border-radius: 15px;
                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            }
            h1 {
                text-align: center;
                margin-bottom: 25px;
                font-size: 24px;
                font-weight: 600;
            }
            input {
                width: 100%;
                padding: 12px;
                margin: 10px 0;
                border: 1px solid #d2d2d7;
                border-radius: 8px;
                box-sizing: border-box;
                font-size: 16px;
                transition: border-color 0.2s;
            }
            input:focus {
                outline: none;
                border-color: #0071e3;
            }
            button {
                width: 100%;
                padding: 12px;
                background: #0071e3;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: 500;
                cursor: pointer;
                transition: background-color 0.2s;
            }
            button:hover {
                background: #0077ED;
            }
            .success {
                color: #28a745;
            }
            .error {
                color: #dc3545;
            }
            .success-icon {
                font-size: 48px;
                margin-bottom: 20px;
            }
            .message {
                text-align: center;
                line-height: 1.5;
            }
            .error-icon {
                font-size: 48px;
                margin-bottom: 20px;
                text-align: center;
            }
            .message {
                text-align: center;
                line-height: 1.5;
                margin-bottom: 20px;
            }
            .form-group {
                margin-bottom: 15px;
            }
            .form-group label {
                display: block;
                margin-bottom: 5px;
                font-weight: 500;
            }
            .device-name {
                color: #0071e3;
                font-weight: 600;
            }
            .setup-code {
                font-size: 24px;
                letter-spacing: 2px;
                text-transform: uppercase;
                text-align: center;
            }
            .setup-code::-webkit-input-placeholder {
                font-size: 16px;
                letter-spacing: normal;
            }
        """
