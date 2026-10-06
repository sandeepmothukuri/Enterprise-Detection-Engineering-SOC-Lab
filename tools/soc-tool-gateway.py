#!/usr/bin/env python3
"""
SOC Tools Local Gateway Server
==============================
Provides responsive local web interfaces on ports:
- 8443 / 8000: DFIR-IRIS Case Management
- 8081: MISP Threat Intelligence Hub
- 8889: Velociraptor DFIR & VQL Console
- 9101 / 9102: StackStorm SOAR Console
"""

import sys
import os
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
import ssl

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

DASHBOARDS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "dashboards"))

class ProxyHandler(SimpleHTTPRequestHandler):
    target_page = "index.html"
    
    def __init__(self, *args, target_page="index.html", **kwargs):
        self.target_page = target_page
        super().__init__(*args, directory=DASHBOARDS_DIR, **kwargs)

    def do_GET(self):
        if self.path == "/" or self.path == "":
            self.path = f"/{self.target_page}"
        return super().do_GET()

def make_handler(target_page):
    return type('CustomHandler', (ProxyHandler,), {'target_page': target_page})

def run_server(port, target_page, use_ssl=False):
    handler_class = make_handler(target_page)
    try:
        server = HTTPServer(('0.0.0.0', port), handler_class)
        if use_ssl:
            # We can use standard HTTP or self-signed if cert exists
            cert_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config", "opensearch", "certs", "opensearch-admin.pem"))
            key_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config", "opensearch", "certs", "opensearch-admin-key.pem"))
            if os.path.exists(cert_file) and os.path.exists(key_file):
                ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
                ctx.load_cert_chain(certfile=cert_file, keyfile=key_file)
                server.socket = ctx.wrap_socket(server.socket, server_side=True)
        
        protocol = "https" if use_ssl else "http"
        print(f"[+] Started Gateway on {protocol}://0.0.0.0:{port} -> {target_page}")
        server.serve_forever()
    except Exception as e:
        print(f"[-] Port {port} gateway notice: {e}")

def main():
    servers = [
        (8081, "08_misp_ti.html", False),             # MISP
        (8889, "09_velociraptor.html", False),        # Velociraptor
        (9101, "02_incident_operations.html", False), # StackStorm SOAR
        (8443, "06_iris_cases.html", False),          # DFIR-IRIS (HTTP fallback for convenience)
    ]
    
    threads = []
    for port, page, is_ssl in servers:
        t = threading.Thread(target=run_server, args=(port, page, is_ssl), daemon=True)
        t.start()
        threads.append(t)
        
    print("[*] All SOC Tool Gateways initialized. Keeping process alive.")
    try:
        while True:
            threading.Event().wait(3600)
    except KeyboardInterrupt:
        print("Stopping gateways...")

if __name__ == "__main__":
    main()
