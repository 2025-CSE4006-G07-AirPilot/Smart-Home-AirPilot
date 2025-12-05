require('dotenv').config();
const express = require('express');
const cors = require('cors');
const path = require('path');
const mysql = require('mysql2/promise');
const swaggerUi = require('swagger-ui-express');
const { randomUUID } = require('crypto');

const app = express();
const PORT = process.env.PORT || 3001;

const sslMode = (process.env.MYSQL_SSL_MODE || '').toUpperCase();
const sslConfig = sslMode === 'REQUIRED'
  ? { rejectUnauthorized: true, ca: process.env.MYSQL_SSL_CA }
  : undefined;

const DB_CONFIG = {
  host: process.env.MYSQL_HOST || 'localhost',
  user: process.env.MYSQL_USER || 'root',
  password: process.env.MYSQL_PASSWORD || '',
  database: process.env.MYSQL_DATABASE || 'puripilot_db',
  port: process.env.MYSQL_PORT ? Number(process.env.MYSQL_PORT) : 3306,
  ssl: sslConfig,
  waitForConnections: true,
  connectionLimit: 10
};

app.use(cors());
app.use(express.json({ limit: '5mb' }));

// Serve built/static front-end assets from /example
const staticDir = path.join(__dirname, 'example');
app.use(express.static(staticDir));

let pool;

async function initDb() {
  pool = await mysql.createPool(DB_CONFIG);
  await pool.query(`CREATE TABLE IF NOT EXISTS devices (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    mode ENUM('OFF','LOW','NORMAL','HIGH','TURBO') NOT NULL DEFAULT 'OFF',
    smell_class ENUM('BACKGROUND','FRAGRANCE','BAD') NOT NULL DEFAULT 'BACKGROUND',
    last_seen DATETIME NULL,
    createdAt DATETIME NOT NULL,
    updatedAt DATETIME NOT NULL
  )`);

  // lightweight migrations in case an older schema exists (MySQL 5.7 compat)
  async function ensureColumn(table, column, definition) {
    const [rows] = await pool.query(
      'SELECT COLUMN_NAME FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ? AND COLUMN_NAME = ? LIMIT 1',
      [DB_CONFIG.database, table, column]
    );
    if (!rows.length) {
      await pool.query(`ALTER TABLE ${table} ADD COLUMN ${definition}`);
    }
  }

  await ensureColumn('devices', 'mode', "mode ENUM('OFF','LOW','NORMAL','HIGH','TURBO') NOT NULL DEFAULT 'OFF'");
  await ensureColumn('devices', 'smell_class', "smell_class ENUM('BACKGROUND','FRAGRANCE','BAD') NOT NULL DEFAULT 'BACKGROUND'");
  await ensureColumn('devices', 'last_seen', 'last_seen DATETIME NULL');
  await ensureColumn('devices', 'createdAt', 'createdAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP');
  await ensureColumn('devices', 'updatedAt', 'updatedAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP');

  await pool.query(`CREATE TABLE IF NOT EXISTS floorplans (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    data MEDIUMTEXT NOT NULL,
    createdAt DATETIME NOT NULL,
    updatedAt DATETIME NOT NULL
  )`);

  const [rows] = await pool.query('SELECT COUNT(*) as cnt FROM devices');
  if (rows[0].cnt === 0) {
    const now = new Date();
    const nowDb = toMySQLDateTime(now);
    await pool.query(
      'INSERT INTO devices (id, name, mode, smell_class, last_seen, createdAt, updatedAt) VALUES (?,?,?,?,?,?,?)',
      ['lg-puricare-1', 'Lg Puricare', 'NORMAL', 'BACKGROUND', nowDb, nowDb, nowDb]
    );
  }
}

function toIso(date) {
  return date ? new Date(date).toISOString() : null;
}

function toMySQLDateTime(dateLike) {
  if (!dateLike) return null;
  const d = new Date(dateLike);
  if (isNaN(d.getTime())) return null;
  const pad = (n) => String(n).padStart(2, '0');
  const yyyy = d.getFullYear();
  const MM = pad(d.getMonth() + 1);
  const dd = pad(d.getDate());
  const hh = pad(d.getHours());
  const mm = pad(d.getMinutes());
  const ss = pad(d.getSeconds());
  return `${yyyy}-${MM}-${dd} ${hh}:${mm}:${ss}`;
}

