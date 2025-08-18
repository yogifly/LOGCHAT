from drain3 import TemplateMiner
from drain3.file_persistence import FilePersistence
from drain3.template_miner_config import TemplateMinerConfig

# Persistence (saves learned templates between runs)
persistence = FilePersistence("drain3_state.json")

# Config
config = TemplateMinerConfig()
config.load_default()

# TemplateMiner instance
template_miner = TemplateMiner(persistence, config)

def parse_with_drain(log_line: str):
    """
    Parse a log line using Drain3.
    Returns structured result with cluster_id and template.
    """
    result = template_miner.add_log_message(log_line)
    if not result:
        return None
    
    return {
        "source": "Drain3",
        "cluster_id": result["cluster_id"],
        "template": result["template_mined"],
        "message": log_line
    }
