import yaml
import os
import logging
from typing import Dict, Any
from backend.utils.path_utils import resolve_path

logger = logging.getLogger(__name__)

def load_config(filepath: str) -> Dict[str, Any]:
    """
    Load configuration from a YAML file.
    """
    absolute_path = resolve_path(filepath)

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            logger.info("Configuration loaded successfully from %s", absolute_path)
            return config
    except Exception as e:
        logger.error("Failed to load configuration file %s: %s", absolute_path, e)
        raise

def get_mongo_uri(config: Dict[str, Any]) -> str:
    return os.getenv("MONGO_URI") or config["database"].get("uri", "mongodb+srv://{user}:{pass}@dp-database.fczwf.mongodb.net/?retryWrites=true&w=majority&appName=DP-Database")

def get_db_name(config: Dict[str, Any]) -> str:
    return os.getenv("MONGO_DB_NAME") or config["database"].get("database_name", "dp_database")
