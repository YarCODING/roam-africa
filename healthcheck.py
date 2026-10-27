import http.server
import socketserver
import os

PORT = int(os.environ.get("PORT", 10000))

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Celery Worker is Running!")

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"Serving healthcheck on port {PORT}")
    httpd.serve_forever()
