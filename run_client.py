import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from dotenv import load_dotenv
from livekit import api

# Load credentials from .env file
load_dotenv()

class ClientHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        # Handle CORS preflight requests
        self.send_response(200, "ok")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "X-Requested-With, Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed_url = urlparse(self.path)
        
        if parsed_url.path == "/token":
            # Generate LiveKit Token
            query_params = parse_qs(parsed_url.query)
            room_name = query_params.get("room", ["friday-room"])[0]
            identity = query_params.get("identity", ["Tony"])[0]
            
            try:
                # Retrieve from environment
                api_key = os.getenv("LIVEKIT_API_KEY", "devkey")
                api_secret = os.getenv("LIVEKIT_API_SECRET", "secret")
                
                # Build token
                token = (
                    api.AccessToken(
                        api_key=api_key,
                        api_secret=api_secret,
                    )
                    .with_identity(identity)
                    .with_name(identity)
                    .with_grants(
                        api.VideoGrants(
                            room_join=True,
                            room=room_name,
                        )
                    )
                    .to_jwt()
                )
                
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"token": token}).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
                
        elif parsed_url.path == "/config":
            # Send current URL to client so it knows where to connect (local or cloud)
            url = os.getenv("LIVEKIT_URL", "ws://localhost:7880")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"url": url}).encode("utf-8"))
            
        elif parsed_url.path in ["", "/", "/index.html"]:
            # Serve index.html from client/
            try:
                with open("client/index.html", "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(content)
            except FileNotFoundError:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"index.html not found. Make sure client/index.html exists.")
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")

def run(port=3000):
    server_address = ('', port)
    httpd = HTTPServer(server_address, ClientHandler)
    print(f"FRIDAY Web Client running at http://localhost:{port}/")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    print("\nServer stopped.")

if __name__ == "__main__":
    run()
