"""
CrimeSense CDT — Streamlit Lite
================================
A single-file, one-click-deployable companion to the React + FastAPI build
in ../frontend and ../backend. It reuses the SAME trained models and the
SAME historical dataset, and reimplements the same "real vs simulated"
computations (Dynamic Risk Index, Hungarian-algorithm resource allocation,
feature importance, crime-type prediction) directly in Python — no
separate backend process required, so it deploys as-is on Streamlit
Community Cloud.

Honesty notes (kept consistent with the main build):
- REAL: crime-type prediction (trained stacking classifier through the real
  label-encoder / scaler / target-encoder pipeline), the Dynamic Risk Index
  (from the real historical CSV), Resource Allocation (Hungarian algorithm
  via scipy.optimize.linear_sum_assignment), Explainable AI
  (native feature_importances_), K-Means hotspot clustering (trained model),
  and every Analytics chart.
- SIMULATED: nothing in this lite build claims to be live sensor/camera
  data — there is no WebSocket/IoT layer here, only the real, static
  historical dataset and the real trained models.

Run locally:
    pip install -r requirements.txt
    streamlit run app.py

Deploy on Streamlit Community Cloud:
    Point the app at this file's path: streamlit_app/app.py
"""
import base64
import io
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from scipy.optimize import linear_sum_assignment

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="CrimeSense CDT — Streamlit Lite",
    page_icon="🛰️",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Theme — matches the React frontend's palette (frontend/src/index.css):
# void #070912, panel #121729, neon-blue #3D8BFD, neon-purple #8B5CF6,
# text-hi #EAF0FC, text-mid #AEB8D4. Streamlit can't be pixel-identical to a
# hand-built Tailwind UI (different rendering engine, no custom Leaflet/CSS
# animations), but this gets the color language, fonts, and card style close.
# ---------------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Inter:wght@400;500;600&display=swap');

