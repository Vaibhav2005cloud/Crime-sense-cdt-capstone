// In production, set VITE_API_BASE_URL (e.g. on Vercel/Netlify) to your
// deployed backend's URL, such as https://crimesense-api.onrender.com.
// Left unset, this falls back to the existing behavior: relative /api
// (proxied by Vite in local dev).
const API_ORIGIN = import.meta.env.VITE_API_BASE_URL || '';
const BASE = `${API_ORIGIN}/api`;

function authHeaders() {
  const token = localStorage.getItem('cdt_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function j(res) {
  if (res.status === 401) {
    localStorage.removeItem('cdt_token');
    localStorage.removeItem('cdt_user');
    window.location.href = '/login';
    throw new Error('Session expired');
  }
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return res.json();
}

export const api = {
  login: (username, password) => fetch(`${BASE}/auth/login`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  }),
  logout: () => fetch(`${BASE}/auth/logout`, { method: 'POST', headers: authHeaders() }),
  me: () => fetch(`${BASE}/auth/me`, { headers: authHeaders() }).then(j),

  health: () => fetch(`${BASE}/health`).then(j),
  zoneRisk: () => fetch(`${BASE}/zones/risk`, { headers: authHeaders() }).then(j),
  zoneCoords: () => fetch(`${BASE}/zones/coords`, { headers: authHeaders() }).then(j),
  incidentPoints: () => fetch(`${BASE}/incidents/points`, { headers: authHeaders() }).then(j),
  zoneReasoning: (zone) => fetch(`${BASE}/zones/${encodeURIComponent(zone)}/reasoning`, { headers: authHeaders() }).then(j),
  analyticsSummary: () => fetch(`${BASE}/analytics/summary`, { headers: authHeaders() }).then(j),
  allocation: () => fetch(`${BASE}/allocation`, { headers: authHeaders() }).then(j),
  explainable: () => fetch(`${BASE}/explainable`, { headers: authHeaders() }).then(j),
  whatifScenarios: () => fetch(`${BASE}/whatif/scenarios`, { headers: authHeaders() }).then(j),
  whatif: (zone, scenario) => fetch(`${BASE}/whatif`, {
    method: 'POST', headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify({ zone, scenario }),
  }).then(j),
  copilot: (question) => fetch(`${BASE}/copilot`, {
    method: 'POST', headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify({ question }),
  }).then(j),
  dailyBrief: () => fetch(`${BASE}/copilot/daily-brief`, { headers: authHeaders() }).then(j),
  predict: (payload) => fetch(`${BASE}/predict`, {
    method: 'POST', headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify(payload),
  }).then(j),
  // Plain <a href> downloads can't attach an Authorization header, so the
  // token travels as a query param here — the backend accepts either.
  reportPdfUrl: () => `${BASE}/report/pdf?token=${encodeURIComponent(localStorage.getItem('cdt_token') || '')}`,
};

export function connectLiveFeed(onMessage, onClose) {
  const isDev = import.meta.env.DEV;
  let proto = window.location.protocol === 'https:' ? 'wss' : 'ws';
  let host = isDev ? '127.0.0.1:8000' : window.location.host;
  if (API_ORIGIN) {
    const u = new URL(API_ORIGIN);
    proto = u.protocol === 'https:' ? 'wss' : 'ws';
    host = u.host;
  }
  const token = localStorage.getItem('cdt_token') || '';
  const ws = new WebSocket(`${proto}://${host}/ws/live?token=${encodeURIComponent(token)}`);
  ws.onmessage = (evt) => onMessage(JSON.parse(evt.data));
  if (onClose) ws.onclose = onClose;
  return ws;
}
