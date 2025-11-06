import json
import ssl
import logging
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from functools import wraps
from collections import defaultdict
from typing import Dict, Optional
from datetime import datetime
import secrets
import hashlib
from phi_3_vision_mlx import load, generate

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='server.log'
)

# Security Configuration
class SecurityConfig:
    def __init__(self):
        self.keys_file = 'api_keys.json'
        self.API_KEYS = self._load_keys()
        self.RATE_LIMIT_WINDOW = 60
        self.MAX_CONTENT_LENGTH = 1024 * 1024
        self.request_history = defaultdict(list)

    def _load_keys(self):
        try:
            with open(self.keys_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def validate_api_key(self, api_key: str) -> bool:
        return api_key in self.API_KEYS

    def check_rate_limit(self, api_key: str) -> bool:
        now = time.time()
        user_requests = self.request_history[api_key]
        user_requests = [req_time for req_time in user_requests
                        if now - req_time < self.RATE_LIMIT_WINDOW]
        self.request_history[api_key] = user_requests
        return len(user_requests) < self.API_KEYS[api_key]["rate_limit"]

# Initialize security config
security_config = SecurityConfig()

# Load model
preload = load()

def require_api_key(f):
    @wraps(f)
    def decorated(self, *args, **kwargs):
        api_key = self.headers.get('X-API-Key')

        if not api_key:
            self.send_error(401, "API key required")
            return None

        if not security_config.validate_api_key(api_key):
            self.send_error(403, "Invalid API key")
            return None

        if not security_config.check_rate_limit(api_key):
            self.send_error(429, "Rate limit exceeded")
            return None

        security_config.log_request(api_key)
        return f(self, *args, **kwargs)
    return decorated

class SecureAPIHandler(BaseHTTPRequestHandler):
    def _send_json_response(self, data: dict, status: int = 200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-Frame-Options', 'DENY')
        self.send_header('X-XSS-Protection', '1; mode=block')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def _validate_content_length(self) -> Optional[str]:
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > security_config.MAX_CONTENT_LENGTH:
                return "Request too large"
            return None
        except ValueError:
            return "Invalid Content-Length header"

    @require_api_key
    def do_POST(self):
        try:
            # Validate request
            if self.path != "/v1/completions":
                self.send_error(404, "Not Found")
                return

            error = self._validate_content_length()
            if error:
                self.send_error(413, error)
                return

            # Process request
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            request = json.loads(post_data.decode('utf-8'))

            # Validate request data
            if 'prompt' not in request:
                self.send_error(400, "Missing 'prompt' field")
                return

            prompts = request.get('prompt', '')
            max_tokens = min(request.get('max_tokens', 512), 1024)  # Limit max tokens

            # Generate response
            if isinstance(prompts, str):
                prompts = [prompts]

            responses = generate(prompts, preload=preload, max_tokens=max_tokens)
            if isinstance(responses, str):
                responses = [responses]

            # Log successful request
            logging.info(f"Successful request - API Key: {self.headers.get('X-API-Key')[-8:]}")

            # Send response
            response = {
                "model": "phi-3-vision",
                "responses": responses,
                "timestamp": datetime.utcnow().isoformat()
            }
            self._send_json_response(response)

        except json.JSONDecodeError:
            self.send_error(400, "Invalid JSON")
        except Exception as e:
            logging.error(f"Error processing request: {str(e)}")
            self.send_error(500, "Internal Server Error")

def run(host='127.0.0.1', port=8000, use_ssl=True):
    """
    Run the secure API server

    Parameters:
        host (str): Host address to bind to (default: localhost)
        port (int): Port to listen on
        use_ssl (bool): Whether to use SSL/TLS
    """
    server_address = (host, port)
    httpd = HTTPServer(server_address, SecureAPIHandler)

    if use_ssl:
        # SSL Configuration
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        try:
            ssl_context.load_cert_chain(
                certfile='server.crt',
                keyfile='server.key'
            )
            httpd.socket = ssl_context.wrap_socket(httpd.socket, server_side=True)
            protocol = "HTTPS"
        except FileNotFoundError:
            logging.warning("SSL certificates not found. Falling back to HTTP")
            protocol = "HTTP"
    else:
        protocol = "HTTP"

    print(f"Starting secure server on {protocol}://{host}:{port}")
    print(f"Default API Key: {security_config.API_KEYS['default_key']['key']}")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        httpd.server_close()

if __name__ == "__main__":
    # Generate self-signed certificates for development
    try:
        import subprocess
        subprocess.run([
            'openssl', 'req', '-x509', '-newkey', 'rsa:4096', '-nodes',
            '-out', 'server.crt', '-keyout', 'server.key',
            '-days', '365', '-subj', '/CN=localhost'
        ])
    except Exception as e:
        logging.warning(f"Failed to generate SSL certificates: {e}")

    run()