.stApp {
    background:
        radial-gradient(circle at 15% 0%, rgba(61,139,253,0.10), transparent 45%),
        radial-gradient(circle at 90% 15%, rgba(139,92,246,0.10), transparent 40%),
        #070912;
    color: #EAF0FC;
    font-family: 'Inter', sans-serif;
}
section[data-testid="stSidebar"] {
    background: #121729;
    border-right: 1px solid rgba(120,150,255,0.14);
}
h1, h2, h3 {
    font-family: 'Space Grotesk', sans-serif !important;
    color: #EAF0FC !important;
}
p, span, label, .stMarkdown, .stCaption {
    color: #AEB8D4;
}
div[data-testid="stMetric"], div[data-testid="stExpander"], .stDataFrame, .stAlert {
    background: rgba(20, 26, 44, 0.62) !important;
    border: 1px solid rgba(120,150,255,0.14) !important;
    border-radius: 18px !important;
    backdrop-filter: blur(16px);
}
div[data-testid="stMetricValue"] { color: #3D8BFD !important; }
.stButton > button, .stFormSubmitButton > button {
    background: #3D8BFD;
    color: #070912;
    border: none;
    border-radius: 10px;
    font-weight: 600;
}
.stButton > button:hover, .stFormSubmitButton > button:hover {
    background: #8B5CF6;
    color: #EAF0FC;
}
.cdt-hero {
    text-align: center;
    padding: 2.5rem 1rem 2rem 1rem;
    border-radius: 20px;
    background:
        radial-gradient(circle at 25% 15%, rgba(61,139,253,0.25), transparent 45%),
        radial-gradient(circle at 80% 75%, rgba(139,92,246,0.25), transparent 45%),
        linear-gradient(rgba(7,9,18,0.55), rgba(7,9,18,0.85)), #0c1020;
    margin-bottom: 1.5rem;
}
.cdt-hero .badge {
    display: inline-block; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 3px;
    color: #3D8BFD; border: 1px solid rgba(61,139,253,0.3); background: rgba(61,139,253,0.1);
    border-radius: 999px; padding: 4px 16px; margin-bottom: 1rem;
}
.cdt-hero h1 { font-size: 2.6rem; margin-bottom: 0.75rem; }
.cdt-hero .accent { color: #3D8BFD; }
.cdt-hero p { max-width: 640px; margin: 0 auto; font-size: 1.05rem; }
.cdt-banner {
    height: 110px;
    border-radius: 16px;
    margin-bottom: 1.25rem;
    background-size: cover;
    background-position: center;
    border: 1px solid rgba(120,150,255,0.14);
}
div[class*="st-key-"] {
    background: rgba(20, 26, 44, 0.65) !important;
    border: 1px solid rgba(120,150,255,0.18) !important;
    border-radius: 16px !important;
    padding: 1.1rem 1.3rem !important;
    backdrop-filter: blur(14px);
}
.cdt-stat-num { font-family: 'Space Grotesk', sans-serif; font-size: 1.9rem; font-weight: 700; color: #3D8BFD; }
.cdt-stat-label { font-size: 0.8rem; color: #AEB8D4; }
.cdt-feat-icon { font-size: 1.4rem; }
.cdt-feat-title { font-weight: 600; margin: 0.35rem 0 0.25rem 0; }
.cdt-feat-desc { font-size: 0.85rem; color: #AEB8D4; }
</style>
""", unsafe_allow_html=True)

BASE_DIR = Path(__file__).parent
ASSETS_DIR = BASE_DIR / "assets"
ZONES = ["North", "Central", "West", "East", "South"]
LIGHTING_SCORE = {"Poor": 1.0, "Moderate": 0.55, "Good": 0.2}
DENSITY_SCORE = {"Low": 0.2, "Medium": 0.5, "High": 0.8, "Very High": 1.0}
FEATURES = [
    "hour", "day_of_week", "month", "zone", "district", "weather",
    "is_festival_day", "is_weekend", "is_night", "population_density",
    "street_lighting", "alcohol_outlet_nearby",
]


def bg_image_css(filename: str, overlay: str) -> str:
    """Return a CSS background-image data URI for a local asset, layered under
    a dark overlay gradient so text stays legible. Same 3 Canva-generated
    images as the React frontend (assets/command-center.jpg, copilot-bg.jpg,
    heatmap-bg.jpg) — drop them in streamlit_app/assets/ to activate.
    Falls back to just the overlay/gradient (no crash) if the file isn't
    there yet, matching how the React build behaves before those images
    are added.
    """
    path = ASSETS_DIR / filename
    if not path.exists():
        return overlay
    b64 = base64.b64encode(path.read_bytes()).decode()
    return f"{overlay}, url('data:image/jpeg;base64,{b64}')"


# ---------------------------------------------------------------------------
# Cached loaders — data and models load once per session, not per rerun
# ---------------------------------------------------------------------------
@st.cache_data
def load_data() -> pd.DataFrame:
    return pd.read_csv(BASE_DIR / "chennai_crime_data.csv")


@st.cache_resource
def load_models():
    m = BASE_DIR / "models"
    return {
        "crime_predictor": joblib.load(m / "crime_predictor.pkl"),
        "deployment_recommender": joblib.load(m / "deployment_recommender.pkl"),
        "label_encoders": joblib.load(m / "label_encoders.pkl"),
        "scaler": joblib.load(m / "scaler.pkl"),
        "target_encoder": joblib.load(m / "target_encoder.pkl"),
        "kmeans": joblib.load(m / "kmeans_hotspots.pkl"),
    }


df = load_data()
models = load_models()


# ---------------------------------------------------------------------------
# Authentication — same demo credentials as backend/main.py's USERS dict,
# so both builds behave like one consistent system.
# For a real deployment, replace this with real hashed passwords
# (e.g. via streamlit-authenticator or st.secrets + passlib/bcrypt).
# ---------------------------------------------------------------------------
USERS = {
    "admin": {"password": "admin123", "role": "Administrator", "name": "Officer Admin"},
    "commissioner": {"password": "commissioner123", "role": "Commissioner", "name": "Commissioner"},
    "analyst": {"password": "analyst123", "role": "Analyst", "name": "Data Analyst"},
}


def login_gate():
    if "auth_user" not in st.session_state:
        st.session_state.auth_user = None

    if st.session_state.auth_user:
        return True

    hero_bg = bg_image_css(
        "login-bg.jpg",
        "radial-gradient(circle at 20% 20%, rgba(61,139,253,0.18), transparent 45%),"
        "radial-gradient(circle at 80% 75%, rgba(139,92,246,0.18), transparent 45%),"
        "linear-gradient(rgba(7,9,18,0.55), rgba(7,9,18,0.75))",
    )
    # full-bleed page background (image shows through, same as React's Login.jsx)
    st.markdown(f"""
    <style>
    .stApp {{
        background-image: {hero_bg} !important;
        background-size: cover !important;
        background-position: center !important;
        background-attachment: fixed !important;
    }}
    div[data-testid="stForm"] {{
        background: rgba(18, 23, 41, 0.82) !important;
        border: 1px solid rgba(120,150,255,0.2) !important;
        border-radius: 20px !important;
        padding: 2rem 2rem 1rem 2rem !important;
        backdrop-filter: blur(18px);
        max-width: 420px;
        margin: 2rem auto 0 auto;
    }}
    div[data-testid="stTextInput"] input {{
        background: rgba(255,255,255,0.05) !important;
        border: 1px solid rgba(255,255,255,0.12) !important;
        border-radius: 8px !important;
        color: #EAF0FC !important;
    }}
    .cdt-login-logo {{
        width: 64px; height: 64px; border-radius: 50%; margin: 0 auto 0.75rem auto;
        background: radial-gradient(circle at 40% 35%, #3D8BFD, #0c1020 70%);
        box-shadow: 0 0 0 1px rgba(61,139,253,0.35), 0 0 30px rgba(61,139,253,0.35);
    }}
    </style>
    <div style="max-width:420px; margin: 3rem auto 0 auto; text-align:center;">
        <div class="cdt-login-logo"></div>
        <h1 style="font-size:1.4rem; margin-bottom:0.1rem;">CrimeSense CDT</h1>
        <div style="font-size:0.7rem; letter-spacing:2px; color:#AEB8D4; text-transform:uppercase;">
            Smart City Digital Twin &middot; Chennai
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.form("login_form"):
        username = st.text_input("Officer ID")
        password = st.text_input("Secure Key", type="password")
        submitted = st.form_submit_button("Authenticate", type="primary")
        st.caption(
            "Demo credentials: admin/admin123 (Administrator) · "
            "commissioner/commissioner123 (Commissioner) · analyst/analyst123 (Analyst)"
        )
    if submitted:
        user = USERS.get(username)
        if user and user["password"] == password:
            st.session_state.auth_user = {"username": username, "role": user["role"], "name": user["name"]}
            st.rerun()
        else:
            st.error("Invalid Officer ID or Secure Key.")
    return False


if not login_gate():
    st.stop()


# ---------------------------------------------------------------------------
# Real computations — same logic as backend/main.py, reused here directly
# ---------------------------------------------------------------------------
def compute_real_zone_risk() -> dict:
    out = {}
    for z in ZONES:
        zdf = df[df["zone"] == z]
        if len(zdf) == 0:
            out[z] = 50.0
            continue
        hist = zdf["crime_severity"].mean() / 10.0
        night_share = zdf["is_night"].mean()
        lighting = zdf["street_lighting"].map(LIGHTING_SCORE).fillna(0.5).mean()
        density = zdf["population_density"].map(DENSITY_SCORE).fillna(0.5).mean()
        unemployment = zdf["unemployment_index"].mean()
        score = (0.40 * hist + 0.20 * night_share + 0.20 * lighting
                 + 0.10 * density + 0.10 * unemployment) * 100
        out[z] = round(min(99, max(5, score)), 1)
    return out


def compute_real_resource_allocation(risk_by_zone: dict):
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
        "unit": f"PATROL-{i + 1}", "response_time_min": unit_response_times[i],
        "zone": zones[j], "zone_risk": risk[j],
    } for i, j in zip(row_ind, col_ind)]
    assignment.sort(key=lambda x: -x["zone_risk"])
    return assignment, round(float(cost[row_ind, col_ind].sum()), 1)


def compute_real_feature_importance() -> dict:
    out = {}
    try:
        rf = models["crime_predictor"].estimators_[0]
        out["crime_type_model"] = sorted(
            zip(FEATURES, [round(float(v), 4) for v in rf.feature_importances_]),
            key=lambda x: x[1], reverse=True)[:6]
    except Exception:
        out["crime_type_model"] = []
    try:
        out["deployment_model"] = sorted(
            zip(FEATURES, [round(float(v), 4) for v in models["deployment_recommender"].feature_importances_]),
            key=lambda x: x[1], reverse=True)[:6]
    except Exception:
        out["deployment_model"] = []
    return out


def zone_reasoning(zone: str) -> dict:
    zdf = df[df["zone"] == zone]
    hist = zdf["crime_severity"].mean() / 10.0
    night_share = zdf["is_night"].mean()
    lighting = zdf["street_lighting"].map(LIGHTING_SCORE).fillna(0.5).mean()
    density = zdf["population_density"].map(DENSITY_SCORE).fillna(0.5).mean()
    unemployment = zdf["unemployment_index"].mean()
    factors = {
        "Historical severity": round(0.40 * hist * 100, 1),
        "Night-time share": round(0.20 * night_share * 100, 1),
        "Poor lighting": round(0.20 * lighting * 100, 1),
        "Population density": round(0.10 * density * 100, 1),
        "Unemployment index": round(0.10 * unemployment * 100, 1),
    }
    total = round(sum(factors.values()), 1)
    top_crime = zdf["crime_type"].value_counts().index[0]
    peak_hour = int(zdf["hour"].value_counts().idxmax()) if len(zdf) else None
    real_risk = compute_real_zone_risk()
    alloc, _ = compute_real_resource_allocation(real_risk)
    recommended = next((a for a in alloc if a["zone"] == zone), None)
    driver = max(factors, key=factors.get)
    narrative = (f"{zone}'s risk score of {total}/100 is driven mostly by {driver.lower()}. "
                 f"The most common offense here is {top_crime}"
                 + (f", peaking around {peak_hour}:00." if peak_hour is not None else "."))
    return {"factors": factors, "total": total, "top_crime": top_crime,
            "peak_hour": peak_hour, "recommended": recommended, "narrative": narrative}


def predict_crime_type(inputs: dict):
    row = pd.DataFrame([inputs])
    for col in models["label_encoders"]:
        if row[col][0] in models["label_encoders"][col].classes_:
            row[col] = models["label_encoders"][col].transform(row[col])
        else:
            row[col] = 0
    scaled = models["scaler"].transform(row)
    pred_encoded = models["crime_predictor"].predict(scaled)[0]
    proba = models["crime_predictor"].predict_proba(scaled)[0]
    pred_label = models["target_encoder"].inverse_transform([pred_encoded])[0]
    classes = models["target_encoder"].inverse_transform(models["crime_predictor"].classes_)
    top3 = sorted(zip(classes, [round(float(p), 3) for p in proba]), key=lambda x: -x[1])[:3]
    return str(pred_label), top3


def build_pdf_report() -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    real_risk = compute_real_zone_risk()
    alloc, cost = compute_real_resource_allocation(real_risk)
    top_zone = max(real_risk, key=real_risk.get)
    top_crime = df["crime_type"].value_counts().index[0]

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter)
    styles = getSampleStyleSheet()
    story = [
        Paragraph("CrimeSense CDT — Executive Intelligence Report (Streamlit Lite)", styles["Title"]),
        Spacer(1, 12),
        Paragraph(f"Highest-priority zone: {top_zone} (DRI {real_risk[top_zone]}/100). "
                  f"Most frequent offense city-wide: {top_crime}.", styles["Normal"]),
        Spacer(1, 16),
        Paragraph("Zone Risk Index (Real)", styles["Heading2"]),
    ]
    t = Table([["Zone", "Risk"]] + [[z, str(s)] for z, s in real_risk.items()])
    t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.grey)]))
    story.append(t)
    story.append(Spacer(1, 16))
    story.append(Paragraph("Recommended Allocation (Hungarian algorithm)", styles["Heading2"]))
    t2 = Table([["Unit", "ETA", "Zone", "Risk"]]
               + [[a["unit"], f"{a['response_time_min']}m", a["zone"], str(a["zone_risk"])] for a in alloc])
    t2.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.grey)]))
    story.append(t2)
    doc.build(story)
    buf.seek(0)
    return buf.getvalue()


