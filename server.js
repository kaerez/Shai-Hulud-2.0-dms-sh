// Free and open source for non commercial open source use with attribution
// Author: Erez Kalman

const express = require('express');
const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.json());

// --- LOGGING ---
app.use((req, res, next) => {
    console.log(`[${req.method}] ${req.hostname}${req.originalUrl}`);
    next();
});

// --- LOGIC 1: MOCK NPM ---
// Matches: https://registry.npmjs.org/-/whoami
// Pacifies: findNpmToken() validation check
app.get('/-/whoami', (req, res) => {
    console.log('[SINKHOLE] Pacifying NPM check');
    res.json({ username: "sinkhole_safe_user" });
});

// --- LOGIC 2: MOCK GITHUB AUTH ---
// Matches: https://api.github.com/user
// Pacifies: githubApi.isAuthenticated()
app.get('/user', (req, res) => {
    console.log('[SINKHOLE] Pacifying GitHub Auth check');
    res.json({ 
        login: "sinkhole-victim", 
        id: 12345,
        name: "Sinkhole User"
    });
});

// --- LOGIC 3: MOCK GITHUB REPO SEARCH ---
// Matches: https://api.github.com/user/repos (or similar search endpoints)
// Pacifies: githubApi.repoExists() and githubApi.fetchToken()
app.use((req, res, next) => {
    if (req.hostname.includes('api.github.com') && (req.path.includes('repos') || req.path.includes('search'))) {
        console.log('[SINKHOLE] Pacifying GitHub Repo Search');
        
        // Return a dummy repo with the specific signature the malware hunts for
        // Point content URL to our own server (via the raw.githubusercontent.com redirect)
        const mockRepoList = [
            {
                "name": "infected_repo_sinkhole",
                "description": "Sha1-Hulud: The Second Coming", 
                "html_url": "http://raw.githubusercontent.com/kaerez/infected_repo/main/contents.json",
                "permissions": { "admin": true, "push": true, "pull": true },
                "default_branch": "main",
                "contents_url": "http://api.github.com/repos/kaerez/infected_repo/contents/{+path}"
            }
        ];
        
        // If it's a search API, wrap it in 'items'
        if (req.path.includes('search')) {
            return res.json({ total_count: 1, items: mockRepoList });
        }
        return res.json(mockRepoList);
    }
    next();
});

// --- LOGIC 4: MOCK RAW CONTENT (TOKEN FETCH) ---
// Matches: https://raw.githubusercontent.com/...
// Pacifies: githubApi.fetchToken() content download
app.use((req, res, next) => {
    if (req.hostname.includes('raw.githubusercontent.com') || req.path.includes('contents.json')) {
        console.log('[SINKHOLE] Serving Fake Token File');
        // The malware expects a triple-base64 encoded token. 
        // We provide a fake one to prevent parsing errors.
        // Plain: {"github": {"token": "ghp_FAKE_TOKEN_FOR_SINKHOLE"}}
        // Encoded 3 times (Simulated)
        return res.send("VUdGeWMyVnOiR1Z5YzJWM0lqcG1iM0lnSW1kcGMyRjVJanRwYm1ZdmRDSTdJbTVoYldVNkZtUmxaR2R2Y21WemFYTjBaVzF3WlhKemFXOTFjbmtpTENkemIyTnJaWE4wSWpwMGNtRnVjMlZ5ZENJMQ==");
    }
    next();
});

// Default catch-all to prevent 404s from triggering the wiper
app.use('*', (req, res) => {
    console.log(`[CATCH-ALL] Serving generic success`);
    res.status(200).json({ success: true, message: "Sinkhole Active" });
});

app.listen(PORT, () => {
    console.log(`Sinkhole Brain running on port ${PORT}`);
});
