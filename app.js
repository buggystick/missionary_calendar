const express = require('express');
const path = require('path');

const PORT = process.env.PORT || 3000;

const app = express();
app.use(express.json());

// Serve static files (index.html, etc.) from /public
app.use(express.static(path.join(__dirname, 'public')));

// In-memory signups storage (replace with database for persistence)
let signups = {};

/**
 * GET /api/signups
 * Returns all signups as JSON
 */
app.get('/api/signups', (req, res) => {
    res.json(signups);
});

/**
 * POST /api/signups
 * Expects { dateKey, name, phone } in JSON body
 * If name and phone are empty, it clears the sign-up for that dateKey.
 */
app.post('/api/signups', (req, res) => {
    const { dateKey, name, phone } = req.body;
    if (!dateKey) {
        return res.status(400).json({ error: 'dateKey is required' });
    }

    // If name/phone are empty, clear the sign-up
    if (!name && !phone) {
        delete signups[dateKey];
        return res.json({ message: `Cleared sign-up for ${dateKey}` });
    }

    // Otherwise, save the sign-up
    signups[dateKey] = { name, phone };
    return res.json({ message: `Saved sign-up for ${dateKey}` });
});

// Fallback route: serve the index.html for any unknown paths
app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Start the server
app.listen(PORT, () => {
    console.log(`Server listening on port ${PORT}`);
});
