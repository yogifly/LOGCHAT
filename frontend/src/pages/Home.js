import React, { useState } from "react";
import axios from "axios";
import "./Home.css";

export default function Home() {
  const [file, setFile] = useState(null);
  const [logs, setLogs] = useState(null);
  const [question, setQuestion] = useState("");
  const [chat, setChat] = useState([]); // ✅ store chat history
  const [loadingQa, setLoadingQa] = useState(false);

  const handleFileChange = (e) => setFile(e.target.files[0]);

  const handleUpload = async () => {
    if (!file) return alert("Upload a log file first.");
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await axios.post("http://localhost:5000/upload", formData);
      setLogs(res.data.gemini_insights || res.data);
    } catch (err) {
      alert("Upload failed.");
      console.error(err);
    }
  };

  async function ask() {
    if (!question.trim()) return;
    setLoadingQa(true);

    // add user message immediately
    setChat((prev) => [...prev, { sender: "user", text: question }]);

    try {
      const res = await axios.post("http://localhost:5000/query", { question });
      setChat((prev) => [
        ...prev,
        { sender: "bot", text: res.data.summary, full: res.data },
      ]);
    } catch (e) {
      alert("Query failed");
    } finally {
      setLoadingQa(false);
      setQuestion("");
    }
  }

  // Add this somewhere at the top (before using it)
const threatColors = {
  High: "red",
  Medium: "yellow",
  Low: "green",
  default: "gray"
};

// Helper function to ensure the logs sections are always arrays
const normalizeArray = (val) => {
  if (!val) return [];
  if (Array.isArray(val)) return val;
  return [val];
};


  return (
    <div className="app-container">
      <div className="two-column">
        {/* LEFT COLUMN */}
        <div className="left-panel">
          <h1 className="title">📂 Log Parser</h1>
          <input type="file" onChange={handleFileChange} className="file-input" />
          <button onClick={handleUpload} className="btn btn-green">Upload</button>

          {logs ? (
            <div className="summary-card">
              {logs.summary && (
  <div className="card">
    <div className="card-header">
      <h2>System Diagnostics</h2>
      {logs.threat_level && (
        <span
          className={`badge ${
            threatColors[logs.threat_level] || "default"
          }`}
        >
          Threat: {logs.threat_level}
        </span>
      )}
    </div>
    <p>{logs.summary}</p>
  </div>
)}

{[
  { title: "Findings", items: normalizeArray(logs.findings), color: "blue" },
  { title: "Anomalies", items: normalizeArray(logs.anomalies), color: "red" },
  { title: "Suspicious Activities", items: normalizeArray(logs.suspicious), color: "orange" },
  { title: "Insights", items: normalizeArray(logs.insights), color: "yellow" },
  { title: "Recommendations", items: normalizeArray(logs.recommendations), color: "green" },
]
  .filter((section) => section.items.length > 0)
  .map((section, idx) => (
    <div key={idx} className={`card border-${section.color}`}>
      <div className="card-header">
        <h2>{section.title}</h2>
      </div>
      <ul>
        {section.items.map((item, i) => (
          <li key={i}>{item}</li>
        ))}
      </ul>
    </div>
  ))}

            </div>
          ) : (
            <p className="placeholder">Upload a log file to see summary.</p>
          )}
        </div>

        {/* RIGHT COLUMN */}
        <div className="right-panel">
          <h2>💬 Ask Questions</h2>

          {/* Chat area */}
          <div className="chat-box">
            {chat.map((msg, idx) => (
              <div
                key={idx}
                className={`chat-bubble ${msg.sender === "user" ? "user" : "bot"}`}
              >
                {msg.text}
                {msg.sender === "bot" && msg.full && (
                  <div className="bot-details">
                    {msg.full.findings?.length > 0 && (
                      <>
                        <strong>Findings:</strong>
                        <ul>
                          {msg.full.findings.map((f, i) => <li key={i}>{f}</li>)}
                        </ul>
                      </>
                    )}
                    {msg.full.recommendations?.length > 0 && (
                      <>
                        <strong>Recommendations:</strong>
                        <ul>
                          {msg.full.recommendations.map((r, i) => <li key={i}>{r}</li>)}
                        </ul>
                      </>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Input */}
          <div className="input-row">
            <input
              className="text-input"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Ask about your logs..."
            />
            <button onClick={ask} disabled={loadingQa} className="btn btn-blue">
              {loadingQa ? "..." : "Send"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
