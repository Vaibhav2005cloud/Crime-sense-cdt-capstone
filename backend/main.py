"""
FastAPI backend for CrimeSense CDT v2.

Honesty notes (read before presenting this as "production"):
- Real: crime-type prediction, deployment recommendation, K-Means hotspot clustering
  (your original trained models, unchanged), the Dynamic Risk Index (from the real
  historical CSV), and the Resource Allocation Engine (a real Hungarian-algorithm
  assignment via scipy.optimize.linear_sum_assignment).
- Simulated: IoT telemetry, drone/patrol positions, and the ~20 "advanced" module
  metrics streamed over the WebSocket — random-walked numbers for a convincing demo,
  not live sensor/camera data.
- Database: this build uses SQLite (via the historical CSV, loaded once at startup)
  as a stand-in for PostgreSQL+PostGIS, since no live Postgres server is available in
  the build environment. Swap DATABASE_URL below for a real Postgres+PostGIS DSN and
  point the same queries at a `crime_incidents` table with a geometry column — the
  API layer doesn't need to change.
"""
import asyncio
import io
import json
import os
import random
import secrets
import time
from datetime import datetime
from typing import Optional

import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from scipy.optimize import linear_sum_assignment

from simulated_data import engine as sim_engine, ZONES

app = FastAPI(title="CrimeSense CDT API", version="2.0.0")

