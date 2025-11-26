# **Shai-Hulud 2.0 Dead Man's Switch Sinkhole (DMS-SH)**

# **⚠️ DISCLAIMER**

**THIS SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED. THE AUTHORS AND CONTRIBUTORS ACCEPT NO LIABILITY FOR ANY DAMAGES, DATA LOSS, OR CONSEQUENCES RESULTING FROM THE USE OR MISUSE OF THIS CODE.**

**WHILE** THIS SOLUTION HAS BEEN FOUND TO CORRECTLY NEUTRALIZE THE DEAD MAN'S SWITCH (DMS) COMPONENT IN THE SHAI-HULUD 2.0 MALWARE BASED ON CURRENT ANALYSIS, MALWARE VARIANTS CAN CHANGE BEHAVIOR. YOU ARE SOLELY RESPONSIBLE FOR TESTING, VERIFYING, AND ENSURING THE SAFETY OF YOUR ENVIRONMENT BEFORE DEPLOYMENT. **USE AT YOUR OWN RISK.**

## **🛡️ Overview**

This project provides a **containment solution** for the Shai-Hulud 2.0 supply chain malware.

The Threat:  
Shai-Hulud 2.0 contains a destructive "Dead Man's Switch." It continuously verifies connectivity to GitHub and NPM. If a security team isolates the infected machine from the internet, these checks fail, and the malware activates a wiper to delete user data.  
The Solution:  
This repository implements a Hybrid Sinkhole:

1. **Local Bridge (Client):** Hijacks DNS and SSL traffic on the infected machine to prevent connection errors.  
2. **Remote Brain (Server):** A Heroku-hosted mock API that returns "Success" JSON responses to the malware, keeping it dormant while you analyze or clean the system.

## **🏗️ Architecture**

1. **Malware** attempts to contact api.github.com.  
2. **Local Hosts File** (modified by script) redirects request to 127.0.0.1.  
3. **Local Bridge** intercepts port 443, terminates SSL using a self-generated trusted certificate.  
4. **Local Bridge** tunnels the request to your **Heroku App**.  
5. **Heroku App** returns a safe, mock JSON response (pacifying the malware).

## **🚀 Deployment Guide**

### **Phase 1: The "Brain" (Heroku)**

*You* must do this first. The local *scripts need a destination to send traffic to.*

1. **Fork/Clone** this repository.  
2. **Create a Heroku App** and deploy this repository to it.  
   * Heroku will automatically detect package.json and start server.js.  
3. **Copy your App URL** (e.g., https://my-sinkhole-123.herokuapp.com).  
4. You can verify it works by visiting https://your-app-url.herokuapp.com/-/whoami in your browser. It should return {"username": "sinkhole\_safe\_user"}.

### **Phase 2: The "Bridge" (Infected Machine)**

*Run this on the machine you wish to isolate/protect.*

1. **Download** one of the defense scripts from this repository to the victim machine.  
2. **Edit the Script:** Open the file and replace the variable HEROKU\_APP\_HOST (or HEROKU\_APP\_URL) with the URL you copied in Phase 1\.  
3. **Run the Script:**

#### **Option A: Node.js is installed (Recommended)**

Use the embedded script which handles certificate generation automatically.

\# Linux / Mac  
sudo node setup\_v2\_embedded.js

\# Windows (Run PowerShell as Admin)  
node setup\_v2\_embedded.js

#### **Option B: No Node.js (Python 3\)**

Use the Python version if Node is not available.

\# Linux / Mac  
sudo python3 defense\_v4\_embedded.py

\# Windows (Run PowerShell as Admin)  
python defense\_v4\_embedded.py

## **📂 Repository Structure**

| File | Description |
| :---- | :---- |
| **Server Side** |  |
| server.js | The Mock API logic. Mimics GitHub/NPM responses. Runs on Heroku. |
| Procfile | Heroku startup configuration. |
| **Client Side** |  |
| setup\_v2\_embedded.js | **Primary Node Script.** Contains embedded certs. Sets up trust store, hosts file, and bridge. |
| defense\_v4\_embedded.py | **Primary Python Script.** Same features as above, for environments without Node.js. |
| setup\_v1\_external.js | Legacy Node script (requires external zip). |
| defense\_v3\_external.py | Legacy Python script (requires external zip). |
| local\_bridge/ | Source folder for bridge logic (for development only). |

## **🛑 Emergency Procedures**

* **Do not close the terminal** running the bridge script. If the bridge stops, the malware will see connection failures and may wipe data.  
* **Do not disconnect the internet** until the bridge script reports \--- BRIDGE ACTIVE \---.  
* To **restore** the machine to normal:  
  1. Stop the script (Ctrl+C).  
  2. Remove the added lines from /etc/hosts (or Windows hosts file).  
  3. Remove the ShaiHuludShield or fake-cert from your OS Trusted Root Certification Authorities.
