import re

def parse_auth_line(line):
    match = re.match(r'(?P<timestamp>\w{3} \d+ \d+:\d+:\d+)', line)
    level = "INFO"
    if "failed" in line.lower():
        level = "ERROR"
    elif "accepted" in line.lower():
        level = "SUCCESS"
    message = line.split("sshd")[-1].strip() if "sshd" in line else line
    return {
        "source": "Auth",
        "timestamp": match.group("timestamp") if match else "",
        "level": level,
        "message": message,
        "raw": line
    }