function deviceRowToDto(row) {
  return {
    id: row.id,
    name: row.name,
    mode: row.mode,
    smell_class: row.smell_class,
    last_seen: toIso(row.last_seen),
    createdAt: toIso(row.createdAt),
    updatedAt: toIso(row.updatedAt)
  };
}

async function getDevice(id) {
  const [rows] = await pool.query('SELECT * FROM devices WHERE id = ?', [id]);
  return rows[0] ? deviceRowToDto(rows[0]) : null;
}

app.get('/api/health', async (req, res) => {
  res.json({ status: 'ok', time: new Date().toISOString() });
});

// Root route serves the front-end entry (index.html)
app.get('/', (req, res) => {
  res.sendFile(path.join(staticDir, 'index.html'));
});

// Devices
app.get('/api/devices', async (req, res) => {
  try {
    const [rows] = await pool.query('SELECT * FROM devices');
    res.json(rows.map(deviceRowToDto));
  } catch (err) {
    res.status(500).json({ error: 'server_error', detail: err.message });
  }
});

app.get('/api/devices/:id', async (req, res) => {
  try {
    const device = await getDevice(req.params.id);
    if (!device) return res.status(404).json({ error: 'not found' });
    res.json(device);
  } catch (err) {
    res.status(500).json({ error: 'server_error', detail: err.message });
  }
});

app.post('/api/devices', async (req, res) => {
  const body = req.body || {};
  const now = new Date();
  const nowDb = toMySQLDateTime(now);
  const id = body.id || randomUUID();
  const name = body.name || 'Lg Puricare';
  try {
    const existing = await getDevice(id);
    if (existing) return res.status(409).json({ error: 'id already exists' });
    const lastSeen = toMySQLDateTime(body.last_seen) || nowDb;
    const createdAt = toMySQLDateTime(body.createdAt) || nowDb;
    const updatedAt = nowDb;
    await pool.query(
      'INSERT INTO devices (id, name, mode, smell_class, last_seen, createdAt, updatedAt) VALUES (?,?,?,?,?,?,?)',
      [id, name, body.mode || 'OFF', body.smell_class || 'BACKGROUND', lastSeen, createdAt, updatedAt]
    );
    const device = await getDevice(id);
    res.status(201).json(device);
  } catch (err) {
    res.status(500).json({ error: 'server_error', detail: err.message });
  }
});

app.put('/api/devices/:id', async (req, res) => {
  const body = req.body || {};
  const now = new Date();
  const nowDb = toMySQLDateTime(now);
  const id = req.params.id;
  try {
    // basic validation
    if (body.name && typeof body.name !== 'string') {
      return res.status(400).json({ error: 'invalid name' });
    }

    const existing = await getDevice(id);
    if (!existing) {
      const lastSeenNew = toMySQLDateTime(body.last_seen) || nowDb;
      const createdAtNew = toMySQLDateTime(body.createdAt) || nowDb;
      await pool.query(
        'INSERT INTO devices (id, name, mode, smell_class, last_seen, createdAt, updatedAt) VALUES (?,?,?,?,?,?,?)',
        [id, body.name || 'Lg Puricare', body.mode || 'OFF', body.smell_class || 'BACKGROUND', lastSeenNew, createdAtNew, nowDb]
      );
      const device = await getDevice(id);
      return res.status(201).json(device);
    }
    const name = body.name && body.name.trim() ? body.name.trim() : existing.name;
    const mode = body.mode || existing.mode;
    const smell = body.smell_class || existing.smell_class;
    const lastSeen = toMySQLDateTime(body.last_seen) || toMySQLDateTime(existing.last_seen) || nowDb;
    const createdAt = toMySQLDateTime(existing.createdAt) || nowDb;

    await pool.query(
      'UPDATE devices SET name = ?, mode = ?, smell_class = ?, last_seen = ?, updatedAt = ?, createdAt = ? WHERE id = ?',
      [name, mode, smell, lastSeen, nowDb, createdAt, id]
    );
    const device = await getDevice(id);
    res.json(device);
  } catch (err) {
    console.error('PUT /api/devices/:id failed', err);
    res.status(500).json({ error: 'server_error', detail: err.message });
  }
});

