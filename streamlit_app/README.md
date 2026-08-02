# CrimeSense CDT — Streamlit Lite

A single-file demo that runs the same trained models and the same
historical dataset as the main `frontend/` + `backend/` build, without
needing Node.js or two separate servers. Good for a quick share link,
a viva demo on someone else's laptop, or a GitHub README preview link.

## What this is (and isn't)

| | React + FastAPI (`../frontend`, `../backend`) | Streamlit Lite (this folder) |
|---|---|---|
| UI | Custom React/Tailwind, Leaflet twin, login | Streamlit components + injected CSS matching the same dark/neon color palette |
| Live IoT/WebSocket feed | ✅ simulated, streamed every 3s | ❌ not included |
| Authentication | ✅ token-based login | ✅ same demo credentials, session-based login |
| Crime-type prediction | ✅ real trained pipeline | ✅ same real trained pipeline |
| AI Copilot | ✅ real-data-grounded Q&A | ✅ same logic, ported directly |
| Dynamic Risk Index | ✅ real, from historical CSV | ✅ same computation, reused |
| Resource allocation (Hungarian algorithm) | ✅ real | ✅ same computation, reused |
| K-Means hotspot clustering | trained but not wired into the API | ✅ visualized here |
| Deployment | needs a host for the API + a static host for the frontend | ✅ one click on Streamlit Community Cloud |

## Login

Same demo accounts as the FastAPI backend's `USERS` store:

| Username | Password | Role |
|---|---|---|
| `admin` | `admin123` | Administrator |
| `commissioner` | `commissioner123` | Commissioner |
| `analyst` | `analyst123` | Analyst |

This is a simple `st.session_state` gate for demo purposes — replace with
real hashed passwords (e.g. `streamlit-authenticator`, or `st.secrets` +
passlib/bcrypt) before any real deployment.

## Run locally

```bash
cd streamlit_app
pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Streamlit Community Cloud

1. Push this repo to GitHub (see the root `README.md`).
2. Go to [share.streamlit.io](https://share.streamlit.io) → **Create app**.
3. Pick this repo, branch `main`, and set the main file path to:
   ```
   streamlit_app/app.py
   ```
4. Deploy. No secrets or environment variables are required — everything
   the app needs (`chennai_crime_data.csv`, the `models/` folder) is
   already inside this folder.

## Background images (optional, matches the React build)

Drop the same 3 Canva-generated images used in `frontend/public/bg/` into
`streamlit_app/assets/` with these exact filenames:

| Filename | Used on |
|---|---|
| `command-center.jpg` | Login screen + Overview page hero |
| `copilot-bg.jpg` | AI Copilot page banner |
| `heatmap-bg.jpg` | Zone Risk & Reasoning page banner |

The app works fine without them (falls back to the gradient-only look) —
this is purely cosmetic, not required to run.

## Files

- `app.py` — the entire app (data loading, real risk/allocation/prediction
  logic, and every page).
- `chennai_crime_data.csv` — the same historical dataset used by the backend.
- `models/*.pkl` — the same trained scikit-learn/XGBoost/LightGBM artifacts
  used by the backend (crime-type classifier, deployment recommender,
  label encoders, scaler, target encoder, K-Means hotspot model).
- `requirements.txt` — pinned to what Streamlit Cloud needs to build this app.

Both this repo copy and the one in `../backend/` come from the exact same
training run — the predictions here match the FastAPI backend's, since it's
the same pickle files.
