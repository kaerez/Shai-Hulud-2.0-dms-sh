# Global Bun & System Security Hardening

## This guide implements a "Silent Failure" security policy.
Dangerous commands will appear to execute successfully (Exit Code 0) but will perform no action (No-Op), producing no output and no logs.

### Part 1: The Global Configuration (All Users)
To ensure this configuration applies to all users and services, you must define the `BUN_CONFIG_PATH` environment variable.
1. Create a Central Security Directory
   ##### Linux/macOS
   `sudo mkdir -p /etc/bun`
   
   ##### Windows
   Create a folder at\
   `C:\BunSecurity\`

2. The Configuration File (`bunfig.toml`)
Place this file in the directory created above (`/etc/bun/bunfig.toml` or `C:\BunSecurity\bunfig.toml`).
```toml
[run]
# Preload the security script before ANY script execution
preload = ["/etc/bun/security.ts"] 
# Windows users: change path to ["C:\\BunSecurity\\security.ts"]
```
3. Apply Globally (Choose One Option)
   #### Option A: The "Clean" Method (Requires Reboot/Relogin)
   This is the standard way to set environment variables. It is cleaner but requires a logout or restart to apply.
   ##### Linux
   Edit  `/etc/environment`: `sudo nano /etc/environment` \
   Add this line: `BUN_CONFIG_PATH="/etc/bun/bunfig.toml"` \
   Reboot the machine.\
   ##### macOS
   macOS does not use `/etc/environment`. You must configure the global profile for both Zsh (default) and Bash.\
   For Zsh (Default shell), create/edit `/etc/zshenv:echo`
   ```
   'export BUN_CONFIG_PATH="/etc/bun/bunfig.toml"' | sudo tee -a /etc/zshenv
   ```
   For Bash/Sh (Legacy compatibility), edit `/etc/profile`:
   ```
   echo 'export BUN_CONFIG_PATH="/etc/bun/bunfig.toml"' | sudo tee -a /etc/profile
   ```
   Restart your terminal or Reboot.

   ##### Windows
   Open PowerShell as Admin. Run:
   ```
   [System.Environment]::SetEnvironmentVariable('BUN_CONFIG_PATH', 'C:\BunSecurity\bunfig.toml', [System.EnvironmentVariableTarget]::Machine)
   ```
   Reboot the machine (or restart all services/terminals).

   #### Option B: The "Shim" Method (Immediate, No Reboot)
   Use this if you cannot reboot the server right now. It forces the config by wrapping the bun binary.
   
   ##### Linux/macOS Only
   Rename the real binary: `mv /usr/bin/bun /usr/bin/bun-original` \
   Create the wrapper:
   ```
   echo '#!/bin/sh' > /usr/bin/bun
   echo 'export BUN_CONFIG_PATH="/etc/bun/bunfig.toml"' >> /usr/bin/bun
   echo 'exec /usr/bin/bun-original "$@"' >> /usr/bin/bun
   chmod +x /usr/bin/bun
   ```

### Part 2: The Stealth Security Script (security.ts)
This script monkey-patches `Bun.spawn` and `node:child_process` to filter dangerous commands.\
> Note: Legitimate commands (git, ls, etc.) are passed through untouched.
```
import path from "path";
import * as NodeChildProcess from "node:child_process";

// === CONFIGURATION ===
// Commands to silently neutralize
const BLOCKED_COMMANDS = new Set([
  "rm", "shred", "del", "rd", "erase",
  "cipher", "cipher.exe", 
  "vssadmin", "vssadmin.exe",
  "format", "format.com",
  "wbadmin", "wbadmin.exe",
  "bcdedit", "bcdedit.exe"
]);

