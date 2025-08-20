# backend/metrics.py
import re
from collections import Counter
from typing import List, Dict
from log_parser import parse_log_line

def compute_metrics(log_lines: List[str]) -> Dict:
    parsed = [parse_log_line(line) for line in log_lines if line.strip()]

    # Aggregations
    requests_per_minute = Counter()
    error_codes = Counter()
    levels = Counter()
    ip_counter = Counter()

    for log in parsed:
        ts = log.get("timestamp", "")
        level = log.get("level", "INFO")
        ip = log.get("ip", "")
        msg = log.get("message", "")

        # Normalize timestamps to minutes
        if ts:
            key = ts[:16]  # yyyy-mm-dd hh:mm
            requests_per_minute[key] += 1

        if "HTTP" in msg:
            m = re.search(r"\s(\d{3})\s", msg)
            if m:
                error_codes[m.group(1)] += 1

        if level:
            levels[level] += 1
        if ip:
            ip_counter[ip] += 1

    return {
        "requests_per_minute": dict(requests_per_minute),
        "error_codes": dict(error_codes),
        "levels": dict(levels),
        "top_ips": dict(ip_counter.most_common(10)),
    }
