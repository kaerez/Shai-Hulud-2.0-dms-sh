# ⚠️ DISCLAIMER

**THIS SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED. THE AUTHORS AND CONTRIBUTORS ACCEPT NO LIABILITY FOR ANY DAMAGES, DATA LOSS, OR CONSEQUENCES RESULTING FROM THE USE OR MISUSE OF THIS CODE.**

**WHILE THIS SOLUTION HAS BEEN FOUND TO CORRECTLY NEUTRALIZE THE DEAD MAN'S SWITCH (DMS) COMPONENT IN THE SHAI-HULUD 2.0 MALWARE BASED ON CURRENT ANALYSIS, MALWARE VARIANTS CAN CHANGE BEHAVIOR. YOU ARE SOLELY RESPONSIBLE FOR TESTING, VERIFYING, AND ENSURING THE SAFETY OF YOUR ENVIRONMENT BEFORE DEPLOYMENT. USE AT YOUR OWN RISK.**

---

# Shai-Hulud 2.0 Defense Mechanism (Dead Man's Switch Bypass)

This repository contains tools to neutralize the "Dead Man's Switch" found in the Shai-Hulud 2.0 malware. The malware monitors connections to `api.github.com` and `registry.npmjs.org`. If these connections fail (e.g., during network isolation), the malware wipes the user's home directory.

**This solution creates a local "Sinkhole" that impersonates GitHub and NPM, satisfying the malware's checks while redirecting data to a safe remote logger.**

#### **🛡️ You *SHOULD* check and verify the digest prior to using the files, see `FINGERPRINT.md`🛡️**

## ⚠️ Prerequisite: Cloud Brain (Heroku)
Before running the local defense scripts, you must deploy the "Brain" to Heroku. This is the server that will receive the redirected traffic.\
**You may optionally use the preconfigured instance configured in the client (local bridge) files:**\
`shai-hulud-2-0-dms-sh-bd640bc05c42.herokuapp.com`

1.  Deploy the code in this repo to Heroku.
2.  Note your Heroku URL (e.g., `https://your-app-123.herokuapp.com`).
3.  **EDIT THE SCRIPTS:** You must open the Python/Node scripts and replace `your-app-name.herokuapp.com` with your actual URL.

## Architecture



1.  **Trust Store Injection:** The script generates/extracts a fake SSL certificate and adds it to the OS Trust Store.
2.  **DNS Hijacking:** The script modifies `/etc/hosts` to point `api.github.com` and `registry.npmjs.org` to `127.0.0.1`.
3.  **Local Bridge:** A script listens on port 443 (HTTPS), terminates the SSL connection (using the fake cert), and forwards the request to your Heroku app.

## Choice of Scripts

Choose the version that matches your environment constraints.\
**You may optionally use the preconfigured instance configured in the client (local bridge) files:**\
`shai-hulud-2-0-dms-sh-bd640bc05c42.herokuapp.com`

### Option A: Node.js Available (Recommended)
If the victim machine has Node.js installed.
* **File:** `setup_v2_embedded.js`
* **Usage:**
    * **Linux/Mac:** `sudo node setup_v2_embedded.js`
    * **Windows:** Open PowerShell as Admin -> `node setup_v2_embedded.js`

### Option B: No Node.js (Python required)
If the victim machine does not have Node, but has Python (standard on Linux/Mac).
* **File:** `defense_v4_embedded.py`
* **Usage:**
    * **Linux/Mac:** `sudo python3 defense_v4_embedded.py`
    * **Windows:** Open PowerShell as Admin -> `python defense_v4_embedded.py`

### Option C: External Certificates (Manual)
If you prefer to manage the `ShaiHuludShield.zip` file manually or the embedded versions are failing.
1.  Ensure `ShaiHuludShield.zip` is in the same folder as the script.
2.  Run `sudo node setup_v1_external.js` OR `sudo python3 defense_v3_external.py`.

## 🚨 Critical Warnings

1.  **Do NOT disconnect the internet** until this script is running and reporting "BRIDGE ACTIVE".
2.  **Do NOT close the terminal** running the script. If the bridge stops while the `hosts` file is modified, the malware checks will fail, and the wiper will trigger.
3.  **Cleanup:** To restore the machine:
    * Remove lines from `/etc/hosts`.
    * Remove the certificate from the Trust Store.
