import sslRedirect from 'heroku-ssl-redirect';
const express = require('express');
const path = require('path');
const { Pool } = require('pg');

// Heroku sets process.env.DATABASE_URL if you added Heroku Postgres
// We'll also respect process.env.PORT
const PORT = process.env.PORT || 3000;
const DATABASE_URL = process.env.DATABASE_URL;


// Create a Pool instance
// SSL is often required in Heroku Postgres.
// Some older DBs might need `ssl: { rejectUnauthorized: false }`
const pool = new Pool({
    connectionString: DATABASE_URL,
    ssl: {
        rejectUnauthorized: false
    }
});

const app = express();
app.use(sslRedirect());
app.use(express.json());

// Serve static files (index.html, etc.) from /public
app.use(express.static(path.join(__dirname, 'public')));

// 1) Ensure the table exists on server startup:
async function initDB() {
    try {
        await pool.query(`
      CREATE TABLE IF NOT EXISTS signups (
        date_key  varchar(20) PRIMARY KEY,
        name      varchar(100),
        phone     varchar(50)
      );
    `);
        console.log('signups table is ready');
    } catch (err) {
        console.error('Error creating table:', err);
    }
}
initDB();

/**
 * GET /api/signups
 * Fetch all signups from the DB and return as an object:
 * { "YYYY-M-D": { name, phone }, ... }
 */
app.get('/api/signups', async (req, res) => {
    try {
        const result = await pool.query('SELECT date_key, name, phone FROM signups');
        // Convert rows into the expected object shape:
        // e.g. if row is { date_key: '2025-3-15', name: 'Alice', phone: '123' },
        // we want signups['2025-3-15'] = { name, phone }
        let signups = {};
        for (let row of result.rows) {
            signups[row.date_key] = { name: row.name, phone: row.phone };
        }
        return res.json(signups);
    } catch (err) {
        console.error(err);
        return res.status(500).json({ error: 'Database error' });
    }
});

/**
 * POST /api/signups
 * Expects { dateKey, name, phone } in JSON body
 * If name and phone are empty, we DELETE. Otherwise we UPSERT.
 */
app.post('/api/signups', async (req, res) => {
    const { dateKey, name, phone } = req.body;
    if (!dateKey) {
        return res.status(400).json({ error: 'dateKey is required' });
    }

    try {
        if (!name && !phone) {
            // Clear the sign-up: DELETE that row
            await pool.query('DELETE FROM signups WHERE date_key = $1', [dateKey]);
            return res.json({ message: `Cleared sign-up for ${dateKey}` });
        } else {
            // UPSERT sign-up.
            // Some Postgres versions let you do INSERT ... ON CONFLICT (date_key) DO UPDATE
            await pool.query(`
        INSERT INTO signups (date_key, name, phone)
        VALUES ($1, $2, $3)
        ON CONFLICT (date_key)
        DO UPDATE SET name = EXCLUDED.name, phone = EXCLUDED.phone
      `, [dateKey, name, phone]);

            return res.json({ message: `Saved sign-up for ${dateKey}` });
        }
    } catch (err) {
        console.error(err);
        return res.status(500).json({ error: 'Database error' });
    }
});

// Fallback route: serve the index.html for any unknown paths
app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Start the server
app.listen(PORT, () => {
    console.log(`Server listening on port ${PORT}`);
});