app.patch('/api/devices/:id/mode', async (req, res) => {
  if (!req.body || !req.body.mode) return res.status(400).json({ error: 'mode required' });
  const allowed = ['OFF', 'LOW', 'NORMAL', 'HIGH', 'TURBO'];
  if (!allowed.includes(req.body.mode)) {
    return res.status(400).json({ error: 'invalid mode' });
  }
  const nowDb = toMySQLDateTime(new Date());
  try {
    const existing = await getDevice(req.params.id);
    if (!existing) return res.status(404).json({ error: 'not found' });
    await pool.query('UPDATE devices SET mode = ?, last_seen = ?, updatedAt = ? WHERE id = ?', [req.body.mode, nowDb, nowDb, req.params.id]);
    const device = await getDevice(req.params.id);
    res.json(device);
  } catch (err) {
    res.status(500).json({ error: 'server_error', detail: err.message });
  }
});

app.delete('/api/devices/:id', async (req, res) => {
  try {
    const [result] = await pool.query('DELETE FROM devices WHERE id = ?', [req.params.id]);
    if (result.affectedRows === 0) return res.status(404).json({ error: 'not found' });
    res.status(204).send();
  } catch (err) {
    res.status(500).json({ error: 'server_error', detail: err.message });
  }
});

// Floorplans
app.get('/api/floorplans', async (req, res) => {
  try {
    const [rows] = await pool.query('SELECT * FROM floorplans');
    res.json(rows.map((r) => ({
      id: r.id,
      name: r.name,
      data: r.data,
      createdAt: toIso(r.createdAt),
      updatedAt: toIso(r.updatedAt)
    })));
  } catch (err) {
    res.status(500).json({ error: 'server_error', detail: err.message });
  }
});

app.get('/api/floorplans/latest/current', async (req, res) => {
  try {
    const [rows] = await pool.query('SELECT * FROM floorplans ORDER BY updatedAt DESC LIMIT 1');
    if (!rows.length) return res.status(404).json({ error: 'not found' });
    const r = rows[0];
    res.json({ id: r.id, name: r.name, data: r.data, createdAt: toIso(r.createdAt), updatedAt: toIso(r.updatedAt) });
  } catch (err) {
    res.status(500).json({ error: 'server_error', detail: err.message });
  }
});

app.get('/api/floorplans/:id', async (req, res) => {
  try {
    const [rows] = await pool.query('SELECT * FROM floorplans WHERE id = ?', [req.params.id]);
    if (!rows.length) return res.status(404).json({ error: 'not found' });
    const r = rows[0];
    res.json({ id: r.id, name: r.name, data: r.data, createdAt: toIso(r.createdAt), updatedAt: toIso(r.updatedAt) });
  } catch (err) {
    res.status(500).json({ error: 'server_error', detail: err.message });
  }
});

app.post('/api/floorplans', async (req, res) => {
  const body = req.body || {};
  if (!body.data) return res.status(400).json({ error: 'data required' });
  const now = new Date();
  const id = body.id || `fp-${Date.now()}`;
  try {
    await pool.query('INSERT INTO floorplans (id, name, data, createdAt, updatedAt) VALUES (?,?,?,?,?)', [id, body.name || 'Floorplan', body.data, now, now]);
    res.status(201).json({ id, name: body.name || 'Floorplan', data: body.data, createdAt: now.toISOString(), updatedAt: now.toISOString() });
  } catch (err) {
    res.status(500).json({ error: 'server_error', detail: err.message });
  }
});

