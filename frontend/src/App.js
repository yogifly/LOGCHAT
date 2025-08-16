import React, { useState } from "react";
import axios from "axios";

export default function App() {
  const [file, setFile] = useState(null);
  const [logs, setLogs] = useState(null);

  const handleFileChange = (e) => setFile(e.target.files[0]);

  const handleUpload = async () => {
    if (!file) return alert("Upload a log file first.");

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await axios.post("http://localhost:5000/upload", formData);
      setLogs(res.data.gemini_insights || res.data); // Use gemini_insights if present
    } catch (err) {
      alert("Upload failed.");
      console.error(err);
    }
  };

  // Convert anything into an array
  const normalizeArray = (data) =>
    Array.isArray(data) ? data : data ? [data] : [];

  const threatColors = {
    High: "bg-red-600",
    Medium: "bg-yellow-500",
    Low: "bg-green-600",
  };

  const [question, setQuestion] = useState("");
const [qa, setQa] = useState(null);
const [loadingQa, setLoadingQa] = useState(false);

async function ask() {
  if (!question.trim()) return;
  setLoadingQa(true);
  setQa(null);
  try {
    const res = await axios.post("http://localhost:5000/query", { question });
    setQa(res.data);
  } catch (e) {
    alert("Query failed");
  } finally {
    setLoadingQa(false);
  }
}

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      <div className="max-w-5xl mx-auto space-y-6">
        {/* Upload Section */}
        <div className="bg-gray-800 p-6 rounded-xl shadow-lg">
          <h1 className="text-2xl font-bold mb-4">Log Parser</h1>
          <input
            type="file"
            onChange={handleFileChange}
            className="mb-4 block w-full text-sm text-gray-300 file:mr-4 file:py-2 file:px-4
              file:rounded-full file:border-0
              file:text-sm file:font-semibold
              file:bg-blue-600 file:text-white
              hover:file:bg-blue-500"
          />
          <button
            onClick={handleUpload}
            className="bg-green-600 hover:bg-green-500 px-4 py-2 rounded font-semibold"
          >
            Upload
          </button>
        </div>

        {/* Display Section */}
        {logs ? (
          <>
            {/* Summary Card */}
            {logs.summary && (
              <div className="bg-gray-800 p-6 rounded-xl shadow-lg">
                <div className="flex justify-between items-center">
                  <h2 className="text-xl font-bold">System Diagnostics</h2>
                  {logs.threat_level && (
                    <span
                      className={`px-4 py-1 rounded-full text-sm font-semibold ${
                        threatColors[logs.threat_level] || "bg-gray-500"
                      }`}
                    >
                      Threat: {logs.threat_level}
                    </span>
                  )}
                </div>
                <p className="text-gray-300 mt-4">{logs.summary}</p>
              </div>
            )}

            {/* Dynamic Sections */}
            {[
              { title: "Anomalies", items: normalizeArray(logs.anomalies), color: "border-red-400" },
              { title: "Insights", items: normalizeArray(logs.insights), color: "border-yellow-400" },
              { title: "Recommendations", items: normalizeArray(logs.recommendations), color: "border-green-400" },
            ]
              .filter((section) => section.items.length > 0)
              .map((section, idx) => (
                <div
                  key={idx}
                  className={`bg-gray-800 p-6 rounded-xl shadow-lg border-l-4 ${section.color}`}
                >
                  <h2 className="text-xl font-bold mb-4">{section.title}</h2>
                  <ul className="space-y-2 list-disc list-inside text-gray-300">
                    {section.items.map((item, i) => (
                      <li key={i} className="leading-relaxed">
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
          </>
        ) : (
          <p className="text-gray-400">Upload a log file to see results.</p>
        )}
      </div>
      <div className="bg-gray-800 p-6 rounded-xl shadow-lg">
  <h2 className="text-xl font-bold mb-4">Ask questions about your logs</h2>
  <div className="flex gap-2">
    <input
      className="flex-1 px-4 py-2 rounded bg-gray-700 text-white"
      value={question}
      onChange={(e) => setQuestion(e.target.value)}
      placeholder="e.g., What failed in auth between 2–4 PM?"
    />
    <button
      onClick={ask}
      disabled={loadingQa}
      className="bg-blue-600 hover:bg-blue-500 px-4 py-2 rounded font-semibold"
    >
      {loadingQa ? "Thinking..." : "Ask"}
    </button>
  </div>

  {qa && (
    <div className="mt-6 space-y-4">
      <div className="bg-gray-900 p-4 rounded">
        <h3 className="font-semibold mb-2">Summary</h3>
        <p className="text-gray-300">{qa.summary}</p>
      </div>
      <div className="flex items-center gap-2">
        <span className="font-semibold">Severity:</span>
        <span className={`px-3 py-1 rounded ${
          qa.severity === "High" ? "bg-red-600" :
          qa.severity === "Medium" ? "bg-yellow-500" : "bg-green-600"
        }`}>{qa.severity}</span>
      </div>
      {qa.findings?.length > 0 && (
        <div>
          <h3 className="font-semibold mb-2">Findings</h3>
          <ul className="list-disc list-inside text-gray-300">
            {qa.findings.map((x,i)=><li key={i}>{x}</li>)}
          </ul>
        </div>
      )}
      {qa.recommendations?.length > 0 && (
        <div>
          <h3 className="font-semibold mb-2">Recommendations</h3>
          <ul className="list-disc list-inside text-gray-300">
            {qa.recommendations.map((x,i)=><li key={i}>{x}</li>)}
          </ul>
        </div>
      )}
      {qa.citations?.length > 0 && (
        <div>
          <h3 className="font-semibold mb-2">Cited logs</h3>
          <ul className="list-disc list-inside text-gray-400 text-sm">
            {qa.citations.map((c,i)=><li key={i}><code>{c}</code></li>)}
          </ul>
        </div>
      )}
    </div>
  )}
</div>
    </div>
  
    
  );
}
