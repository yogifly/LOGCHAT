from flask import Flask, request, jsonify
from flask_cors import CORS
import re
import datetime
from dotenv import load_dotenv
import os
import google.generativeai as genai
import nltk
from nltk.tokenize import word_tokenize

# Download NLTK resources at startup (only needs to run once)
nltk.download('punkt')

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

def clean_and_tokenize(line):
    tokens = word_tokenize(line)
    tokens = [t for t in tokens if t.isalnum() or t in [':', '[', ']', '-', '.', ',', '/']]
    return tokens

def parse_apache(line):
    tokens = clean_and_tokenize(line)
    timestamp = ""
    level = "INFO"
    message = ""
    # Find timestamp in tokens
    if '[' in tokens and ']' in tokens:
        try:
            start = tokens.index('[')
            end = tokens.index(']')
            timestamp = ' '.join(tokens[start+1:end])
        except:
            timestamp = ""
    # Find log level
    levels = ['error', 'notice', 'warn', 'info', 'debug']
    for l in levels:
        if l in tokens:
            level = l.upper()
            break
    # Message is everything after the last ']'
    try:
        last_bracket = max(idx for idx, t in enumerate(tokens) if t == ']')
        message = ' '.join(tokens[last_bracket+1:])
    except:
        message = ' '.join(tokens)
    return {
        "source": "Apache",
        "timestamp": timestamp,
        "level": level,
        "message": message.strip(),
        "raw": line
    }

def parse_windows(line):
    tokens = clean_and_tokenize(line)
    timestamp = ""
    level = "INFO"
    message = ""
    # Timestamp is usually the first token(s)
    if len(tokens) > 2 and tokens[0].count('-') == 2:
        timestamp = tokens[0]
    # Level is often 'info', 'warning', 'error'
    levels = ['info', 'warning', 'error']
    for l in levels:
        if l in tokens:
            level = l.upper()
            break
    # Message is everything after the level
    try:
        level_idx = next(idx for idx, t in enumerate(tokens) if t.lower() == level.lower())
        message = ' '.join(tokens[level_idx+1:])
    except:
        message = ' '.join(tokens)
    return {
        "source": "Windows",
        "timestamp": timestamp,
        "level": level,
        "message": message.strip(),
        "raw": line
    }

def parse_auth(line):
    tokens = clean_and_tokenize(line)
    timestamp = ""
    level = "INFO"
    message = ""
    # Timestamp is usually first 3 tokens (e.g., Mar 6 06:18:01)
    if len(tokens) >= 3:
        timestamp = ' '.join(tokens[:3])
    # Level detection
    if "failed" in tokens or "error" in tokens:
        level = "ERROR"
    elif "accepted" in tokens or "success" in tokens:
        level = "SUCCESS"
    # Message is everything after timestamp
    message = ' '.join(tokens[3:])
    return {
        "source": "Auth",
        "timestamp": timestamp,
        "level": level.upper(),
        "message": message.strip(),
        "raw": line
    }

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

Respond ONLY in valid JSON format. Do NOT include markdown code fences.

Logs:
{log_lines}
"""

    try:
        response = model.generate_content(prompt)

        # 🔹 Debug print of raw Gemini response
        print("\n========== RAW GEMINI RESPONSE ==========")
        print(response)
        print("=========================================\n")

        # Use safe text extraction
        response_text = ""
        if hasattr(response, "text") and response.text:
            response_text = response.text.strip()
        elif hasattr(response, "candidates") and response.candidates:
            parts = response.candidates[0].content.parts
            if parts and hasattr(parts[0], "text"):
                response_text = parts[0].text.strip()

        # Remove ```json ... ``` wrappers if they exist
        if response_text.startswith("```"):
            response_text = re.sub(r"^```(?:json)?", "", response_text.strip(), flags=re.IGNORECASE)
            response_text = re.sub(r"```$", "", response_text.strip())

        response_text = response_text.strip()

        return json.loads(response_text)

    except json.JSONDecodeError as e:
        return {
            "error": "Gemini returned invalid JSON",
            "raw_response": str(response) if 'response' in locals() else None,
            "exception": str(e)
        }
    except Exception as e:
        return {
            "error": "Unexpected error",
            "exception": str(e)
        }



if __name__ == '__main__':
    app.run(debug=True)