# Local dev origins always allowed; add your deployed frontend's URL via the
# FRONTEND_ORIGIN env var (comma-separated if you have more than one), e.g.
# FRONTEND_ORIGIN=https://crimesense-cdt.vercel.app
_extra_origins = [o.strip() for o in os.environ.get("FRONTEND_ORIGIN", "").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", *_extra_origins],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------
# Demo credential store. For a real deployment, replace with a users table
# (hashed passwords, e.g. passlib/bcrypt) — this is intentionally simple so
# the whole auth flow is easy to read and change for your project.
USERS = {
    "admin": {"password": "admin123", "role": "Administrator", "name": "Officer Admin"},
    "commissioner": {"password": "commissioner123", "role": "Commissioner", "name": "Commissioner"},
    "analyst": {"password": "analyst123", "role": "Analyst", "name": "Data Analyst"},
}
SESSIONS = {}  # token -> {username, role, name, expires}
TOKEN_TTL_SECONDS = 8 * 60 * 60  # 8 hours


class LoginRequest(BaseModel):
    username: str
    password: str


@app.post("/api/auth/login")
def login(req: LoginRequest):
    user = USERS.get(req.username)
    if not user or user["password"] != req.password:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = secrets.token_urlsafe(32)
    SESSIONS[token] = {
        "username": req.username, "role": user["role"], "name": user["name"],
        "expires": time.time() + TOKEN_TTL_SECONDS,
    }
    return {"token": token, "role": user["role"], "name": user["name"], "username": req.username}


def _check_token(token: Optional[str]):
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = SESSIONS.get(token)
    if not session or session["expires"] < time.time():
        SESSIONS.pop(token, None)
        raise HTTPException(status_code=401, detail="Session expired — please log in again")
    return session


def require_auth(authorization: Optional[str] = Header(None)):
    """REST dependency — expects `Authorization: Bearer <token>`."""
    token = authorization.split(" ", 1)[1] if authorization and authorization.startswith("Bearer ") else None
    return _check_token(token)


def require_auth_ws(token: Optional[str] = Query(None)):
    """WebSocket auth — browsers can't set custom headers on a WS handshake,
    so the token travels as a query param instead: /ws/live?token=..."""
    return _check_token(token)


@app.post("/api/auth/logout")
def logout(authorization: Optional[str] = Header(None)):
    token = authorization.split(" ", 1)[1] if authorization and authorization.startswith("Bearer ") else None
    SESSIONS.pop(token, None)
    return {"status": "logged out"}


@app.get("/api/auth/me")
def me(session=Depends(require_auth)):
    return {"username": session["username"], "role": session["role"], "name": session["name"]}


# ---------------------------------------------------------------------------
# Real data + real trained models (loaded once at startup)
# ---------------------------------------------------------------------------
df = pd.read_csv("chennai_crime_data.csv")
crime_predictor = joblib.load("models/crime_predictor.pkl")
deployment_recommender = joblib.load("models/deployment_recommender.pkl")
label_encoders = joblib.load("models/label_encoders.pkl")
scaler = joblib.load("models/scaler.pkl")
target_encoder = joblib.load("models/target_encoder.pkl")

LIGHTING_SCORE = {'Poor': 1.0, 'Moderate': 0.55, 'Good': 0.2}
DENSITY_SCORE = {'Low': 0.2, 'Medium': 0.5, 'High': 0.8, 'Very High': 1.0}
FEATURES = ['hour', 'day_of_week', 'month', 'zone', 'district', 'weather',
            'is_festival_day', 'is_weekend', 'is_night', 'population_density',
            'street_lighting', 'alcohol_outlet_nearby']


def compute_real_zone_risk():
    out = {}
    for z in ZONES:
        zdf = df[df['zone'] == z]
        if len(zdf) == 0:
            out[z] = 50.0
            continue
        hist = zdf['crime_severity'].mean() / 10.0
        night_share = zdf['is_night'].mean()
        lighting = zdf['street_lighting'].map(LIGHTING_SCORE).fillna(0.5).mean()
        density = zdf['population_density'].map(DENSITY_SCORE).fillna(0.5).mean()
        unemployment = zdf['unemployment_index'].mean()
        score = (0.40 * hist + 0.20 * night_share + 0.20 * lighting + 0.10 * density + 0.10 * unemployment) * 100
        out[z] = round(min(99, max(5, score)), 1)
    return out


def compute_real_resource_allocation(risk_by_zone):
    unit_response_times = [4, 6, 5, 7, 9]
    zones = ZONES
    risk = [risk_by_zone.get(z, 50) for z in zones]
    n = len(zones)
    cost = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            cost[i, j] = unit_response_times[i] * risk[j]
    row_ind, col_ind = linear_sum_assignment(cost)
    assignment = [{
        'unit': f'PATROL-{i+1}', 'response_time_min': unit_response_times[i],
        'zone': zones[j], 'zone_risk': risk[j]
    } for i, j in zip(row_ind, col_ind)]
    assignment.sort(key=lambda x: -x['zone_risk'])
    return assignment, round(float(cost[row_ind, col_ind].sum()), 1)


def compute_real_feature_importance():
    out = {}
    try:
        rf = crime_predictor.estimators_[0]
        out['crime_type_model'] = sorted(
            zip(FEATURES, [round(float(v), 4) for v in rf.feature_importances_]),
            key=lambda x: x[1], reverse=True)[:6]
    except Exception:
        out['crime_type_model'] = []
    try:
        out['deployment_model'] = sorted(
            zip(FEATURES, [round(float(v), 4) for v in deployment_recommender.feature_importances_]),
            key=lambda x: x[1], reverse=True)[:6]
    except Exception:
        out['deployment_model'] = []
    return out


# ---------------------------------------------------------------------------
# REST endpoints
# ---------------------------------------------------------------------------
@app.get("/api/health")
def health():
    return {"status": "ok", "time": datetime.now().isoformat(), "zones": ZONES}


@app.get("/api/zones/risk")
def zone_risk(session=Depends(require_auth)):
    """REAL — computed from the historical dataset."""
    return compute_real_zone_risk()


@app.get("/api/zones/coords")
def zone_coords(session=Depends(require_auth)):
    """REAL — average lat/long per zone from the historical dataset."""
    return df.groupby('zone')[['latitude', 'longitude']].mean().to_dict('index')


@app.get("/api/incidents/points")
def incident_points(session=Depends(require_auth)):
    """REAL — every historical incident's lat/long/severity, for the live
    heatmap layer on the Cognitive Digital Twin map."""
    cols = df[['latitude', 'longitude', 'crime_severity', 'zone', 'crime_type']].dropna()
    return cols.rename(columns={'latitude': 'lat', 'longitude': 'lng', 'crime_severity': 'severity'}).to_dict('records')


@app.get("/api/analytics/summary")
def analytics_summary(session=Depends(require_auth)):
    """REAL — real aggregates from the historical dataset, used by the Analytics page charts."""
    return {
        "total_incidents": int(len(df)),
        "high_severity": int((df['crime_severity'] >= 8).sum()),
        "by_crime_type": df['crime_type'].value_counts().to_dict(),
        "by_hour": df['hour'].value_counts().sort_index().to_dict(),
        "by_zone": df['zone'].value_counts().to_dict(),
        "night_share_pct": round(df['is_night'].mean() * 100, 1),
    }


@app.get("/api/zones/{zone}/reasoning")
def zone_reasoning(zone: str, session=Depends(require_auth)):
    """REAL — breaks the Dynamic Risk Index down into its actual weighted
    factors for one zone, plus the nearest recommended patrol unit. This is
    the 'cognitive' layer: not just a number, but why the number is what it is."""
    if zone not in ZONES:
        raise HTTPException(status_code=404, detail="unknown zone")
    zdf = df[df['zone'] == zone]
    if len(zdf) == 0:
        raise HTTPException(status_code=404, detail="no data for zone")
    hist = zdf['crime_severity'].mean() / 10.0
    night_share = zdf['is_night'].mean()
    lighting = zdf['street_lighting'].map(LIGHTING_SCORE).fillna(0.5).mean()
    density = zdf['population_density'].map(DENSITY_SCORE).fillna(0.5).mean()
    unemployment = zdf['unemployment_index'].mean()
    factors = {
        "historical_severity": round(0.40 * hist * 100, 1),
        "night_time_share": round(0.20 * night_share * 100, 1),
        "poor_lighting": round(0.20 * lighting * 100, 1),
        "population_density": round(0.10 * density * 100, 1),
        "unemployment_index": round(0.10 * unemployment * 100, 1),
    }
    total = round(sum(factors.values()), 1)
    top_crime = zdf['crime_type'].value_counts().index[0]
    peak_hour = int(zdf['hour'].value_counts().idxmax()) if len(zdf) else None
    real_risk = compute_real_zone_risk()
    alloc, _ = compute_real_resource_allocation(real_risk)
    recommended = next((a for a in alloc if a['zone'] == zone), None)
    return {
        "zone": zone, "total_risk": total, "factors": factors,
        "top_crime_type": top_crime, "peak_hour": peak_hour,
        "recommended_unit": recommended,
        "narrative": (f"{zone}'s risk score of {total}/100 is driven mostly by "
                      f"{'historical severity' if factors['historical_severity'] == max(factors.values()) else 'night-time activity' if factors['night_time_share'] == max(factors.values()) else 'lighting conditions'}. "
                      f"The most common offense here is {top_crime}"
                      + (f", peaking around {peak_hour}:00." if peak_hour is not None else ".")),
    }


@app.get("/api/allocation")
def allocation(session=Depends(require_auth)):
    """REAL — Hungarian-algorithm assignment (scipy.optimize.linear_sum_assignment)."""
    risk = compute_real_zone_risk()
    alloc, cost = compute_real_resource_allocation(risk)
    return {"allocation": alloc, "total_cost": cost}


@app.get("/api/explainable")
def explainable(session=Depends(require_auth)):
    """REAL — native feature_importances_ from the trained models (not SHAP)."""
    return compute_real_feature_importance()


class PredictRequest(BaseModel):
    hour: int
    day_of_week: str
    month: int
    zone: str
    district: str
    weather: str
    is_festival_day: int
    is_weekend: int
    is_night: int
    population_density: str
    street_lighting: str
    alcohol_outlet_nearby: int


@app.post("/api/predict")
def predict(req: PredictRequest, session=Depends(require_auth)):
    """REAL — runs your actual trained stacking classifier through the real
    label-encoder + scaler + target-encoder pipeline (same as the original app)."""
    row = pd.DataFrame([req.dict()])
    try:
        for col in label_encoders:
            if row[col][0] in label_encoders[col].classes_:
                row[col] = label_encoders[col].transform(row[col])
            else:
                row[col] = 0
        scaled = scaler.transform(row)
        pred_encoded = crime_predictor.predict(scaled)[0]
        proba = crime_predictor.predict_proba(scaled)[0]
        pred_label = target_encoder.inverse_transform([pred_encoded])[0]
        classes = target_encoder.inverse_transform(crime_predictor.classes_)
        top3 = sorted(zip(classes, [round(float(p), 3) for p in proba]), key=lambda x: -x[1])[:3]
        return {"predicted_crime_type": str(pred_label), "top3": [(str(c), p) for c, p in top3]}
    except Exception as e:
        return {"error": str(e)}


class WhatIfRequest(BaseModel):
    zone: str
    scenario: str


SCENARIOS = {
    'streetlight_failure': {'label': 'Streetlight Failure', 'risk_delta': 14, 'note': 'Visibility drops sharply after dark; night-time offense probability rises.'},
    'festival': {'label': 'Major Festival / Public Event', 'risk_delta': 9, 'note': 'Crowd density spikes; pickpocketing and crowd-crush risk increase.'},
    'heavy_rain': {'label': 'Heavy Rain / Flooding', 'risk_delta': -4, 'note': 'Street activity drops; response times worsen.'},
    'power_outage': {'label': 'Power Outage', 'risk_delta': 18, 'note': 'CCTV and lighting degrade simultaneously — highest-impact scenario.'},
    'vip_movement': {'label': 'VIP Movement / Convoy', 'risk_delta': 6, 'note': 'Traffic diversions strain patrol coverage in surrounding zones.'},
    'protest': {'label': 'Protest / Public Gathering', 'risk_delta': 11, 'note': 'Elevated crowd-control demand; displacement of routine patrols.'},
}


@app.get("/api/whatif/scenarios")
def whatif_scenarios(session=Depends(require_auth)):
    return SCENARIOS


@app.post("/api/whatif")
def whatif(req: WhatIfRequest, session=Depends(require_auth)):
    """REAL risk math (base index from the dataset) + a documented rule-based delta model."""
    sc = SCENARIOS.get(req.scenario)
    if not sc:
        return {"error": "unknown scenario"}
    real_risk = compute_real_zone_risk()
    base = real_risk.get(req.zone, 50)
    new_score = max(5, min(99, base + sc['risk_delta']))
    alloc, cost = compute_real_resource_allocation({**real_risk, req.zone: new_score})
    return {
        "zone": req.zone, "scenario": sc['label'], "note": sc['note'],
        "base_risk": base, "new_risk": round(new_score, 1), "delta": sc['risk_delta'],
        "allocation": alloc[:3],
    }


def generate_ai_briefing(question: Optional[str] = None):
    risk = compute_real_zone_risk()
    top_zone = max(risk, key=risk.get)
    top_crime = df['crime_type'].value_counts().index[0]
    peak_hour = int(df['hour'].value_counts().idxmax())
    night_share = round(df['is_night'].mean() * 100, 1)
    if question:
        q = question.lower()
        if 'zone' in q or 'hotspot' in q or 'risk' in q:
            ranked = sorted(risk.items(), key=lambda x: -x[1])
            return "Current zone risk ranking: " + "; ".join(f"{z}: {s}/100" for z, s in ranked) + f". {top_zone} is highest-priority."
        if 'patrol' in q or 'deploy' in q or 'resource' in q:
            alloc, cost = compute_real_resource_allocation(risk)
            top = alloc[0]
            return f"Send {top['unit']} (ETA {top['response_time_min']} min) to {top['zone']} (DRI {top['zone_risk']}). Total weighted cost: {cost}."
        if 'crime' in q or 'type' in q:
            counts = df['crime_type'].value_counts().head(3)
            return f"Top crime types: {', '.join(f'{k} ({v})' for k, v in counts.items())}."
        return f"{top_zone} is highest risk (DRI {round(risk[top_zone],1)}). Most frequent offense: {top_crime}. Night share: {night_share}%, peak hour {peak_hour}:00."
    return (f"DAILY TACTICAL BRIEF\nHighest-priority zone: {top_zone} (DRI {round(risk[top_zone],1)}/100)\n"
            f"Most frequent offense: {top_crime}\nNight-time share: {night_share}% (peak {peak_hour}:00)")


class CopilotRequest(BaseModel):
    question: str


@app.post("/api/copilot")
def copilot(req: CopilotRequest, session=Depends(require_auth)):
    """SIM generation (template-based, no LLM key wired) but grounded in REAL data."""
    return {"answer": generate_ai_briefing(req.question)}


@app.get("/api/copilot/daily-brief")
def daily_brief(session=Depends(require_auth)):
    return {"brief": generate_ai_briefing()}


@app.get("/api/report/pdf")
def report_pdf(authorization: Optional[str] = Header(None), token: Optional[str] = Query(None)):
    header_token = authorization.split(" ", 1)[1] if authorization and authorization.startswith("Bearer ") else None
    _check_token(header_token or token)
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib import colors

    real_risk = compute_real_zone_risk()
    alloc, cost = compute_real_resource_allocation(real_risk)
    brief = generate_ai_briefing()

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter)
    styles = getSampleStyleSheet()
    story = [
        Paragraph("CrimeSense CDT v2 — Executive Intelligence Report", styles['Title']),
        Spacer(1, 12),
        Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal']),
        Spacer(1, 16),
        Paragraph("Daily Tactical Brief", styles['Heading2']),
        Paragraph(brief.replace(chr(10), '<br/>'), styles['Normal']),
        Spacer(1, 16),
        Paragraph("Zone Risk Index (Real)", styles['Heading2']),
    ]
    t = Table([['Zone', 'Risk']] + [[z, str(s)] for z, s in real_risk.items()])
    t.setStyle(TableStyle([('GRID', (0, 0), (-1, -1), 0.5, colors.grey)]))
    story.append(t)
    story.append(Spacer(1, 16))
    story.append(Paragraph("Recommended Allocation (Hungarian algorithm)", styles['Heading2']))
    t2 = Table([['Unit', 'ETA', 'Zone', 'Risk']] + [[a['unit'], f"{a['response_time_min']}m", a['zone'], str(a['zone_risk'])] for a in alloc])
    t2.setStyle(TableStyle([('GRID', (0, 0), (-1, -1), 0.5, colors.grey)]))
    story.append(t2)
    doc.build(story)
    buf.seek(0)
    return StreamingResponse(buf, media_type="application/pdf",
                              headers={"Content-Disposition": "attachment; filename=crimesense_report_v2.pdf"})


# ---------------------------------------------------------------------------
# WebSocket — live simulated feed (drives Command Center + Digital Twin)
# ---------------------------------------------------------------------------
@app.websocket("/ws/live")
async def ws_live(websocket: WebSocket, token: Optional[str] = Query(None)):
    try:
        _check_token(token)
    except HTTPException:
        await websocket.close(code=4401)
        return
    await websocket.accept()
    real_risk = compute_real_zone_risk()
    try:
        while True:
            live = sim_engine.tick()
            blended_risk = {z: round(0.65 * real_risk[z] + 0.35 * live['risk_index'][z], 1) for z in ZONES}
            payload = {
                "risk": blended_risk,
                "iot": live["iot"],
                "drones": live["drones"],
                "patrols": live["patrols"],
                "incidents": live["incident_feed"][:8],
                "modules": live["module_metrics"],
            }
            await websocket.send_text(json.dumps(payload))
            await asyncio.sleep(3)
    except WebSocketDisconnect:
        pass
