from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import joblib
import pandas as pd
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import os
import io
from fastapi.responses import StreamingResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import requests
from fastapi import FastAPI
from pydantic import BaseModel

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

MODEL_PATH = "model.joblib"
DB_PATH = "predictions.db"

# Load model
saved = joblib.load(MODEL_PATH)
pipeline = saved["pipeline"]
features = saved["features"]
means = saved["means"]
importances = saved["importances"]

app = FastAPI(title="Student Performance Predictor")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# init db
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY,
            payload TEXT,
            label TEXT,
            confidence REAL,
            risk REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

init_db()

class Student(BaseModel):
    attendance: float = Field(..., ge=0, le=100)
    study_hours: float = Field(..., ge=0)
    internal_marks: float = Field(..., ge=0, le=100)
    assignments_submitted: int = Field(..., ge=0)
    activities: int = Field(..., ge=0)
    previous_gpa: float = Field(..., ge=0, le=10)
    screen_time: float = Field(..., ge=0)

# risk score
def compute_risk(p):
    risk = (
        max(0, 90 - p["attendance"]) * 0.3 +
        max(0, 60 - p["internal_marks"]) * 0.3 +
        max(0, 5 - p["previous_gpa"]) * 4 +
        p["screen_time"] * 2
    ) / 10

    return round(min(max(risk, 0), 100), 2)

# explainability approx
def explain(p):
    result = {}
    total_imp = sum(importances.values())
    for f in features:
        imp = importances[f] / total_imp
        contrib = (p[f] - means[f]) * imp
        result[f] = round(contrib, 4)
    return result

@app.post("/predict")
def predict(data: Student):
    p = data.dict()

    X = pd.DataFrame([[p[f] for f in features]], columns=features)

    prob = pipeline.predict_proba(X)[0]
    pred = int(pipeline.predict(X)[0])
    label = "Pass" if pred == 1 else "Fail"
    confidence = round(float(prob[pred]), 4)
    risk = compute_risk(p)
    explanation = explain(p)

    # Save to DB
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("INSERT INTO predictions (payload, label, confidence, risk) VALUES (?, ?, ?, ?)",
                (str(p), label, confidence, risk))
    conn.commit()
    conn.close()

    return {
        "label": label,
        "confidence": confidence,
        "risk_score": risk,
        "explanation": explanation
    }
# append these imports at top of your app.py
import io
from fastapi.responses import StreamingResponse, JSONResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from operator import itemgetter

# -------------------------------
# Helper: what-if (if not already)
# -------------------------------
@app.post("/whatif")
def whatif_endpoint(payload: dict):
    base = {k: float(payload.get(k, 0)) for k in features}

    # modifications passed inside payload
    mods = payload.get("modifications", {})
    modified = base.copy()

    for k, v in mods.items():
        if k in modified:
            modified[k] = float(v)

    # Convert to DataFrame
    Xb = pd.DataFrame([[base[f] for f in features]], columns=features)
    Xm = pd.DataFrame([[modified[f] for f in features]], columns=features)

    # Probabilities
    prob_b = float(pipeline.predict_proba(Xb)[0][1])
    prob_m = float(pipeline.predict_proba(Xm)[0][1])

    return {
        "base": {
            "prob_pass": prob_b
        },
        "modified": {
            "prob_pass": prob_m
        },
        "delta_prob_points": round((prob_m - prob_b) * 100, 3)
    }

# -------------------------------
# Analytics endpoint
# -------------------------------
@app.get("/analytics")
def analytics():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # read predictions (label + confidence)
    cur.execute("SELECT label, confidence FROM predictions")
    rows = cur.fetchall()
    conn.close()

    total = len(rows)
    if total == 0:
        return {
            "total_predictions": 0,
            "pass_rate": 0,
            "avg_confidence": 0,
            "feature_importances": []
        }

    # label is "Pass" or "Fail"
    pass_count = sum(1 for r in rows if r[0].lower() == "pass")
    avg_conf = sum(float(r[1]) for r in rows) / total

    # build feature importance safely
    try:
        fi_sorted = sorted(importances.items(), key=lambda x: -x[1])
    except:
        fi_sorted = []

    return {
        "total_predictions": total,
        "pass_rate": round(pass_count / total, 4),
        "avg_confidence": round(avg_conf, 4),
        "feature_importances": fi_sorted
    }

