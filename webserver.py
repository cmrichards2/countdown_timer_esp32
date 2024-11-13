import http.server
import ssl

# Port number for the HTTPS server
PORT = 8000

# Define the handler to serve files from the current directory
handler = http.server.SimpleHTTPRequestHandler

# Create the HTTP server instance
httpd = http.server.HTTPServer(("localhost", PORT), handler)

# Wrap the server's socket with SSL for HTTPS
httpd.socket = ssl.wrap_socket(
    httpd.socket,
    certfile="server.pem",  # Path to your SSL certificate file
    server_side=True,
)

print(f"Serving on https://localhost:{PORT}")
httpd.serve_forever()