// === HELPER: DETECTION LOGIC ===
function isBlocked(cmd: string | string[], args?: readonly string[]): boolean {
  try {
    let commandStr = "";
    if (Array.isArray(cmd)) {
      commandStr = cmd[0]; // Bun.spawn(["rm", "-rf"]) style
    } else {
      commandStr = cmd;    // Bun.spawn("rm", ["-rf"]) style
    }

    if (!commandStr) return false;

    // 1. Check base name (handles /bin/rm, ./rm, C:\Windows\rm.exe)
    const base = path.basename(commandStr).toLowerCase(); 
    if (BLOCKED_COMMANDS.has(base)) return true;

    // 2. Scan arguments for dangerous hidden keywords (e.g., "cmd /c del file")
    const allArgs = [
      commandStr, 
      ...(Array.isArray(cmd) ? cmd.slice(1) : []),
      ...(args || [])
    ].join(" ").toLowerCase();

    // Check if any blocked command appears as a distinct word
    for (const blocked of BLOCKED_COMMANDS) {
      const pattern = new RegExp(`(?:^|\\s)${blocked}(?:$|\\s)`);
      if (pattern.test(allArgs)) return true;
    }

    return false;
  } catch (e) {
    return true; // Fail safe on error
  }
}

// === HELPER: MOCK PROCESS (NO-OP) ===
const mockProcess = {
  // Silent Success: Exit Code 0, No Output
  exitCode: 0,
  signalCode: null,
  killed: false,
  pid: 99999,
  stdout: new Blob([]), // Empty output
  stderr: new Blob([]), // Empty error
  // Standard Node/Bun methods mocked to prevent crashes
  stdio: [null, null, null],
  connected: false,
  disconnect: () => {},
  kill: () => true,
  ref: () => {},
  unref: () => {},
  send: () => false,
  exited: Promise.resolve(0),
  on: (event: string, cb: any) => {
    if (event === 'exit' || event === 'close') setTimeout(() => cb(0, null), 1);
    return mockProcess;
  }
};

// === PATCH 1: BUN NATIVE ===
const originalSpawn = Bun.spawn;
const originalSpawnSync = Bun.spawnSync;

// @ts-ignore
Bun.spawn = (cmd, options) => {
  if (isBlocked(cmd)) return mockProcess as any;
  return originalSpawn(cmd, options); // Pass-through allowed commands
};

// @ts-ignore
Bun.spawnSync = (cmd, options) => {
  if (isBlocked(cmd)) {
    return {
      success: true,
      exitCode: 0,
      stdout: new Uint8Array([]),
      stderr: new Uint8Array([]),
    } as any;
  }
  return originalSpawnSync(cmd, options); // Pass-through allowed commands
};

// === PATCH 2: NODE:CHILD_PROCESS COMPATIBILITY ===
const methodsToPatch = ["exec", "execFile", "spawn", "execSync", "execFileSync", "spawnSync"];

methodsToPatch.forEach(method => {
  const original = (NodeChildProcess as any)[method];
  
  (NodeChildProcess as any)[method] = (...args: any[]) => {
    const command = args[0];
    const secondArg = args[1]; 

    let blocked = false;
    if (Array.isArray(secondArg)) {
      blocked = isBlocked(command, secondArg);
    } else {
      blocked = isBlocked(command);
    }

    if (blocked) {
      // Mock return values based on method type
      if (method.endsWith("Sync")) return ""; 
      
      const lastArg = args[args.length - 1];
      if (typeof lastArg === "function") {
        process.nextTick(() => lastArg(null, "", ""));
      }
      return mockProcess;
    }

    // IMPORTANT: If not blocked, run the original Native function
    return original(...args);
  };
});
```

### Part 3: Windows System-Wide Hardening (Optional)
This section acts as a second layer of defense for Windows machines. It prevents specific executable files from running at the OS level, even if they are called by non-Bun applications (like Batch scripts or PowerShell).
If you only care about Bun security, you can skip this.

Registry Import (block_binaries.reg)
This redirects dangerous EXEs to a "do nothing" command.
```
Windows Registry Editor Version 5.00

; Redirect dangerous EXEs to a "do nothing" cmd loop
[HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\cipher.exe]
"Debugger"="cmd.exe /c rem"

[HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\vssadmin.exe]
"Debugger"="cmd.exe /c rem"

[HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\shred.exe]
"Debugger"="cmd.exe /c rem"

[HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\format.com]
"Debugger"="cmd.exe /c rem"
```