# -------------------------------
# Recommendation engine
# -------------------------------
@app.post("/recommend")
def recommend(payload: dict):
    """
    Given payload (7 features), tests small improvements for a set of actions and returns top 3 actions
    Actions tested:
      - increase attendance by +5, +10
      - increase study_hours by +1, +2
      - increase internal_marks by +5, +10
      - increase previous_gpa by +0.5, +1
      - reduce screen_time by -1, -2
      - increase assignments_submitted by +1
    Returns sorted list by delta change in pass probability (points)
    """
    base = {k: float(payload.get(k, 0)) for k in features}
    Xb = pd.DataFrame([[base[f] for f in features]], columns=features)
    base_prob = float(pipeline.predict_proba(Xb)[0][1])

    actions = []
    # define candidate actions: tuple(label, modified_payload)
    candidates = []

    def add_candidate(mods, label):
        tmp = base.copy()
        for k, v in mods.items():
            if k in tmp:
                tmp[k] = tmp[k] + v
                # keep within sensible bounds
                if k == "attendance":
                    tmp[k] = min(max(tmp[k], 0), 100)
                if k == "previous_gpa":
                    tmp[k] = min(max(tmp[k], 0), 10)
                if k == "screen_time":
                    tmp[k] = max(tmp[k], 0)
        candidates.append((label, tmp))

    # populate candidates
    add_candidate({"attendance": 5}, "Increase attendance by 5%")
    add_candidate({"attendance": 10}, "Increase attendance by 10%")
    add_candidate({"study_hours": 1}, "Add 1 hour of study per day")
    add_candidate({"study_hours": 2}, "Add 2 hours of study per day")
    add_candidate({"internal_marks": 5}, "Improve internal marks by 5 points")
    add_candidate({"internal_marks": 10}, "Improve internal marks by 10 points")
    add_candidate({"previous_gpa": 0.5}, "Improve GPA by 0.5")
    add_candidate({"previous_gpa": 1.0}, "Improve GPA by 1.0")
    add_candidate({"screen_time": -1}, "Reduce screen time by 1 hour")
    add_candidate({"screen_time": -2}, "Reduce screen time by 2 hours")
    add_candidate({"assignments_submitted": 1}, "Submit 1 extra assignment")

    for label, mod_payload in candidates:
        Xm = pd.DataFrame([[mod_payload[f] for f in features]], columns=features)
        prob_m = float(pipeline.predict_proba(Xm)[0][1])
        delta = (prob_m - base_prob) * 100
        actions.append({"action": label, "new_prob": round(prob_m,4), "delta_points": round(delta,3)})

    # sort descending by delta
    actions_sorted = sorted(actions, key=lambda x: -x["delta_points"])
    return {"base_prob": round(base_prob,4), "recommendations": actions_sorted[:5]}

# -------------------------------
# Export (PDF) for last prediction
# -------------------------------
@app.get("/export_pdf")
def export_pdf():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT payload, label, confidence, risk, created_at
        FROM predictions
        ORDER BY id DESC LIMIT 1
    """)
    row = cur.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="No predictions found")

    payload_str, label, confidence, risk, created_at = row

    payload = eval(payload_str.replace("'", '"'))

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # HEADER BAR
    c.setFillColorRGB(0.05, 0.3, 0.8)
    c.rect(0, height - 70, width, 70, fill=True, stroke=False)
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 22)
    c.drawString(40, height - 40, "Student Performance Report")

    # DETAILS
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica", 13)
    c.drawString(40, height - 110, f"Prediction: {label}")
    c.drawString(40, height - 130, f"Confidence: {(confidence * 100):.1f}%")
    c.drawString(40, height - 150, f"Risk Score: {risk}")
    c.drawString(40, height - 170, f"Generated: {created_at}")

    # INPUT TITLE
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, height - 210, "Input Factors:")

    y = height - 240
    c.setFont("Helvetica", 12)

    for key, value in payload.items():
        c.drawString(50, y, f"{key}: {value}")
        y -= 20

        if y < 50:
            c.showPage()
            y = height - 50

    c.showPage()
    c.save()
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=student_report.pdf"}
    )

@app.get("/predictions")
def list_predictions(limit: int = 50):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT id, payload, label, confidence, risk, created_at
        FROM predictions
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))
    
    rows = cur.fetchall()
    conn.close()

    cols = ["id", "payload", "label", "confidence", "risk", "created_at"]
    return {
        "count": len(rows),
        "predictions": [dict(zip(cols, r)) for r in rows]
    }

class ChatRequest(BaseModel):
    message: str

@app.post("/ai_chat")
def ai_chat(req: ChatRequest):
    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "http://localhost",   # required
        "X-Title": "Student Predictor App",   # optional
        "Content-Type": "application/json"
    }

    payload = {
        "model": "meta-llama/llama-3-8b-instruct",  # FREE + working
        "messages": [
            {"role": "system", "content": "You are a helpful study assistant."},
            {"role": "user", "content": req.message}
        ]
    }

    try:
        r = requests.post(url, json=payload, headers=headers)
        data = r.json()

        print("AI RAW:", data)   # Debug logs

        # If OpenRouter returns error
        if "error" in data:
            return {"reply": f"AI Error: {data['error']}"}

        if "choices" not in data:
            return {"reply": "AI Error: No choices returned."}

        reply = data["choices"][0]["message"]["content"]
        return {"reply": reply}

    except Exception as e:
        return {"reply": f"AI Error: {str(e)}"}
