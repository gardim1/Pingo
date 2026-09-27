import express, { Request, Response } from 'express';
import path from 'path';
import { fileURLToPath } from 'url';
import { getBackendHeaders, getBackendUrl } from './auth.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const port = parseInt(process.env.PORT || '8080', 10);
const host = process.env.HOST || '0.0.0.0';

app.use(express.json());

// Log incoming requests sanitarily
app.use((req, res, next) => {
  const start = Date.now();
  res.on('finish', () => {
    const duration = Date.now() - start;
    if (req.path.startsWith('/api/') || req.path === '/health') {
      console.log(JSON.stringify({
        path: req.path,
        method: req.method,
        status: res.statusCode,
        duration_ms: duration,
      }));
    }
  });
  next();
});

// Health check for Cloud Run startup probe & monitoring
app.get('/health', (req: Request, res: Response) => {
  res.status(200).json({ status: 'ok', service: 'pingo-frontend' });
});

// Test connectivity to private backend
app.get('/api/pingo/health', async (req: Request, res: Response) => {
  try {
    const backendUrl = getBackendUrl();
    const headers = await getBackendHeaders();
    const backendRes = await fetch(`${backendUrl}/health`, {
      method: 'GET',
      headers,
    });
    const data = await backendRes.json().catch(() => ({ status: backendRes.status }));
    res.status(backendRes.status).json(data);
  } catch (err: any) {
    console.error('Backend health proxy error:', err);
    res.status(503).json({ error: 'backend_unavailable', message: err.message });
  }
});

// Chat endpoint proxy to backend /api/chat
app.post('/api/pingo/chat', async (req: Request, res: Response) => {
  try {
    const backendUrl = getBackendUrl();
    const headers = await getBackendHeaders();

    // Security check: reject if client attempts to pass user_id or persona_key
    const payload: Record<string, any> = {
      message: req.body.message,
    };
    if (req.body.decision !== undefined) {
      payload.decision = req.body.decision;
    }

    const backendRes = await fetch(`${backendUrl}/api/chat`, {
      method: 'POST',
      headers,
      body: JSON.stringify(payload),
    });

    const data = await backendRes.json().catch(() => ({ status: backendRes.status }));
    res.status(backendRes.status).json(data);
  } catch (err: any) {
    console.error('Backend chat proxy error:', err);
    res.status(503).json({ error: 'backend_unavailable', message: err.message });
  }
});

// Plan endpoint proxy to backend /api/plan
app.post('/api/pingo/plan', async (req: Request, res: Response) => {
  try {
    const backendUrl = getBackendUrl();
    const headers = await getBackendHeaders();

    const payload = {
      message: req.body.message || 'Salvar plano na sessão',
      consent_enabled: req.body.consent_enabled === true,
      decision: req.body.decision,
    };

    const backendRes = await fetch(`${backendUrl}/api/plan`, {
      method: 'POST',
      headers,
      body: JSON.stringify(payload),
    });

    const data = await backendRes.json().catch(() => ({ status: backendRes.status }));
    res.status(backendRes.status).json(data);
  } catch (err: any) {
    console.error('Backend plan proxy error:', err);
    res.status(503).json({ error: 'backend_unavailable', message: err.message });
  }
});

// Supervisor endpoint proxy to backend /api/accompaniment/review
app.post('/api/pingo/supervisor', async (req: Request, res: Response) => {
  try {
    const backendUrl = getBackendUrl();
    const headers = await getBackendHeaders();

    const payload: Record<string, any> = {
      consent_enabled: req.body.consent_enabled === true,
    };
    if (req.body.plan_snapshot) {
      payload.plan_snapshot = req.body.plan_snapshot;
    }
    if (req.body.event) {
      payload.event = req.body.event;
    }

    const backendRes = await fetch(`${backendUrl}/api/accompaniment/review`, {
      method: 'POST',
      headers,
      body: JSON.stringify(payload),
    });

    const data = await backendRes.json().catch(() => ({ status: backendRes.status }));
    res.status(backendRes.status).json(data);
  } catch (err: any) {
    console.error('Backend supervisor proxy error:', err);
    res.status(503).json({ error: 'backend_unavailable', message: err.message });
  }
});

// Serve frontend static files
const distPath = path.resolve(__dirname, '../dist');
app.use(express.static(distPath));

// Fallback to index.html for SPA routing
app.get('*', (req: Request, res: Response) => {
  res.sendFile(path.join(distPath, 'index.html'));
});

app.listen(port, host, () => {
  console.log(`Pingo frontend server listening on http://${host}:${port}`);
});