def generate_ai_briefing(question: str = None) -> str:
    """SIM text generation (template-based, no LLM key wired) but every number
    it cites is REAL — same approach as backend/main.py's copilot endpoint."""
    risk = compute_real_zone_risk()
    top_zone = max(risk, key=risk.get)
    top_crime = df["crime_type"].value_counts().index[0]
    peak_hour = int(df["hour"].value_counts().idxmax())
    night_share = round(df["is_night"].mean() * 100, 1)
    if question:
        q = question.lower()
        if "zone" in q or "hotspot" in q or "risk" in q:
            ranked = sorted(risk.items(), key=lambda x: -x[1])
            return ("Current zone risk ranking: " + "; ".join(f"{z}: {s}/100" for z, s in ranked)
                    + f". {top_zone} is highest-priority.")
        if "patrol" in q or "deploy" in q or "resource" in q:
            alloc, cost = compute_real_resource_allocation(risk)
            top = alloc[0]
            return (f"Send {top['unit']} (ETA {top['response_time_min']} min) to {top['zone']} "
                    f"(DRI {top['zone_risk']}). Total weighted cost: {cost}.")
        if "crime" in q or "type" in q:
            counts = df["crime_type"].value_counts().head(3)
            return f"Top crime types: {', '.join(f'{k} ({v})' for k, v in counts.items())}."
        return (f"{top_zone} is highest risk (DRI {round(risk[top_zone], 1)}). Most frequent offense: "
                f"{top_crime}. Night share: {night_share}%, peak hour {peak_hour}:00.")
    return (f"DAILY TACTICAL BRIEF\nHighest-priority zone: {top_zone} (DRI {round(risk[top_zone], 1)}/100)\n"
            f"Most frequent offense: {top_crime}\nNight-time share: {night_share}% (peak {peak_hour}:00)")


