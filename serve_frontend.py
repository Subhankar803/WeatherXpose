"""
Weather360 - Frontend Server & API Reverse Proxy
Serves static frontend files from 'frontend/' and reverse-proxies '/api' and '/uploads'
requests to the FastAPI backend at http://127.0.0.1:8000.

Allows a SINGLE ngrok tunnel (e.g., ngrok http 5000) to serve the entire application:
- Frontend UI (HTML, CSS, JS, Assets)
- Backend APIs (/api/auth, /api/citizen-report, /api/map, etc.)
- Uploaded media (/uploads/...)
Without any Mixed Content (HTTPS -> HTTP) or localhost resolution issues for remote users.
"""
import sys
import os
import http.server
import socketserver
import urllib.request
import urllib.error
import urllib.parse

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
BACKEND_URL = os.environ.get("BACKEND_URL", "http://127.0.0.1:8000").rstrip("/")
FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "frontend"))

HOP_BY_HOP = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
}

class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True

class ProxyAndStaticHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=FRONTEND_DIR, **kwargs)

    def is_proxy_path(self):
        parsed = urllib.parse.urlparse(self.path)
        return (
            parsed.path.startswith("/api/")
            or parsed.path == "/api"
            or parsed.path.startswith("/uploads/")
            or parsed.path == "/health"
            or parsed.path == "/docs"
            or parsed.path == "/openapi.json"
        )

    def do_proxy(self):
        target_url = f"{BACKEND_URL}{self.path}"
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else None

        # Forward headers, adjusting Host
        req_headers = {}
        for key, val in self.headers.items():
            if key.lower() not in HOP_BY_HOP and key.lower() != "host":
                req_headers[key] = val
        req_headers["Host"] = "127.0.0.1:8000"

        req = urllib.request.Request(
            target_url,
            data=body,
            headers=req_headers,
            method=self.command,
        )

        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                self.send_response(resp.status)
                for header, val in resp.headers.items():
                    if header.lower() not in HOP_BY_HOP:
                        self.send_header(header, val)
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS, PATCH")
                self.send_header("Access-Control-Allow-Headers", "*")
                self.end_headers()
                self.wfile.write(resp.read())
        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            for header, val in e.headers.items():
                if header.lower() not in HOP_BY_HOP:
                    self.send_header(header, val)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS, PATCH")
            self.send_header("Access-Control-Allow-Headers", "*")
            self.end_headers()
            self.wfile.write(e.read())
        except Exception as e:
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            err_body = f'{{"detail": "Backend proxy error: {str(e)}"}}'
            self.wfile.write(err_body.encode("utf-8"))
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS, PATCH")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()

    def do_GET(self):
        if self.is_proxy_path():
            self.do_proxy()
        else:
            if self.path == "/" or self.path == "":
                self.send_response(302)
                self.send_header("Location", "/home.html")
                self.end_headers()
                return
            super().do_GET()

    def do_POST(self):
        if self.is_proxy_path():
            self.do_proxy()
        else:
            self.send_error(405, "Method Not Allowed")

    def do_PUT(self):
        if self.is_proxy_path():
            self.do_proxy()
        else:
            self.send_error(405, "Method Not Allowed")

    def do_DELETE(self):
        if self.is_proxy_path():
            self.do_proxy()
        else:
            self.send_error(405, "Method Not Allowed")

    def do_PATCH(self):
        if self.is_proxy_path():
            self.do_proxy()
        else:
            self.send_error(405, "Method Not Allowed")


def run():
    server = ThreadedHTTPServer(("", PORT), ProxyAndStaticHTTPRequestHandler)
    print(f"=================================================================")
    print(f" Weather360 Unified Frontend & API Proxy Server running on port {PORT}")
    print(f" - Frontend static directory: {FRONTEND_DIR}")
    print(f" - Forwarding /api requests to: {BACKEND_URL}")
    print(f" - Local URL: http://127.0.0.1:{PORT}/home.html")
    print(f" - Share with ngrok: ngrok http {PORT}")
    print(f"=================================================================")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")

if __name__ == "__main__":
    run()