app.put('/api/floorplans/:id', async (req, res) => {
  const body = req.body || {};
  if (!body.data) return res.status(400).json({ error: 'data required' });
  const now = new Date();
  try {
    const [existing] = await pool.query('SELECT id FROM floorplans WHERE id = ?', [req.params.id]);
    if (!existing.length) {
      await pool.query('INSERT INTO floorplans (id, name, data, createdAt, updatedAt) VALUES (?,?,?,?,?)', [req.params.id, body.name || 'Floorplan', body.data, now, now]);
      return res.status(201).json({ id: req.params.id, name: body.name || 'Floorplan', data: body.data, createdAt: now.toISOString(), updatedAt: now.toISOString() });
    }
    await pool.query('UPDATE floorplans SET name = ?, data = ?, updatedAt = ? WHERE id = ?', [body.name || existing[0].name || 'Floorplan', body.data, now, req.params.id]);
    res.json({ id: req.params.id, name: body.name || existing[0].name || 'Floorplan', data: body.data, updatedAt: now.toISOString() });
  } catch (err) {
    res.status(500).json({ error: 'server_error', detail: err.message });
  }
});

app.delete('/api/floorplans/:id', async (req, res) => {
  try {
    const [result] = await pool.query('DELETE FROM floorplans WHERE id = ?', [req.params.id]);
    if (result.affectedRows === 0) return res.status(404).json({ error: 'not found' });
    res.status(204).send();
  } catch (err) {
    res.status(500).json({ error: 'server_error', detail: err.message });
  }
});

// Swagger
const openapiDoc = {
  openapi: '3.0.1',
  info: {
    title: 'PuriPilot API',
    version: '1.0.0'
  },
  servers: [{ url: 'http://localhost:' + PORT }],
  paths: {
    '/api/health': { get: { summary: 'Health', responses: { 200: { description: 'ok' } } } },
    '/api/devices': {
      get: { summary: 'List devices', responses: { 200: { description: 'array of devices' } } },
      post: { summary: 'Create device', responses: { 201: { description: 'created' } } }
    },
    '/api/devices/{id}': {
      get: { summary: 'Get device', parameters: [{ in: 'path', name: 'id', required: true }], responses: { 200: { description: 'device' }, 404: { description: 'not found' } } },
      put: { summary: 'Upsert device', parameters: [{ in: 'path', name: 'id', required: true }], responses: { 200: { description: 'updated' }, 201: { description: 'created' } } },
      delete: { summary: 'Delete device', parameters: [{ in: 'path', name: 'id', required: true }], responses: { 204: { description: 'deleted' } } }
    },
    '/api/devices/{id}/mode': {
      patch: { summary: 'Update mode', parameters: [{ in: 'path', name: 'id', required: true }], responses: { 200: { description: 'updated' }, 404: { description: 'not found' } } }
    },
    '/api/floorplans': {
      get: { summary: 'List floorplans', responses: { 200: { description: 'list' } } },
      post: { summary: 'Create floorplan', responses: { 201: { description: 'created' } } }
    },
    '/api/floorplans/latest/current': {
      get: { summary: 'Latest floorplan', responses: { 200: { description: 'latest' }, 404: { description: 'not found' } } }
    },
    '/api/floorplans/{id}': {
      get: { summary: 'Get floorplan', parameters: [{ in: 'path', name: 'id', required: true }], responses: { 200: { description: 'one' }, 404: { description: 'not found' } } },
      put: { summary: 'Upsert floorplan', parameters: [{ in: 'path', name: 'id', required: true }], responses: { 200: { description: 'updated' }, 201: { description: 'created' } } },
      delete: { summary: 'Delete floorplan', parameters: [{ in: 'path', name: 'id', required: true }], responses: { 204: { description: 'deleted' } } }
    }
  }
};

app.use('/api/docs', swaggerUi.serve, swaggerUi.setup(openapiDoc));

// SPA-style fallback: non-API routes serve index.html so client-side routing works
app.get(/^\/(?!api).*/, (req, res) => {
  res.sendFile(path.join(staticDir, 'index.html'));
});

initDb().then(() => {
  app.listen(PORT, () => {
    console.log(`Backend listening on http://localhost:${PORT}`);
    console.log(`Swagger UI at http://localhost:${PORT}/api/docs`);
  });
}).catch((err) => {
  console.error('Failed to init DB', err);
  process.exit(1);
});