# ---------------------------------------------------------------------------
# Sidebar navigation
# ---------------------------------------------------------------------------
st.sidebar.title("🛰️ CrimeSense CDT")
st.sidebar.caption("Streamlit Lite — Chennai crime hotspot digital twin")
st.sidebar.success(f"Signed in as {st.session_state.auth_user['name']} ({st.session_state.auth_user['role']})")
if st.sidebar.button("Log out"):
    st.session_state.auth_user = None
    st.rerun()
page = st.sidebar.radio("Go to", [
    "Overview", "Zone Risk & Reasoning", "Crime Type Predictor",
    "Hotspot Clusters (K-Means)", "Resource Allocation", "AI Copilot",
    "Analytics", "Download Report",
])
with st.sidebar.expander("What's real vs simulated?"):
    st.write(
        "**Real**: crime-type prediction, Dynamic Risk Index, resource allocation, "
        "feature importance, hotspot clustering, all charts — all computed from the "
        "actual historical dataset and the trained models.\n\n"
        "**Not included in this lite build**: the live IoT/WebSocket feed and "
        "authentication from the full React + FastAPI version — see the `frontend/` "
        "and `backend/` folders in this repo for that build."
    )

real_risk = compute_real_zone_risk()

# ---------------------------------------------------------------------------
# Overview
# ---------------------------------------------------------------------------
if page == "Overview":
    hero_bg = bg_image_css(
        "command-center.jpg",
        "radial-gradient(circle at 25% 15%, rgba(61,139,253,0.25), transparent 45%),"
        "radial-gradient(circle at 80% 75%, rgba(139,92,246,0.25), transparent 45%),"
        "linear-gradient(rgba(7,9,18,0.6), rgba(7,9,18,0.88))",
    )
    st.markdown(f"""
    <div class="cdt-hero" style="background-image: {hero_bg}; background-size: cover; background-position: center;">
        <span class="badge">Final-Year AI &amp; Data Science Capstone &middot; Chennai Metro</span>
        <h1>CrimeSense <span class="accent">CDT</span></h1>
        <p>A cognitive digital twin for crime hotspot detection &amp; intelligent security
        management — real machine learning, real optimization, and a live reasoning
        layer over the city itself.</p>
    </div>
    """, unsafe_allow_html=True)

    hc1, hc2, hc3 = st.columns(3)
    with hc1, st.container(border=True, key="stat_zones"):
        st.markdown('<div class="cdt-stat-num">%d</div><div class="cdt-stat-label">Zones modeled</div>' % len(ZONES), unsafe_allow_html=True)
    with hc2, st.container(border=True, key="stat_incidents"):
        st.markdown(f'<div class="cdt-stat-num">{len(df):,}</div><div class="cdt-stat-label">Historical incidents</div>', unsafe_allow_html=True)
    with hc3, st.container(border=True, key="stat_pages"):
        st.markdown('<div class="cdt-stat-num">7</div><div class="cdt-stat-label">Dashboard pages</div>', unsafe_allow_html=True)

    st.write("")
    feat_cols = st.columns(3)
    features = [
        ("🌐", "Cognitive Digital Twin", "A reasoning-enabled map of Chennai that explains why a zone is risky."),
        ("🔥", "Real Risk Heatmap", "Historical incident density mapped per zone from the real dataset."),
        ("🧠", "Real ML Forecasting", "A genuinely trained stacking classifier predicts crime type."),
        ("⚙️", "Optimized Patrol Allocation", "A real Hungarian-algorithm solver assigns patrol units to zones."),
        ("💬", "AI Copilot", "Ask plain-English questions about zones, patrols, or crime types."),
        ("📄", "One-Click Reporting", "Generate an executive PDF brief instantly."),
    ]
    for i, (col, (icon, title, desc)) in enumerate(zip(feat_cols * 2, features)):
        with col, st.container(border=True, key=f"feat_{i}"):
            st.markdown(
                f'<div class="cdt-feat-icon">{icon}</div>'
                f'<div class="cdt-feat-title">{title}</div>'
                f'<div class="cdt-feat-desc">{desc}</div>',
                unsafe_allow_html=True,
            )

    st.divider()
    st.subheader("Command Center")
    c1, c2, c3, c4 = st.columns(4)
    with c1, st.container(border=True, key="cc_zones"):
        st.metric("Zones modeled", len(ZONES))
    with c2, st.container(border=True, key="cc_incidents"):
        st.metric("Historical incidents", f"{len(df):,}")
    with c3, st.container(border=True, key="cc_severe"):
        st.metric("High-severity incidents", int((df["crime_severity"] >= 8).sum()))
    with c4, st.container(border=True, key="cc_night"):
        st.metric("Night-time share", f"{round(df['is_night'].mean() * 100, 1)}%")

    st.write("")
    with st.container(border=True, key="cc_chart"):
        st.subheader("Dynamic Risk Index by zone")
        risk_df = pd.DataFrame({"zone": list(real_risk.keys()), "risk": list(real_risk.values())})
        fig = px.bar(risk_df.sort_values("risk", ascending=False), x="zone", y="risk",
                     color="risk", color_continuous_scale="Reds", text="risk")
        fig.update_layout(yaxis_range=[0, 100], plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, width='stretch')

    top_zone = max(real_risk, key=real_risk.get)
    top_crime = df["crime_type"].value_counts().index[0]
    peak_hour = int(df["hour"].value_counts().idxmax())
    st.info(
        f"**Daily tactical brief** — Highest-priority zone: **{top_zone}** "
        f"(DRI {real_risk[top_zone]}/100). Most frequent offense: **{top_crime}**. "
        f"Peak hour: **{peak_hour}:00**."
    )

