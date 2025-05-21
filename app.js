import herokuSSLRedirect from 'heroku-ssl-redirect';
import express from 'express';
import path from 'path';
import pg from 'pg';
// For ESM usage:
import { createServer } from 'http';
import { WebSocketServer } from 'ws';

const sslRedirect = herokuSSLRedirect.default;
const __dirname = import.meta.dirname;

const PORT = process.env.PORT || 3000;
const DATABASE_URL = process.env.DATABASE_URL;

let pool;

// Create a PostgreSQL connection pool using the DATABASE_URL environment variable
const Pool = pg.Pool;
pool = new Pool({
    connectionString: DATABASE_URL,
    ssl: {
        rejectUnauthorized: false
    }
});

const app = express();
app.use(sslRedirect(['production'], 301));
app.use(express.json());

// Serve static files from /public
app.use(express.static(path.join(__dirname, 'public')));

// Initialize DB table if not present
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

// ----- REST API ENDPOINTS -----

// Serve the main calendar page
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// API: Get all signups
app.get('/api/signups', async (req, res) => {
    try {
        const result = await pool.query('SELECT date_key, name, phone FROM signups');
        const signups = {};
        for (const row of result.rows) {
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
 * Expects { dateKey, name, phone } in JSON body.
 * If name & phone are empty, we DELETE. Otherwise we insert only on first-writer-wins.
 * After updating the DB, broadcast to connected WebSocket clients.
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
            broadcastWsMessage({ event: 'signup-changed', dateKey, name: '', phone: '' });
            return res.json({ message: `Cleared sign-up for ${dateKey}` });
        } else {
            // First-write-wins: try to insert, but if date_key already exists, do nothing
            const insertRes = await pool.query(`
                INSERT INTO signups (date_key, name, phone)
                VALUES ($1, $2, $3)
                ON CONFLICT (date_key)
                DO NOTHING
                RETURNING *
            `, [dateKey, name, phone]);

            if (insertRes.rowCount === 0) {
                // someone else already signed up for this date—leave it alone
                return res.json({ message: `Date ${dateKey} already taken` });
            }

            // only broadcast & report a save when *this* request actually inserted
            broadcastWsMessage({ event: 'signup-changed', dateKey, name, phone });
            return res.json({ message: `Saved sign-up for ${dateKey}` });
        }
    } catch (err) {
        console.error(err);
        return res.status(500).json({ error: 'Database error' });
    }
});

// For React-style SPAs, serve index.html for any unknown route
app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// ----- WEBSOCKET SETUP -----

// Create a raw HTTP server from our Express app
const server = createServer(app);
const wss = new WebSocketServer({ server });
const wsClients = new Set();

wss.on('connection', (ws) => {
    wsClients.add(ws);
    ws.on('close', () => wsClients.delete(ws));
    ws.on('message', (message) => {
        console.log('Received message from client:', message);
    });
});

/**
 * Broadcast a JS object to all connected WebSocket clients
 */
function broadcastWsMessage(msgObj) {
    const jsonStr = JSON.stringify(msgObj);
    for (const ws of wsClients) {
        if (ws.readyState === 1) {
            ws.send(jsonStr);
        }
    }
}

// Start the server if not running a unit test (Vitest)
if (!process.env.IS_VITEST) {
    server.listen(PORT, () => {
        console.log(`Server listening on port ${PORT}`);
    });
}

export default app;
