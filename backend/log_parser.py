import re
from typing import Dict, Any, Optional

from drain3 import TemplateMiner
from drain3.template_miner_config import TemplateMinerConfig
from drain3.file_persistence import FilePersistence

# -------- Drain3 setup --------
# Persistence so learned templates survive restarts
PERSIST_FILE = "drain3_state.bin"
persistence = FilePersistence(PERSIST_FILE)

config = TemplateMinerConfig()
# If you include a drain3.ini next to this file, it will be picked up here:
try:
    config.load("drain3.ini")
except Exception:
    config.load_default()

template_miner = TemplateMiner(persistence, config)

# -------- Light enrichment regex (best-effort) --------
RX_TIMESTAMP = re.compile(
    r'(?P<ts>\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?'
    r'|\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}'
    r'|\d{2}/\w{3}/\d{4}:\d{2}:\d{2}:\d{2}\s+[+-]\d{4})'
)
RX_IP = re.compile(r'(?P<ip>\b\d{1,3}(?:\.\d{1,3}){3}\b|\b[0-9a-fA-F:]{2,}\b)')
RX_LEVEL = re.compile(r'\b(INFO|WARN|WARNING|ERROR|DEBUG|CRITICAL|FATAL)\b', re.IGNORECASE)

def best_effort_extract(line: str) -> Dict[str, Optional[str]]:
    ts = None
    ip = None
    level = None

    m = RX_TIMESTAMP.search(line)
    if m:
        ts = m.group("ts")

    m = RX_IP.search(line)
    if m:
        ip = m.group("ip")

    m = RX_LEVEL.search(line)
    if m:
        level = m.group(1).upper()

    return {"timestamp": ts or "", "ip": ip or "", "level": level or ""}

def parse_log_line(line: str) -> Dict[str, Any]:
    """
    Universal parser:
    - Uses Drain3 to mine/assign a template + cluster
    - Adds best-effort timestamp, level, ip
    - Always returns a consistent dictionary
    """
    line = (line or "").rstrip("\n")

    d3 = template_miner.add_log_message(line) or {}
    template = d3.get("template_mined")
    cluster_id = d3.get("cluster_id")
    params = d3.get("parameter_list") or d3.get("template_params") or []

    enrich = best_effort_extract(line)

    return {
        "source": "Drain3",
        "template": template or "",
        "cluster_id": cluster_id if cluster_id is not None else -1,
        "parameters": params,
        "message": line,
        "timestamp": enrich["timestamp"],
        "level": enrich["level"] or ("ERROR" if "error" in line.lower() else ("WARN" if "warn" in line.lower() else "")),
        "ip": enrich["ip"]
    }