# ---------------------------------------------------------------------------
# Zone Risk & Reasoning
# ---------------------------------------------------------------------------
elif page == "Zone Risk & Reasoning":
    st.title("Zone Risk & Reasoning")
    banner_bg = bg_image_css(
        "heatmap-bg.jpg",
        "linear-gradient(90deg, rgba(7,9,18,0.75), rgba(251,69,112,0.12))",
    )
    st.markdown(f'<div class="cdt-banner" style="background-image: {banner_bg};"></div>', unsafe_allow_html=True)

    coords = df.groupby("zone")[["latitude", "longitude"]].mean().reset_index()
    coords["risk"] = coords["zone"].map(real_risk)

    map_col, side_col = st.columns([2, 1])

    with map_col, st.container(border=True, key="zone_map_card"):
        map_fig = px.scatter_map(
            coords, lat="latitude", lon="longitude", size="risk", color="risk",
            color_continuous_scale="Reds", size_max=40, zoom=10, hover_name="zone",
            map_style="open-street-map",
        )
        map_fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=460)
        st.plotly_chart(map_fig, width='stretch')
        zone = st.selectbox("Select a zone for a factor-by-factor breakdown", ZONES)

    with side_col:
        with st.container(border=True, key="zone_risk_live"):
            st.markdown("**Zone Risk (Live)**")
            for z, s in sorted(real_risk.items(), key=lambda x: -x[1]):
                color = "#FB4570" if s >= 55 else ("#FFC24B" if s >= 45 else "#22D3A6")
                st.markdown(
                    f'<div style="display:flex; justify-content:space-between; padding:4px 0;">'
                    f'<span>{z}</span><span style="color:{color}; font-family:monospace;">{s}</span></div>',
                    unsafe_allow_html=True,
                )

        st.write("")
        with st.container(border=True, key="zone_reasoning_card"):
            st.markdown('**Cognitive Reasoning** <span style="color:#22D3A6; font-size:0.7rem;">REAL</span>',
                        unsafe_allow_html=True)
            r = zone_reasoning(zone)
            st.metric(f"{zone} — total risk", f"{r['total']}/100")
            factor_df = pd.DataFrame({"factor": list(r["factors"].keys()), "contribution": list(r["factors"].values())})
            fbar = px.bar(factor_df, x="contribution", y="factor", orientation="h")
            fbar.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=220,
                               plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fbar, width='stretch')
            st.caption(r["narrative"])
            if r["recommended"]:
                st.success(f"Recommended unit: **{r['recommended']['unit']}** "
                           f"(ETA {r['recommended']['response_time_min']} min)")

