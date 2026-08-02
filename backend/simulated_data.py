"""
simulated_data.py
------------------
Synthetic / simulated live-data engine for the CrimeSense CDT platform.

IMPORTANT — HONESTY NOTE FOR THE DEVELOPER (you):
Everything generated here is clearly labeled SIMULATED. Nothing in this
file performs real facial recognition, real ANPR, real weapon detection,
or tracks any real person. It produces plausible, randomly-walked numbers
so the dashboard "streams" during a demo/viva. Disclose this in your
documentation — see README_UPGRADE.md.

Where real computation IS possible (risk index from the actual historical
CSV, feature importance from the actual trained model, resource allocation
via a real assignment algorithm) it is done for real — see app.py.
"""
import random
import time
import math
from datetime import datetime

ZONES = ["North", "Central", "West", "East", "South"]

random.seed(42)

class SimEngine:
    def __init__(self):
        self.t0 = time.time()
        self.state = {
            "iot": {z: {
                "street_lighting_pct": random.randint(55, 92),
                "foot_traffic": random.randint(20, 90),
                "cctv_density_pct": random.randint(40, 95),
                "weather": random.choice(["Clear", "Cloudy", "Rain", "Foggy"]),
            } for z in ZONES},
            "risk_index": {z: random.uniform(35, 78) for z in ZONES},
            "drones": [
                {"id": f"UAV-{i+1}", "zone": z, "battery": random.randint(46, 98),
                 "status": random.choice(["Patrolling", "Returning", "Charging", "Standby"])}
                for i, z in enumerate(ZONES)
            ],
            "patrols": [
                {"id": f"PATROL-{i+1}", "zone": z, "officers": random.randint(2, 6),
                 "eta_min": random.randint(2, 14), "status": "Active"}
                for i, z in enumerate(ZONES)
            ],
            "incident_feed": [],
            "anomaly_flags": [],
            "module_metrics": self._init_module_metrics(),
        }
        self._seed_incidents()

    # ---- module registry for the Command Center grid -----------------
    def _init_module_metrics(self):
        return {
            "st_gcn": {"label": "Spatial-Temporal Graph Forecast", "value": round(random.uniform(71, 89), 1), "unit": "% conf", "icon": "bi-diagram-3", "color": "blue", "kind": "sim", "desc": "Forecasts where crime risk is likely to spread next, using street-network relationships."},
            "spatial_cluster": {"label": "Dynamic HDBSCAN Reclustering", "value": random.randint(6, 11), "unit": "active clusters", "icon": "bi-bullseye", "color": "purple", "kind": "sim", "desc": "Groups nearby incidents into hotspot clusters that update through the day."},
            "rl_patrol": {"label": "RL Patrol Optimizer (PPO)", "value": round(random.uniform(0.72, 0.94), 2), "unit": "coverage reward", "icon": "bi-cpu", "color": "blue", "kind": "sim", "desc": "Suggests patrol routes aimed at covering the most ground with the fastest response."},
            "displacement": {"label": "Crime Displacement Model", "value": random.choice(ZONES), "unit": "top spillover zone", "icon": "bi-arrow-left-right", "color": "orange", "kind": "sim", "desc": "Predicts which neighboring zone crime may shift to if patrols increase here."},
            "resource_alloc": {"label": "Resource Allocation Engine", "value": "Live", "unit": "assignment solved", "icon": "bi-diagram-2", "color": "green", "kind": "real", "desc": "Matches available patrol units to zones so the riskiest areas get the fastest response."},
            "explainable_ai": {"label": "Explainable AI (SHAP-style)", "value": "Live", "unit": "feature importances", "icon": "bi-lightbulb", "color": "green", "kind": "real", "desc": "Shows which factors (lighting, time of day, etc.) most influenced a prediction."},
            "anomaly_engine": {"label": "Anomaly & Escalation Trigger", "value": random.randint(0, 2), "unit": "active alerts", "icon": "bi-exclamation-diamond", "color": "orange", "kind": "sim", "desc": "Flags zones where incident activity is unusually high compared to their own history."},
            "cv_face": {"label": "Face-Match Confidence Engine", "value": f"{random.randint(0,1)} match(es)", "unit": "authorized watchlist", "icon": "bi-person-bounding-box", "color": "purple", "kind": "sim", "desc": "Would flag matches against an authorized watchlist from camera footage."},
            "cv_anpr": {"label": "ANPR — Plate Recognition", "value": random.randint(180, 340), "unit": "plates read/hr", "icon": "bi-car-front", "color": "blue", "kind": "sim", "desc": "Would read vehicle license plates from camera footage."},
            "cv_weapon": {"label": "Weapon Detection", "value": "Clear", "unit": "camera network", "icon": "bi-shield-exclamation", "color": "orange", "kind": "sim", "desc": "Would flag visible weapons detected in camera footage."},
            "cv_crowd": {"label": "Crowd Density Analytics", "value": random.randint(120, 2400), "unit": "est. people", "icon": "bi-people", "color": "purple", "kind": "sim", "desc": "Would estimate how many people are in a monitored area."},
            "cv_fire": {"label": "Fire & Smoke Detection", "value": "Clear", "unit": "camera network", "icon": "bi-fire", "color": "orange", "kind": "sim", "desc": "Would flag visible fire or smoke in camera footage."},
            "cv_vehicle": {"label": "Vehicle Recognition & Class.", "value": random.randint(400, 1600), "unit": "vehicles/hr", "icon": "bi-truck", "color": "blue", "kind": "sim", "desc": "Would count and classify vehicles passing through a monitored area."},
            "reid": {"label": "Person Re-Identification", "value": random.randint(0, 4), "unit": "cross-camera tracks", "icon": "bi-person-lines-fill", "color": "purple", "kind": "sim", "desc": "Would track the same person's movement across multiple cameras."},
            "behaviour": {"label": "Behaviour & Anomaly Detection", "value": random.randint(0, 3), "unit": "flagged behaviours", "icon": "bi-activity", "color": "orange", "kind": "sim", "desc": "Would flag unusual movement patterns (loitering, running, fighting)."},
            "voice_sos": {"label": "Voice Emergency Assistant", "value": random.randint(0, 5), "unit": "calls handled today", "icon": "bi-mic", "color": "green", "kind": "sim", "desc": "Handles incoming emergency voice calls and routes them to dispatch."},
            "pattern_discovery": {"label": "Crime Pattern Discovery Engine", "value": random.randint(3, 9), "unit": "patterns found", "icon": "bi-search", "color": "blue", "kind": "sim", "desc": "Surfaces recurring crime patterns across time and location."},
            "investigation_ai": {"label": "AI Investigation Assistant", "value": "Ready", "unit": "query engine", "icon": "bi-search-heart", "color": "purple", "kind": "sim", "desc": "Answers investigator questions about past incidents in plain language."},
            "knowledge_graph": {"label": "Knowledge Graph Reasoning", "value": random.randint(1200, 4800), "unit": "linked entities", "icon": "bi-diagram-2-fill", "color": "blue", "kind": "sim", "desc": "Links people, places, and incidents together to reveal hidden connections."},
            "cyber_threat": {"label": "Cyber Threat Monitoring", "value": "Nominal", "unit": "network posture", "icon": "bi-hdd-network", "color": "green", "kind": "sim", "desc": "Monitors the platform's own network for suspicious activity."},
            "infra_health": {"label": "Infrastructure Health Monitor", "value": f"{random.randint(92,99)}%", "unit": "uptime", "icon": "bi-broadcast", "color": "green", "kind": "sim", "desc": "Tracks uptime of connected sensors, cameras, and network links."},
            "multi_hazard": {"label": "Multi-Hazard Prediction", "value": random.choice(["Low", "Moderate"]), "unit": "combined risk", "icon": "bi-cloud-lightning", "color": "orange", "kind": "sim", "desc": "Combines crime risk with weather/traffic/fire risk into one outlook."},
            "evidence_mgmt": {"label": "Digital Evidence Management", "value": random.randint(40, 120), "unit": "records secured", "icon": "bi-archive", "color": "blue", "kind": "sim", "desc": "Tracks digital evidence records tied to open cases."},
            "officer_perf": {"label": "Officer Performance Analytics", "value": f"{random.randint(78,95)}%", "unit": "avg response SLA", "icon": "bi-person-badge", "color": "green", "kind": "sim", "desc": "Tracks how quickly officers respond relative to target times."},
            "training_sim": {"label": "AI Training Simulator", "value": random.randint(2, 6), "unit": "scenarios queued", "icon": "bi-collection-play", "color": "purple", "kind": "sim", "desc": "Runs practice scenarios for officer training."},
            "kpi_center": {"label": "Smart City KPI Center", "value": f"{random.randint(70,88)}", "unit": "composite safety score", "icon": "bi-speedometer2", "color": "blue", "kind": "sim", "desc": "Rolls every metric on this page into one overall city safety score."},
            "notif_engine": {"label": "Escalation & Notification Engine", "value": random.randint(3, 14), "unit": "alerts routed/hr", "icon": "bi-bell", "color": "orange", "kind": "sim", "desc": "Routes alerts to the right team automatically based on severity."},
            "twin_replay": {"label": "Digital Twin Timeline Replay", "value": "Ready", "unit": "24h buffer", "icon": "bi-clock-history", "color": "purple", "kind": "sim", "desc": "Lets you rewind the last 24 hours of simulated activity."},
            "nlq": {"label": "Natural Language Query Interface", "value": "Online", "unit": "ask the twin", "icon": "bi-chat-dots", "color": "green", "kind": "sim", "desc": "Lets you ask the twin questions in plain English instead of clicking through menus."},
        }

    def _seed_incidents(self):
        types = ["Theft", "Robbery", "Assault", "Vehicle-theft", "Burglary", "Drug-offense"]
        for i in range(6):
            self.state["incident_feed"].append({
                "id": f"INC-{1000+i}", "zone": random.choice(ZONES), "type": random.choice(types),
                "severity": random.randint(3, 9), "time": datetime.now().strftime("%H:%M:%S"),
            })

    def tick(self):
        """Advance the simulation by one small random-walk step."""
        for z in ZONES:
            iot = self.state["iot"][z]
            iot["foot_traffic"] = self._walk(iot["foot_traffic"], 15, 95, 6)
            iot["cctv_density_pct"] = self._walk(iot["cctv_density_pct"], 35, 98, 3)
            iot["street_lighting_pct"] = self._walk(iot["street_lighting_pct"], 40, 95, 2)
            self.state["risk_index"][z] = round(self._walk(self.state["risk_index"][z], 20, 96, 4), 1)

        for d in self.state["drones"]:
            d["battery"] = max(12, d["battery"] - random.randint(0, 2))
            if d["battery"] < 20:
                d["status"] = "Charging"
                d["battery"] = min(100, d["battery"] + random.randint(5, 15))

        if random.random() < 0.3:
            types = ["Theft", "Robbery", "Assault", "Vehicle-theft", "Burglary", "Suspicious Activity"]
            self.state["incident_feed"].insert(0, {
                "id": f"INC-{random.randint(2000,9999)}", "zone": random.choice(ZONES),
                "type": random.choice(types), "severity": random.randint(2, 9),
                "time": datetime.now().strftime("%H:%M:%S"),
            })
            self.state["incident_feed"] = self.state["incident_feed"][:10]

        m = self.state["module_metrics"]
        m["st_gcn"]["value"] = round(self._walk(m["st_gcn"]["value"], 65, 93, 2), 1)
        m["rl_patrol"]["value"] = round(self._walk(m["rl_patrol"]["value"]*100, 60, 97, 3)/100, 2)
        m["cv_anpr"]["value"] = int(self._walk(m["cv_anpr"]["value"], 150, 380, 20))
        m["cv_crowd"]["value"] = int(self._walk(m["cv_crowd"]["value"], 100, 2600, 150))
        m["cv_vehicle"]["value"] = int(self._walk(m["cv_vehicle"]["value"], 350, 1800, 80))
        m["knowledge_graph"]["value"] = int(self._walk(m["knowledge_graph"]["value"], 1000, 5200, 100))
        m["notif_engine"]["value"] = max(0, int(self._walk(m["notif_engine"]["value"], 0, 18, 3)))
        return self.state

    @staticmethod
    def _walk(val, lo, hi, step):
        val = val + random.uniform(-step, step)
        return max(lo, min(hi, val))

    def snapshot(self):
        return self.state


engine = SimEngine()
