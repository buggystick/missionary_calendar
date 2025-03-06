/***************************************
 * app.js - Express Server
 ***************************************/
const express = require('express');
const path = require('path');

// For Heroku or other platforms, they often set an environment port
const PORT = process.env.PORT || 3000;

const app = express();
app.use(express.json()); // Parse JSON bodies in POST requests

// Serve static files (our index.html, etc.) from /public
app.use(express.static(path.join(__dirname, 'public')));

// In-memory data store for sign-ups: { "YYYY-M-D": { name: "...", phone: "..." }, ... }
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
 * dateKey is something like "2025-3-15"
 */
app.post('/api/signups', (req, res) => {
    const { dateKey, name, phone } = req.body;
    if (!dateKey) {
        return res.status(400).json({ error: 'dateKey is required' });
    }

    // If name/phone are empty, we can treat it as a "clear"
    if (!name && !phone) {
        delete signups[dateKey];
        return res.json({ message: 'Cleared sign-up for ' + dateKey });
    }

    signups[dateKey] = { name, phone };
    return res.json({ message: 'Saved sign-up for ' + dateKey });
});

// Example fallback route
app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Start server
app.listen(PORT, () => {
    console.log(`Server listening on port ${PORT}`);
});