# ---------------------------------------------------------------------------
# Crime Type Predictor
# ---------------------------------------------------------------------------
elif page == "Crime Type Predictor":
    st.title("Crime Type Predictor")
    st.caption("Runs the real trained stacking classifier through the real preprocessing pipeline.")

    col1, col2, col3 = st.columns(3)
    with col1:
        hour = st.slider("Hour", 0, 23, 21)
        zone_in = st.selectbox("Zone", ZONES)
        district = st.selectbox("District", sorted(df["district"].unique()))
        weather = st.selectbox("Weather", sorted(df["weather"].unique()))
    with col2:
        day_of_week = st.selectbox("Day of week", sorted(df["day_of_week"].unique()))
        month = st.slider("Month", 1, 12, 7)
        population_density = st.selectbox("Population density", ["Low", "Medium", "High", "Very High"])
        street_lighting = st.selectbox("Street lighting", ["Poor", "Moderate", "Good"])
    with col3:
        is_festival_day = st.checkbox("Festival day")
        is_weekend = st.checkbox("Weekend")
        is_night = st.checkbox("Night-time", value=True)
        alcohol_outlet_nearby = st.checkbox("Alcohol outlet nearby")

    if st.button("Predict crime type", type="primary"):
        inputs = {
            "hour": hour, "day_of_week": day_of_week, "month": month, "zone": zone_in,
            "district": district, "weather": weather,
            "is_festival_day": int(is_festival_day), "is_weekend": int(is_weekend),
            "is_night": int(is_night), "population_density": population_density,
            "street_lighting": street_lighting, "alcohol_outlet_nearby": int(alcohol_outlet_nearby),
        }
        try:
            label, top3 = predict_crime_type(inputs)
            st.success(f"Predicted crime type: **{label}**")
            top3_df = pd.DataFrame(top3, columns=["crime_type", "probability"])
            st.plotly_chart(px.bar(top3_df, x="probability", y="crime_type", orientation="h"),
                             width='stretch')
        except Exception as e:
            st.error(f"Prediction failed: {e}")

