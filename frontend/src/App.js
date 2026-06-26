import React, { useState, useEffect } from "react";
import "./App.css";

import { Bar, Pie } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  Tooltip,
  Legend
} from "chart.js";

ChartJS.register(CategoryScale, LinearScale, BarElement, ArcElement, Tooltip, Legend);

function TabButton({ active, onClick, children }) {
  return (
    <button className={`tab-btn ${active ? "active" : ""}`} onClick={onClick}>
      {children}
    </button>
  );
}

export default function App() {

  // ---------------- CHAT STATES ----------------
  const [chatOpen, setChatOpen] = useState(false);
  const [chatInput, setChatInput] = useState("");
  const [chatMessages, setChatMessages] = useState([]);

  async function sendMessage() {
  if (!chatInput.trim()) return;

  setChatMessages((prev) => [...prev, { sender: "user", text: chatInput }]);
  const userMessage = chatInput;
  setChatInput("");

  try {
    const resp = await fetch("http://localhost:8000/ai_chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: userMessage })
    });

    const data = await resp.json();

    setChatMessages((prev) => [...prev, { sender: "bot", text: data.reply }]);

  } catch (err) {
    setChatMessages((prev) => [
      ...prev,
      { sender: "bot", text: "AI could not respond right now." }
    ]);
  }
}


  // ---------------- APP STATES ----------------
  const [tab, setTab] = useState("predict");
  const [form, setForm] = useState({
    attendance: 75,
    study_hours: 3,
    internal_marks: 60,
    assignments_submitted: 4,
    activities: 1,
    previous_gpa: 7,
    screen_time: 4
  });

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [whatif, setWhatif] = useState(null);
  const [rec, setRec] = useState(null);
  const [history, setHistory] = useState([]);

  // ---------------- FUNCTIONS ----------------

  useEffect(() => {
    fetchAnalytics();
  }, []);

  useEffect(() => {
    if (tab === "history") fetchHistory();
  }, [tab]);

  function handleChange(e) {
    setForm({ ...form, [e.target.name]: e.target.value });
  }

  async function predict(e) {
    e.preventDefault();
    setLoading(true);
    setResult(null);

    try {
      const resp = await fetch("http://localhost:8000/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          attendance: Number(form.attendance),
          study_hours: Number(form.study_hours),
          internal_marks: Number(form.internal_marks),
          assignments_submitted: Number(form.assignments_submitted),
          activities: Number(form.activities),
          previous_gpa: Number(form.previous_gpa),
          screen_time: Number(form.screen_time)
        })
      });

      const data = await resp.json();
      setResult(data);
      fetchAnalytics();
    } catch {
      alert("Backend Error");
    }

    setLoading(false);
  }

  async function fetchAnalytics() {
    const resp = await fetch("http://localhost:8000/analytics");
    const data = await resp.json();
    setAnalytics(data);
  }

  async function fetchHistory() {
    const resp = await fetch("http://localhost:8000/predictions");
    const data = await resp.json();

    const cleaned = data.predictions.map((p) => ({
      ...p,
      payload:
        typeof p.payload === "string"
          ? JSON.parse(p.payload.replace(/'/g, '"'))
          : p.payload
    }));

    setHistory(cleaned);
  }

  async function getRecommendations() {
    const resp = await fetch("http://localhost:8000/recommend", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(form)
    });

    setRec(await resp.json());
  }

  function downloadReport() {
    window.open("http://localhost:8000/export_pdf", "_blank");
  }

  // ---------------- UI START ----------------

  return (
    <div className="main">

      {/* CHAT ICON */}
      <div className="chat-button" onClick={() => setChatOpen(true)}>
        💬
      </div>

      {/* CHAT POPUP */}
      {chatOpen && (
        <div className="chat-popup">
          <div className="chat-header">
            <strong>AI Study Assistant</strong>
            <button onClick={() => setChatOpen(false)}>✖</button>
          </div>

          <div className="chat-body">
            {chatMessages.map((m, i) => (
              <div key={i} className={m.sender === "user" ? "msg-user" : "msg-bot"}>
                {m.text}
              </div>
            ))}
          </div>

          <div className="chat-input-area">
            <input
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              placeholder="Ask something…"
            />
            <button onClick={sendMessage}>Send</button>
          </div>
        </div>
      )}

      {/* MAIN CONTENT */}
      <div className="container">

        {/* LEFT PANEL */}
        <div className="left">

          <div className="tabs">
            <TabButton active={tab === "predict"} onClick={() => setTab("predict")}>Predict</TabButton>
            <TabButton active={tab === "whatif"} onClick={() => setTab("whatif")}>What-If</TabButton>
            <TabButton active={tab === "analytics"} onClick={() => setTab("analytics")}>Analytics</TabButton>
            <TabButton active={tab === "report"} onClick={() => setTab("report")}>Report</TabButton>
            <TabButton active={tab === "history"} onClick={() => setTab("history")}>History</TabButton>
          </div>

          {/* ---- INSERT YOUR FULL TAB CONTENT (unchanged) ---- */}
          {/* I am NOT modifying your logic; only placing properly */}

          {/* --------------------- PREDICT TAB --------------------- */}
          {tab === "predict" && (
            <form className="card" onSubmit={predict}>
              <h2>Predict Student Performance</h2>

              {[ 
                ["Attendance %", "attendance"],
                ["Study Hours", "study_hours"],
                ["Internal Marks", "internal_marks"],
                ["Assignments Submitted", "assignments_submitted"],
                ["Activities", "activities"],
                ["Previous GPA (0–10)", "previous_gpa"],
                ["Screen Time (hrs/day)", "screen_time"]
              ].map(([label, name]) => (
                <label key={name} className="field">
                  <span>{label}</span>
                  <input type="number" name={name} value={form[name]} onChange={handleChange} required />
                </label>
              ))}

              <div className="row">
                <button className="primary" disabled={loading}>
                  {loading ? "Predicting…" : "Predict"}
                </button>

                <button type="button" onClick={getRecommendations}>
                  Get Recommendations
                </button>
              </div>

              {result && (
                <div className="result">
                  <h3>
                    Prediction:{" "}
                    <span className={result.label === "Pass" ? "pass" : "fail"}>
                      {result.label}
                    </span>
                  </h3>

                  <p>Confidence: {(result.confidence * 100).toFixed(2)}%</p>
                  <p>Risk Score: {result.risk_score}</p>

                  <h4>Explanation</h4>
                  <pre>{JSON.stringify(result.explanation, null, 2)}</pre>
                </div>
              )}

              {rec && (
                <div className="recommend">
                  <h3>Top Recommendations</h3>
                  {rec.recommendations.slice(0, 5).map((r, i) => (
                    <div key={i} className="rec-item">
                      <span>{i + 1}. {r.action}</span>
                      <span>+{r.delta_points} pts → {(r.new_prob * 100).toFixed(1)}%</span>
                    </div>
                  ))}
                </div>
              )}
            </form>
          )}

          {/* --------------------- WHAT-IF TAB --------------------- */}
          {tab === "whatif" && (
            <div className="card">
              <h2>What-If Simulator</h2>

              <button className="primary"
                onClick={async () => {
                  const resp = await fetch("http://localhost:8000/whatif", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                      ...form,
                      modifications: { study_hours: Number(form.study_hours) + 1 }
                    })
                  });
                  setWhatif(await resp.json());
                }}>
                +1 Study Hour
              </button>

              <button className="primary"
                onClick={async () => {
                  const resp = await fetch("http://localhost:8000/whatif", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                      ...form,
                      modifications: { attendance: Number(form.attendance) + 10 }
                    })
                  });
                  setWhatif(await resp.json());
                }}>
                +10% Attendance
              </button>

              <button className="primary"
                onClick={async () => {
                  const resp = await fetch("http://localhost:8000/whatif", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                      ...form,
                      modifications: { assignments_submitted: Number(form.assignments_submitted) + 1 }
                    })
                  });
                  setWhatif(await resp.json());
                }}>
                +1 Assignment
              </button>

              <button className="primary"
                onClick={async () => {
                  const resp = await fetch("http://localhost:8000/whatif", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                      ...form,
                      modifications: { screen_time: Math.max(0, Number(form.screen_time) - 1) }
                    })
                  });
                  setWhatif(await resp.json());
                }}>
                -1 Screen Hour
              </button>

              {whatif && (
                <div className="result">
                  <h4>
                    Base: {(whatif.base.prob_pass * 100).toFixed(2)}% → New:{" "}
                    {(whatif.modified.prob_pass * 100).toFixed(2)}%
                  </h4>
                  <p>Change: {whatif.delta_prob_points} pts</p>
                </div>
              )}
            </div>
          )}

          {/* --------------------- ANALYTICS TAB --------------------- */}
          {tab === "analytics" && (
            <div className="card">
              <h2>Analytics Dashboard</h2>

              {analytics ? (
                <>
                  <div className="stats-grid">
                    <div className="stat-box">
                      <h4>Total Predictions</h4>
                      <p>{analytics.total_predictions}</p>
                    </div>

                    <div className="stat-box">
                      <h4>Pass Rate</h4>
                      <p>{(analytics.pass_rate * 100).toFixed(1)}%</p>
                    </div>

                    <div className="stat-box">
                      <h4>Avg Confidence</h4>
                      <p>{(analytics.avg_confidence * 100).toFixed(1)}%</p>
                    </div>
                  </div>

                  <h3>Pass / Fail Distribution</h3>
                  <Pie
                    key="passfail-chart"
                    data={{
                      labels: ["Fail", "Pass"],
                      datasets: [
                        {
                          data: [
                            analytics.total_predictions * (1 - analytics.pass_rate),
                            analytics.total_predictions * analytics.pass_rate
                          ],
                          backgroundColor: ["#f44336", "#4caf50"]
                        }
                      ]
                    }}
                    style={{ maxWidth: "260px", margin: "0 auto" }}
                  />

                  <h3>Feature Importance</h3>
                  <Bar
                    key="feature-bar"
                    data={{
                      labels: analytics.feature_importances.map((i) => i[0]),
                      datasets: [
                        {
                          label: "Importance",
                          data: analytics.feature_importances.map((i) => i[1]),
                          backgroundColor: "#1976d2"
                        }
                      ]
                    }}
                  />
                </>
              ) : (
                <p>Loading…</p>
              )}
            </div>
          )}

          {/* --------------------- HISTORY TAB --------------------- */}
          {tab === "history" && (
            <div className="card history-card">
              <h2>Prediction History</h2>

              <table className="history-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Attendance</th>
                    <th>Marks</th>
                    <th>GPA</th>
                    <th>Screen Time</th>
                    <th>Label</th>
                    <th>Confidence</th>
                    <th>Risk</th>
                    <th>Time</th>
                  </tr>
                </thead>

                <tbody>
                  {history.map((item, idx) => (
                    <tr key={idx}>
                      <td>{item.id}</td>
                      <td>{item.payload.attendance}</td>
                      <td>{item.payload.internal_marks}</td>
                      <td>{item.payload.previous_gpa}</td>
                      <td>{item.payload.screen_time}</td>
                      <td className={item.label === "Pass" ? "pass" : "fail"}>
                        {item.label}
                      </td>
                      <td>{(Number(item.confidence) * 100).toFixed(1)}%</td>
                      <td>{item.risk}</td>
                      <td>{item.created_at}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* --------------------- REPORT TAB --------------------- */}
          {tab === "report" && (
            <div className="card">
              <h2>Export Report</h2>
              <button className="primary" onClick={downloadReport}>
                Download PDF
              </button>
            </div>
          )}
        </div>

        {/* RIGHT PANEL */}
        <div className="right">
          <div className="info-card">
            <h3>Quick Tips</h3>
            <ul>
              <li>Increase study hours</li>
              <li>Reduce screen time</li>
              <li>Use What-If simulation</li>
            </ul>
          </div>

          <div className="history-card">
            <h4>Raw History JSON</h4>
            <button onClick={() => window.open("http://localhost:8000/predictions", "_blank")}>
              Open in New Tab
            </button>
          </div>
        </div>

      </div>

    </div>
  );
}
