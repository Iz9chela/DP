import yaml
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

def load_config(filepath: str) -> Dict[str, Any]:
    """
    Load configuration from a YAML file.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            logger.info("Configuration loaded successfully from %s", filepath)
            return config
    except Exception as e:
        logger.error("Failed to load configuration file %s: %s", filepath, e)
        raise
