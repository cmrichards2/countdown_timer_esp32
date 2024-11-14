import network
import socket
import json
import select
import time
from config import Config
from device_id import DeviceID
from event_bus import event_bus, Events

class SoftAPProvisioning:
    def __init__(self, handle_wifi_credentials):
        self.handle_wifi_credentials = handle_wifi_credentials
        self.ap = network.WLAN(network.AP_IF)
        self.web_server = None
        self.dns_server = None
        self.ssid = f"ESP32_Setup_{DeviceID.get_id()[:6]}"
        self.connected = False
        event_bus.publish(Events.ENTERING_PAIRING_MODE)
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
        print(f"Access Point started. SSID: {self.ssid}")
        print(f"Connect to {self.ssid} and visit http://192.168.4.1")

    def _start_web_server(self):
        """Start the web server and DNS server for the captive portal"""
        self.web_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.web_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.web_server.bind(('0.0.0.0', 80))
        self.web_server.listen(1)
        
        self.dns_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.dns_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.dns_server.bind(('0.0.0.0', 53))
        print("Web and DNS servers started")

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
            print(f"Error handling web client: {e}")

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
            print(f"Error handling DNS request: {e}")

    def _parse_credentials(self, post_data):
        """Parse the POST data to extract WiFi credentials"""
        try:
            params = {}
            for param in post_data.split("&"):
                key, value = param.split("=")
                params[key] = value.replace("+", " ")
            return {
                "ssid": params.get("ssid", ""),
                "password": params.get("password", "")
            }
        except:
            return None

    def _try_connection(self, credentials, client):
        """Attempt to connect to WiFi with provided credentials"""
        # Pass an empty callback since we'll show the result page instead
        success = self.handle_wifi_credentials(
            credentials["ssid"],
            credentials["password"],
            lambda status: None  # Empty callback
        )
        
        if success:
            self._serve_success_page(client)
        else:
            self._serve_error_page(client)
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
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .container {{ max-width: 400px; margin: 0 auto; text-align: center; }}
                .success {{ color: #28a745; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1 class="success">Successfully Connected!</h1>
                <p>Your device is now connected to WiFi.</p>
                <p>You can close this page.</p>
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
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .container {{ max-width: 400px; margin: 0 auto; text-align: center; }}
                .error {{ color: #dc3545; }}
                button {{ width: 200px; padding: 10px; background: #007bff; color: white; border: none; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1 class="error">Connection Failed</h1>
                <p>Unable to connect to the WiFi network. Please check your credentials.</p>
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
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .container {{ max-width: 400px; margin: 0 auto; }}
                form {{ width: 100%; box-sizing: border-box; }}
                input {{ 
                    width: 100%;
                    padding: 8px;
                    margin: 10px 0;
                    box-sizing: border-box;
                }}
                button {{ 
                    width: 100%;
                    padding: 10px;
                    background: #007bff;
                    color: white;
                    border: none;
                    box-sizing: border-box;
                    border-radius: 10px;
                }}
                h1 {{ text-align: center; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>ESP32 WiFi Setup</h1>
                <form method="POST" action="/configure">
                    <input type="text" name="ssid" placeholder="WiFi Name" required>
                    <input type="password" name="password" placeholder="WiFi Password" required>
                    <button type="submit">Connect</button>
                </form>
                <div id="status"></div>
            </div>
        </body>
        </html>
        """
        response = f"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n{html}"
        client.send(response.encode())

    def disconnect(self):
        """Clean up and shut down AP mode"""
        if self.web_server:
            self.web_server.close()
        if self.dns_server:
            self.dns_server.close()
        self.ap.active(False)
        event_bus.publish(Events.EXITING_PAIRING_MODE)
        print("SoftAP provisioning completed and shut down") 
