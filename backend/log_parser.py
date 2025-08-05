import re
import json

def parse_apache_log(line):
    # Apache Common Log Format
    apache_pattern = re.compile(
        r'(?P<ip>\S+) \S+ \S+ \[(?P<timestamp>.+?)\] "(?P<request>.+?)" (?P<status>\d{3}) (?P<size>\S+)'
    )
    match = apache_pattern.match(line)
    if match:
        return {
            "log_type": "apache",
            "timestamp": match.group("timestamp"),
            "ip": match.group("ip"),
            "event": match.group("request"),
            "status": match.group("status"),
            "size": match.group("size"),
        }
    return None

def parse_auth_log(line):
    # Example: Nov  3 10:23:01 hostname sshd[12345]: Failed password for user from 192.168.1.100 port 22 ssh2
    auth_pattern = re.compile(
        r'(?P<timestamp>\w{3} +\d+ \d+:\d+:\d+) .*? (?P<event_type>Failed|Accepted) .* from (?P<ip>\d+\.\d+\.\d+\.\d+)'
    )
    match = auth_pattern.search(line)
    if match:
        return {
            "log_type": "auth",
            "timestamp": match.group("timestamp"),
            "ip": match.group("ip"),
            "event": match.group("event_type"),
            "status": "failure" if match.group("event_type") == "Failed" else "success"
        }
    return None

def parse_log_line(line):
    result = parse_apache_log(line)
    if not result:
        result = parse_auth_log(line)
    return result

def parse_log_file(filepath):
    logs = []
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            parsed = parse_log_line(line)
            if parsed:
                logs.append(parsed)
    return logs