# ---------------------------------------------------------------------------
# Hotspot Clusters (K-Means)
# ---------------------------------------------------------------------------
elif page == "Hotspot Clusters (K-Means)":
    st.title("Hotspot Clusters — K-Means")
    st.caption("Real trained K-Means model clustering historical incidents by location.")

    coords = df[["latitude", "longitude"]].dropna()
    clusters = models["kmeans"].predict(coords)
    plot_df = coords.copy()
    plot_df["cluster"] = clusters.astype(str)

    fig = px.scatter_map(
        plot_df, lat="latitude", lon="longitude", color="cluster",
        zoom=10, map_style="open-street-map", height=600,
    )
    centers = models["kmeans"].cluster_centers_
    fig.add_scattermap(lat=centers[:, 0], lon=centers[:, 1], mode="markers",
                        marker=dict(size=16, color="black", symbol="star"),
                        name="Cluster centers")
    st.plotly_chart(fig, width='stretch')
    st.caption(f"{models['kmeans'].n_clusters} clusters, {len(plot_df):,} incidents plotted.")

# ---------------------------------------------------------------------------
# Resource Allocation
# ---------------------------------------------------------------------------
elif page == "Resource Allocation":
    st.title("Resource Allocation Engine")
    st.caption("Real Hungarian-algorithm assignment via scipy.optimize.linear_sum_assignment.")

    alloc, cost = compute_real_resource_allocation(real_risk)
    st.metric("Total weighted cost", cost)
    st.dataframe(pd.DataFrame(alloc), width='stretch', hide_index=True)

    st.subheader("Explainable AI — native feature importances")
    fi = compute_real_feature_importance()
    fi_col1, fi_col2 = st.columns(2)
    with fi_col1:
        st.write("**Crime-type model**")
        if fi["crime_type_model"]:
            st.dataframe(pd.DataFrame(fi["crime_type_model"], columns=["feature", "importance"]),
                         hide_index=True, width='stretch')
    with fi_col2:
        st.write("**Deployment recommender**")
        if fi["deployment_model"]:
            st.dataframe(pd.DataFrame(fi["deployment_model"], columns=["feature", "importance"]),
                         hide_index=True, width='stretch')

# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# AI Copilot
# ---------------------------------------------------------------------------
elif page == "AI Copilot":
    st.title("AI Copilot")
    banner_bg = bg_image_css(
        "copilot-bg.jpg",
        "linear-gradient(90deg, rgba(7,9,18,0.75), rgba(139,92,246,0.14))",
    )
    st.markdown(f'<div class="cdt-banner" style="background-image: {banner_bg};"></div>', unsafe_allow_html=True)
    st.caption("Template-based response generation, but every figure it cites comes from the real dataset.")

    if "copilot_history" not in st.session_state:
        st.session_state.copilot_history = []

    col_brief, col_ask = st.columns(2)

    with col_brief, st.container(border=True, key="copilot_brief"):
        st.markdown("**Daily Tactical Brief**")
        if st.button("Generate daily brief"):
            st.session_state.last_brief = generate_ai_briefing()
        if st.session_state.get("last_brief"):
            st.code(st.session_state.last_brief, language=None)
        else:
            st.caption("Click to generate today's brief from the real dataset.")

    with col_ask, st.container(border=True, key="copilot_ask", height=420):
        st.markdown("**Ask the Copilot**")
        for msg in st.session_state.copilot_history:
            align = "right" if msg["role"] == "user" else "left"
            tag = "You" if msg["role"] == "user" else "Copilot"
            st.markdown(
                f'<div style="text-align:{align}; margin-bottom:0.5rem;">'
                f'<span style="font-size:0.65rem; padding:1px 8px; border-radius:6px; '
                f'background:rgba(61,139,253,0.25);">{tag}</span>'
                f'<div style="font-size:0.9rem; margin-top:2px;">{msg["text"]}</div></div>',
                unsafe_allow_html=True,
            )
        question = st.text_input("Ask about zones, patrols, crime types…", label_visibility="collapsed",
                                  placeholder="Ask about zones, patrols, crime types…", key="copilot_q")
        if st.button("Send", type="primary") and question:
            answer = generate_ai_briefing(question)
            st.session_state.copilot_history.append({"role": "user", "text": question})
            st.session_state.copilot_history.append({"role": "assistant", "text": answer})
            st.rerun()

elif page == "Analytics":
    st.title("Analytics Center")

    c1, c2 = st.columns(2)
    with c1:
        by_type = df["crime_type"].value_counts().reset_index()
        by_type.columns = ["crime_type", "count"]
        st.plotly_chart(px.pie(by_type, names="crime_type", values="count", title="By crime type"),
                         width='stretch')
    with c2:
        by_zone = df["zone"].value_counts().reset_index()
        by_zone.columns = ["zone", "count"]
        st.plotly_chart(px.bar(by_zone, x="zone", y="count", title="By zone"), width='stretch')

    by_hour = df["hour"].value_counts().sort_index().reset_index()
    by_hour.columns = ["hour", "count"]
    st.plotly_chart(px.line(by_hour, x="hour", y="count", title="Incidents by hour of day", markers=True),
                     width='stretch')

# ---------------------------------------------------------------------------
# Download Report
# ---------------------------------------------------------------------------
elif page == "Download Report":
    st.title("Executive Intelligence Report")
    st.write("Generates a PDF summarizing the current zone risk index and recommended patrol allocation.")
    if st.button("Generate PDF report", type="primary"):
        pdf_bytes = build_pdf_report()
        st.download_button("Download report", data=pdf_bytes,
                            file_name="crimesense_report_streamlit.pdf", mime="application/pdf")
