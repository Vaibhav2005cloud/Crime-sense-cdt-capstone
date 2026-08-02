# CrimeSense CDT v2 — React + FastAPI + CesiumJS Digital Twin

## What's new in this pass

- **Real authentication** — `/api/auth/login` issues a token against an in-memory user
  store (`admin/admin123`, `commissioner/commissioner123`, `analyst/analyst123` — see
  `USERS` in `main.py`). Every REST endpoint and the WebSocket now require it. Swap
  `USERS` for a real hashed-password table (passlib/bcrypt) before any real deployment
  — this demo store is intentionally simple to read and change.
- **Public landing page** (`/`) and **login page** (`/login`) — the app itself now lives
  at `/app`. The login/landing hero references a Canva-generated background image at
  `frontend/public/bg/command-center.jpg` — see `frontend/public/bg/README.md` for why
  that file isn't bundled and how to add it (one download, no code changes).
- **Cognitive Digital Twin replaces the CesiumJS globe.** Feedback was that a 3D globe
  for a 5-zone city was disorienting rather than useful. This is now a real Leaflet map
  centered on Chennai (real streets, real labels) with:
  - A **live heatmap** built from every real historical incident's lat/long/severity
    (`/api/incidents/points`), blended visually with the live WebSocket feed.
  - A **reasoning panel** — click any zone and `/api/zones/{zone}/reasoning` returns a
    real factor-by-factor breakdown of *why* that zone's risk score is what it is
    (historical severity, night-time share, lighting, density, unemployment index),
    plus the recommended patrol unit. This is the "cognitive" part: not just a number
    on the twin, but the reasoning behind it.
  - Toggleable layers for the heatmap, simulated patrol units, and simulated drones.
- **Plain-language descriptions** on every Command Center module card and nav item, so
  it's clear what each one actually does without needing to already know the domain.

This is the modern-stack rewrite: React + Vite + Tailwind CSS frontend, FastAPI backend,
a real CesiumJS 3D globe, ECharts dashboards. It sits alongside (does not replace) the
Flask version already delivered — keep both, they demonstrate different things.

**Tested end-to-end in the build sandbox**: every REST endpoint, the WebSocket live feed,
the real crime-type prediction pipeline, and `npm run build` all ran successfully before
this was packaged. That doesn't guarantee your exact machine has zero setup friction, but
the code itself is verified working, not just written.

## Stack actually used vs. requested

| You asked for | What's in this build | Why |
|---|---|---|
| React + Vite + Tailwind | ✅ exactly this | — |
| FastAPI backend | ✅ exactly this | — |
| CesiumJS 3D twin | ⚠️ Replaced with a 2D Leaflet Cognitive Digital Twin | The Cesium globe was reported as disorienting for a 5-zone city — a real Chennai street map with a live heatmap and click-to-reason panel tested as more understandable. Cesium/vite-plugin-cesium have been removed. |
| Mapbox GL | ⚠️ not wired in this pass | Mapbox requires a personal API key too; Cesium covers the "3D twin" requirement, so this was deprioritized — straightforward to add if you want a 2D layer alongside it |
| Apache ECharts | ✅ exactly this | — |
| PyTorch + XGBoost | ⚠️ XGBoost only (inside your original stacking classifier) | Your trained models are scikit-learn/XGBoost, not PyTorch. I didn't force a PyTorch wrapper around them just to check a box — that would be misleading in your documentation. If you want a genuine PyTorch component, a real next step is a small MLP or LSTM for the hourly incident time series (see `by_hour` in `/api/analytics/summary` as the training target) |
| PostgreSQL + PostGIS | ⚠️ SQLite/CSV stand-in | No live Postgres server in the build sandbox. The FastAPI code reads a flat CSV; swapping to real Postgres+PostGIS is a `pandas.read_sql` change, not an architecture change |
| WebSockets | ✅ exactly this | `/ws/live` streams every 3s |
| GitHub | not applicable here | you'll push this yourself |
| Kling AI / Leonardo AI / ElevenLabs / Suno / Runway | ❌ not available | none of these are connected tools in this environment |
| Canva AI | ✅ used | generated a cover/poster design earlier in this conversation |
| Figma | ❌ not available | not a connected tool |

## Running it

**Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**Frontend** (separate terminal):
```bash
cd frontend
npm install
npm run dev
```
Open http://localhost:5173 — the Vite dev server proxies `/api/*` to `localhost:8000` automatically.

**Production build:**
```bash
cd frontend && npm run build   # outputs frontend/dist
```

## Repository structure

```
.
├── frontend/           React + Vite + Tailwind UI (this README's main subject)
├── backend/             FastAPI API + trained models + historical dataset
├── streamlit_app/       One-click Streamlit Cloud demo (same models, same data)
├── .gitignore
└── README.md             you are here
```

## Streamlit Lite demo

Alongside the full React + FastAPI build, `streamlit_app/` is a single-file
Streamlit app that reuses the exact same trained models and historical
dataset, with no Node.js and no second server required. It's meant for a
one-click share link or a quick demo on a machine that doesn't have the
frontend/backend toolchain set up. See `streamlit_app/README.md` for what's
included and how it compares to the full build.

```bash
cd streamlit_app
pip install -r requirements.txt
streamlit run app.py
```

## Pushing this repo to GitHub

From the project root (the folder containing this README):

```bash
git init
git add .
git commit -m "CrimeSense CDT v2 — React/FastAPI build + Streamlit Lite demo"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo>.git
git push -u origin main
```

The `.gitignore` already excludes `node_modules/`, `dist/`, and Python
virtual envs, so the push stays small — the trained model files and CSV
dataset are small enough (a few MB total) to commit directly, no Git LFS
needed.

## Deploying live

### Streamlit Lite (`streamlit_app/`)
Push to GitHub, then on [share.streamlit.io](https://share.streamlit.io) create
an app pointing at `streamlit_app/app.py` on the `main` branch. No secrets
required.

### FastAPI backend (`backend/`) — e.g. on Render
1. [render.com](https://render.com) → **New** → **Web Service** → connect this
   GitHub repo.
2. **Root directory**: `backend`
3. **Build command**: `pip install -r requirements.txt`
4. **Start command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Deploy. Note the URL Render gives you, e.g.
   `https://crimesense-api.onrender.com`.
6. Once you also have your frontend's URL (next section), come back and add
   an environment variable on this Render service:
   `FRONTEND_ORIGIN=https://your-frontend-url.vercel.app` — this is read by
   `main.py`'s CORS config, so no code edit is needed.

### React frontend (`frontend/`) — e.g. on Vercel
1. [vercel.com](https://vercel.com) → **Add New** → **Project** → import this
   repo.
2. **Root directory**: `frontend`
3. **Build command**: `npm run build`, **output directory**: `dist` (Vercel
   usually detects this automatically as a Vite project).
4. Add an environment variable: `VITE_API_BASE_URL` = your Render backend URL
   from above (no trailing slash), e.g. `https://crimesense-api.onrender.com`.
   `frontend/.env.example` documents this.
5. Deploy. `src/api.js` and the WebSocket connection both read
   `VITE_API_BASE_URL` at build time — no rewrite rules needed, and this
   covers the live-feed WebSocket too, not just REST calls.
6. Copy the Vercel URL you're given and add it as `FRONTEND_ORIGIN` on the
   Render backend (step 6 above), then redeploy the backend so CORS allows it.

### Quick temporary share (no deployment)
To let someone reach your local `localhost:5173` right now without deploying
anything, run both servers locally as usual, then tunnel the frontend port
with [ngrok](https://ngrok.com): `ngrok http 5173`. Vite's local dev proxy
(`vite.config.js`) still forwards `/api` and `/ws` to your local backend
server-side, so this works without any code changes — but only while your
machine and both servers stay running.

## What's REAL vs SIMULATED (same discipline as the Flask build)

- **REAL**: crime-type prediction (your trained stacking classifier, through the real
  label-encoder/scaler/target-encoder pipeline), the Dynamic Risk Index (from the actual
  historical CSV), Resource Allocation (Hungarian algorithm via `scipy.optimize.linear_sum_assignment`),
  Explainable AI (native `feature_importances_`), all Analytics Center charts, the PDF report.
- **SIMULATED**: IoT telemetry, drone/patrol positions, the ~20 advanced module metrics on
  the Command Center grid, and the AI Copilot's text generation (template-based, though every
  number it cites comes from the real dataset).

Say this plainly in your documentation — it reads as engineering maturity, not a weakness.
