from flask import Flask, request, jsonify
from flask_cors import CORS
import re
import datetime
from dotenv import load_dotenv
import os
import google.generativeai as genai

load_dotenv()

app = Flask(__name__)
CORS(app)

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def detect_log_type(line):
    if 'sshd' in line:
        return 'Auth'
    elif re.search(r'\[\w+ \d+ \d+:\d+:\d+\]', line) or 'error' in line.lower():
        return 'Apache'
    elif re.match(r'\d{2}/\d{2}/\d{4}', line) and ('Information' in line or 'Warning' in line or 'Error' in line):
        return 'Windows'
    return 'Unknown'

def parse_apache(line):
    match = re.search(r'\[(.*?)\] \[(\w+)\] (.+)', line)
    if match:
        timestamp = match.group(1)
        level = match.group(2).upper()
        message = match.group(3)
        return {"source": "Apache", "timestamp": timestamp, "level": level, "message": message, "raw": line}
    return {"source": "Apache", "timestamp": "", "level": "INFO", "message": line, "raw": line}

def parse_windows(line):
    try:
        parts = line.split(',')
        timestamp = parts[0].strip()
        level = parts[1].strip().upper()
        message = ','.join(parts[2:]).strip()
        return {"source": "Windows", "timestamp": timestamp, "level": level, "message": message, "raw": line}
    except:
        return {"source": "Windows", "timestamp": "", "level": "INFO", "message": line, "raw": line}

def parse_auth(line):
    match = re.match(r'(\w{3} \d+ \d+:\d+:\d+)', line)
    timestamp = match.group(1) if match else ""
    level = "INFO"
    if "failed" in line.lower():
        level = "ERROR"
    elif "accepted" in line.lower():
        level = "SUCCESS"
    message = line.split("sshd")[-1].strip() if "sshd" in line else line
    return {"source": "Auth", "timestamp": timestamp, "level": level.upper(), "message": message, "raw": line}
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    content = file.read().decode('utf-8').splitlines()

    parsed_logs = []
    for line in content:
        line_type = detect_log_type(line)
        if line_type == 'Apache':
            parsed_logs.append(parse_apache(line))
        elif line_type == 'Windows':
            parsed_logs.append(parse_windows(line))
        elif line_type == 'Auth':
            parsed_logs.append(parse_auth(line))
        else:
            parsed_logs.append({"source": "Unknown", "timestamp": "", "level": "INFO", "message": line, "raw": line})

    # Send parsed logs to Gemini LLM
    gemini_analysis = analyze_with_gemini(parsed_logs)

    return jsonify({
        "parsed_logs": parsed_logs,
        "gemini_insights": gemini_analysis
    })


def analyze_with_gemini(parsed_logs):
    import json
    model = genai.GenerativeModel("gemini-2.5-flash")

    log_lines = "\n".join(
        f"{log['timestamp']} | {log['source']} | {log['level']} | {log['message']}"
        for log in parsed_logs
    )

    prompt = f"""
You are a log analysis assistant. The logs below are from multiple sources (Windows, Apache, Auth). 
Analyze them and return a JSON object with the following fields:

- "summary": One-paragraph summary of the system state
- "insights": Key findings from logs
- "anomalies": Any errors, warnings, or unusual patterns
- "recommendations": Suggestions to fix or improve
- "threat_level": Low / Medium / High based on logs

Respond ONLY in valid JSON format.

Logs:
{log_lines}
"""

    try:
        response = model.generate_content(prompt)
        response_text = response.text.strip()

        # 🧽 Remove ```json or ``` wrappers if present
        if response_text.startswith("```"):
            response_text = re.sub(r"^```(json)?\n?", "", response_text)
            response_text = re.sub(r"\n?```$", "", response_text)

        return json.loads(response_text)
    except Exception as e:
        return {"error": "Gemini response couldn't be parsed", "raw_response": response.text}

if __name__ == '__main__':
    app.run(debug=True)
