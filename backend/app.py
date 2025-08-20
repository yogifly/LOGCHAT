from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import re
import json
import nltk
from dotenv import load_dotenv
import google.generativeai as genai

from log_parser import parse_log_line
from rag.ingest import ingest_parsed_logs
from rag.retrieval import answer_question
from metrics import compute_metrics

# --- NLTK setup (safe) ---
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    try:
        nltk.download('punkt', quiet=True)
    except Exception:
        pass

# --- App setup ---
load_dotenv()
app = Flask(__name__)
CORS(app)

UPLOADS_DIR = "uploads"
os.makedirs(UPLOADS_DIR, exist_ok=True)
LAST_LOG_PATH = os.path.join(UPLOADS_DIR, "last.log")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


def analyze_with_gemini(parsed_logs):
    """
    Ask Gemini to summarize/assess logs. Returns dict.
    Falls back to simple structured summary if Gemini not configured.
    """
    try:
        if not GEMINI_API_KEY:
            # Fallback: lightweight local summary
            levels = [pl.get("level", "INFO") for pl in parsed_logs]
            errors = sum(1 for l in levels if str(l).upper() in ("ERROR", "CRITICAL"))
            warns = sum(1 for l in levels if str(l).upper() in ("WARN", "WARNING"))
            return {
                "summary": f"Parsed {len(parsed_logs)} lines; {errors} errors, {warns} warnings.",
                "insights": ["Local summary used (Gemini API key not set)."],
                "anomalies": ["Counts only; no LLM analysis."],
                "recommendations": ["Set GEMINI_API_KEY to enable deep analysis."],
                "threat_level": "Medium" if errors > 0 else "Low",
            }

        model = genai.GenerativeModel("gemini-2.5-flash")
        lines = []
        for log in parsed_logs:
            parts = [
                str(log.get("timestamp", "")),
                log.get("level", ""),
                log.get("ip", ""),
                log.get("template", "") or log.get("message", ""),
            ]
            lines.append(" | ".join(p for p in parts if p))

        prompt = f"""
You are a log analysis assistant. The logs below are parsed via Drain3 (templates) with light enrichment.
Return ONLY valid JSON with fields:
- "summary": one paragraph
- "insights": array of key findings
- "anomalies": array of errors/warnings/unusual patterns
- "recommendations": array of concrete actions
- "threat_level": one of Low/Medium/High

Logs:
{os.linesep.join(lines)}
"""
        resp = model.generate_content(prompt)

        # Extract safe text
        text = ""
        if hasattr(resp, "text") and resp.text:
            text = resp.text.strip()
        elif hasattr(resp, "candidates") and resp.candidates:
            parts = resp.candidates[0].content.parts
            if parts and hasattr(parts[0], "text"):
                text = parts[0].text.strip()

        # Strip code fences if any
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?", "", text, flags=re.I).strip()
            text = re.sub(r"```$", "", text).strip()

        return json.loads(text)
    except Exception as e:
        return {"error": "Gemini analysis failed", "exception": str(e)}


@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    try:
        content = file.read().decode("utf-8", errors="ignore").splitlines()
    except Exception:
        return jsonify({"error": "Unable to read file as UTF-8"}), 400

    # ✅ Save last uploaded file so /metrics can reuse it
    with open(LAST_LOG_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(content))

    parsed_logs = [parse_log_line(line) for line in content if line.strip()]

    gemini_analysis = analyze_with_gemini(parsed_logs)

    # Ingest to local RAG stub (safe)
    try:
        ingested = ingest_parsed_logs(parsed_logs)
    except Exception as e:
        ingested = 0
        print("Ingestion error:", e)

    return jsonify(
        {
            "parsed_logs": parsed_logs,
            "gemini_insights": gemini_analysis,
            "ingested_chunks": ingested,
        }
    )


@app.route("/query", methods=["POST"])
def query():
    try:
        data = request.get_json(silent=True) or {}
        question = data.get("question")
        if not question:
            return jsonify({"error": "No question provided"}), 400
        result = answer_question(question)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/metrics", methods=["GET"])
def metrics():
    try:
        if not os.path.exists(LAST_LOG_PATH):
            return jsonify({"error": "No logs uploaded yet"}), 404

        with open(LAST_LOG_PATH, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()

        metrics = compute_metrics(lines)
        return jsonify(metrics)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    # Use a fixed port for convenience
    app.run(debug=True, port=5000)
