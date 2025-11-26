# **Shai-Hulud 2.0 Dead Man's Switch Sinkhole (DMS-SH)**

# **⚠️ DISCLAIMER**

**THIS SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED. THE AUTHORS AND CONTRIBUTORS ACCEPT NO LIABILITY FOR ANY DAMAGES, DATA LOSS, OR CONSEQUENCES RESULTING FROM THE USE OR MISUSE OF THIS CODE.**

**WHILE** THIS SOLUTION HAS BEEN FOUND TO CORRECTLY NEUTRALIZE THE DEAD MAN'S SWITCH (DMS) COMPONENT IN THE SHAI-HULUD 2.0 MALWARE BASED ON CURRENT ANALYSIS, MALWARE VARIANTS CAN CHANGE BEHAVIOR. YOU ARE SOLELY RESPONSIBLE FOR TESTING, VERIFYING, AND ENSURING THE SAFETY OF YOUR ENVIRONMENT BEFORE DEPLOYMENT. **USE AT YOUR OWN RISK.**

## **🛡️ Overview**

This project provides a **containment solution** for the Shai-Hulud 2.0 supply chain malware.

### The Threat:  
Shai-Hulud 2.0 contains a destructive "Dead Man's Switch". It continuously verifies connectivity to GitHub and NPM. If a security team isolates the infected machine from the internet, these checks fail, and the malware activates a wiper to delete user data.  
### The Solution:  
This repository implements a Hybrid Sinkhole:

1. **Local Bridge (Client):** Hijacks DNS and SSL traffic on the infected machine to prevent connection errors.  
2. **Remote Brain (Server):** A Heroku-hosted mock API that returns "Success" JSON responses to the malware, keeping it dormant while you analyze or clean the system.

## **🏗️ Architecture**

1. **Malware** attempts to contact `api.github.com`.  
2. **Local Hosts File** (modified by script) redirects request to `127.0.0.1`.  
3. **Local Bridge** intercepts port 443, terminates SSL using a self-generated trusted certificate.  
4. **Local Bridge** tunnels the request to your **Heroku App**.  
5. **Heroku App** returns a safe, mock JSON response (pacifying the malware).

## **🚀 Deployment Guide**
#### **🛡️ You *SHOULD* check and verify the digest prior to using the files, see `FINGERPRINT.md`🛡️**

### **Phase 1: The "Brain" (Heroku)**

*You* must do this first. The local *scripts need a destination to send traffic to.*\
**You may optionally use the preconfigured instance configured in the client (local bridge) files:**\
`shai-hulud-2-0-dms-sh-bd640bc05c42.herokuapp.com`

1. **Fork/Clone** this repository.  
2. **Create a Heroku App** and deploy this repository to it.  
   * Heroku will automatically detect package.json and start server.js.  
3. **Copy your App URL** (e.g., `https://my-sinkhole-123.herokuapp.com`).  
4. You can verify it works by visiting `https://your-app-url.herokuapp.com/-/whoami` in your browser. It should return `{"username": "sinkhole_safe_user"}`.

### **Phase 2: The "Bridge" (Infected Machine)**

*Run this on the machine you wish to isolate/protect.*\
**You may optionally use the preconfigured instance configured in the client (local bridge) files:**\
`shai-hulud-2-0-dms-sh-bd640bc05c42.herokuapp.com`

1. **Download** one of the defense scripts from this repository to the victim machine.  
2. **Edit the Script:** Open the file and replace the variable `HEROKU_APP_HOST` (or `HEROKU_APP_URL`) with the URL you copied in Phase 1.
3. **Run the Script:**
 
**Option A: Node.js is installed (Recommended)** 

> Use the embedded script which handles certificate generation automatically. 

*Linux / Mac*\
`sudo node setup_v2_embedded.js` 
 
*Windows (Run PowerShell as Admin)*\
`node setup_v2_embedded.js` 
 
**Option B: No Node.js (Python 3)** 
 
> Use the Python version if Node is not available.
 
*Linux / Mac*\
`sudo python3 defense_v4_embedded.py` 
 
*Windows (Run PowerShell as Admin)*\
`python defense_v4_embedded.py` 
 
## **📂 Repository Structure**

| File | Description |
| :---- | :---- |
| **Server Side** |  |
| server.js | The Mock API logic. Mimics GitHub/NPM responses. Runs on Heroku. |
| Procfile | Heroku startup configuration. |
| **Client Side** |  |
| setup_v2_embedded.js | **Primary Node Script.** Contains embedded certs. Sets up trust store, hosts file, and bridge. |
| defense_v4_embedded.py | **Primary Python Script.** Same features as above, for environments without Node.js. |
| setup_v1_external.js | Legacy Node script (requires `ShaiHuludShield.zip`). |
| defense_v3_external.py | Legacy Python script (requires `ShaiHuludShield.zip`). |
| ShaiHuludShield.zip | Contains the certificate and private key |
| local_bridge | Source folder containing the client side scripts files |

## **🛑 Emergency Procedures**

* **Do not close the terminal** running the bridge script. If the bridge stops, the malware will see connection failures and may wipe data.  
* **Do not disconnect the internet** until the bridge script reports `--- BRIDGE ACTIVE ---` and you tested and verified connectivity.  
* To **restore** the machine to normal:  
  1. Stop the script (Ctrl+C).  
  2. Remove the added lines from /etc/hosts (or Windows hosts file).  
  3. Remove the ShaiHuludShield or fake-cert from your OS Trusted Root Certification Authorities.

## **Technical Details**
### TL;DR - By combining OS-level DNS hijacking with a protocol-compliant Mock Server, we create an environment where the malware believes it is fully connected, while actually being isolated in a controlled loop. 
 
### The Heroku "Brain" (server.js) is engineered to specifically satisfy the logical checks used by the "Dead Man's Switch."
* NPM Check Verification:
  * Malware Check: requests `https://registry.npmjs.org/-/whoami`.
  * Sinkhole Response: The server listens for `/-/whoami` and returns `200 OK` with `{"username": "sinkhole_safe_user"}`.
  * Result: The malware believes it has a valid connection to NPM and is logged in. **DMS Status: SAFE**.
* GitHub Check Verification:
  * Malware Check: Checks connectivity to `api.github.com` and looks for a repository signature `Sha1-Hulud: The Second Coming`.
  * Sinkhole Response: The server intercepts requests to `api.github.com`, returning `200 OK` and a JSON payload containing a dummy repository with that exact description string.
  * Result: The malware finds the "exfiltration repo," believes the channel is open, and attempts to upload data (which goes nowhere). **DMS Status: SAFE**.
* The Fail-Safe (Catch-All):
  * Malware Behavior: It may attempt random API calls (e.g., creating a new repo, checking limits).
  * Sinkhole Response: The `server.js` includes a wildcard `app.use('*', ...)` route that returns 200 OK for any unknown request.
* Result: Even if the malware makes an unexpected API call, it receives a "Success" status code instead of a "Network Error," preventing the wiper trigger.

### The 1% Risk (SSL Pinning): The only technical scenario where this fails is if the malware authors utilized Certificate Pinning.
* Note: The malware **is not** currently known to implement this.
* What it is: The malware would contain a hardcoded hash of GitHub's actual public key and refuse to connect to anything else, ignoring the System Trust Store.
* Likelihood: Low. This is rare in supply chain scripts because it makes the malware brittle (if GitHub rotates their keys, the malware breaks). Current analysis of Shai-Hulud 2.0 indicates it relies on standard `npm` and system connectivity checks, which respect the System Trust Store.
