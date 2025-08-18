import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import "./LandingPage.css";

export default function LandingPage() {
  const [uploadProgress, setUploadProgress] = useState(0);
  const [showAnalysis, setShowAnalysis] = useState(false);
  const [showResults, setShowResults] = useState(false);

  useEffect(() => {
    let timer;
    if (uploadProgress < 100) {
      timer = setTimeout(() => setUploadProgress(uploadProgress + 20), 400);
    } else {
      setTimeout(() => setShowAnalysis(true), 800);
      setTimeout(() => setShowResults(true), 2000);
    }
    return () => clearTimeout(timer);
  }, [uploadProgress]);

  return (
    <div className="landing-wrapper">

      {/* Welcome + Intro */}
      <div className="intro-section">
        <h1 className="welcome-title">LogChat - AI powered Log Analyzer</h1>
        <p className="intro-text">
          A <span className="highlight"> log analysis system </span> 
           that helps you parse, analyze, and understand logs instantly.
        </p>
        <p className="intro-subtext">
          Built with <span className="tech">RAG</span>, <span className="tech">LangChain</span>, 
          <span className="tech"> Pinecone</span>, and <span className="tech">Gemini AI</span>.
        </p>
      </div>

      {/* Terminal Window */}
      <div className="terminal-window">
        {/* Header */}
        <div className="terminal-header">
        <span className="terminal-title">Terminal</span>
        <div className="terminal-controls">
            <button className="ctrl-btn minimize">—</button>
            <button className="ctrl-btn maximize">▢</button>
            <button className="ctrl-btn close">✕</button>
        </div>
        </div>

        {/* Body */}
        <div className="terminal-body">
          <p><span className="highlight">LogChat....</span></p>
          <p>AI-powered log analyzer ready.</p>
          <p className="cmd">C:\User\Logs&gt; Uploading activity.logs</p>

          {/* Upload Progress */}
          <div className="progress-bar">
            <div
              className="progress-fill"
              style={{ width: `${uploadProgress}%` }}
            ></div>
          </div>

          {/* Analysis */}
          {showAnalysis && <p className="cmd">Analyzing logs...</p>}

          {/* Results */}
          {showResults && (
            <>
              <p className="cmd">Results Generated:</p>
              <ul className="results-list">
                <li>⚠ 3 anomalies detected in Apache worker logs</li>
                <li>⏱ High response time spikes at 12:30 PM</li>
                <li>🔒 Multiple failed login attempts detected</li>
              </ul>
              <div className="chat-box">
                <span className="cmd">C:\AskLogs&gt;</span>
                <input
                  type="text"
                  placeholder="Ask about your logs..."
                  className="chat-input"
                />
              </div>
            </>
          )}
        </div>
      </div>

          {showResults && (
  <div className="report-window">
    <h2 className="report-title">📊 Log Analysis Report</h2>
    
    <div className="report-section">
      <h3>📝 Summary</h3>
      <p>
        The system processed <b>activity.logs</b> and detected multiple anomalies 
        indicating potential security and performance issues.
      </p>
    </div>

    <div className="report-section">
      <h3>🔍 Insights</h3>
      <ul>
        <li>⚠ Error rate increased by 35% in the last 24 hours.</li>
        <li>📈 Traffic surge noticed during midnight hours.</li>
        <li>🛑 Unauthorized access attempts from 3 different IPs.</li>
      </ul>
    </div>

    <div className="report-section">
      <h3>✅ Recommendations</h3>
      <ul>
        <li>Enable stricter firewall rules to block repeated failed logins.</li>
        <li>Optimize database queries to handle high-traffic hours.</li>
        <li>Set up alerting for unusual error spikes.</li>
      </ul>
    </div>

    <div className="report-section">
      <h3>📚 Citations</h3>
      <ul>
        <li>[1] Apache Worker Log Reference Docs</li>
        <li>[2] OWASP Security Guidelines 2025</li>
        <li>[3] Internal Monitoring Best Practices</li>
      </ul>
    </div>

    <button className="download-btn">⬇ Download PDF</button>
  </div>
)}

      {/* CTA */}
      <Link to="/home" className="landing-link">
        <button className="landing-btn">Go to Log Parser</button>
      </Link>
    </div>
  );
}

