const express = require('express');
const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.json());

// --- LOGIC 1: MOCK NPM ---
// Matches: https://registry.npmjs.org/-/whoami
app.get('/-/whoami', (req, res) => {
    console.log('[SINKHOLE] Pacifying NPM check');
    res.json({ username: "sinkhole_safe_user" });
});

// --- LOGIC 2: MOCK GITHUB ---
// Matches: https://api.github.com/user/repos (or similar search endpoints)
app.use((req, res, next) => {
    // The malware often checks specific GitHub endpoints. 
    // We catch-all generic GitHub API traffic to be safe.
    if (req.hostname.includes('github') || req.path.includes('repos')) {
        console.log('[SINKHOLE] Pacifying GitHub check');
        
        // Return a dummy repo with the specific signature the malware hunts for
        const mockRepoList = [
            {
                "name": "infected_repo_sinkhole",
                "description": "Sha1-Hulud: The Second Coming", 
                "html_url": "http://localhost/infected_repo",
                "permissions": { "admin": true, "push": true, "pull": true }
            }
        ];
        return res.json(mockRepoList);
    }
    next();
});

// Default catch-all to prevent 404s from triggering the wiper
app.use('*', (req, res) => {
    console.log(`[CATCH-ALL] ${req.method} ${req.originalUrl}`);
    res.status(200).json({ success: true, message: "Sinkhole Active" });
});

app.listen(PORT, () => {
    console.log(`Sinkhole Brain running on port ${PORT}`);
});
