import os

import yaml
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
        raise RuntimeError(f"Failed to load configuration file {absolute_path}") from e

def get_api_key(provider: str, config: Dict[str, Any]) -> str:
    """
    Retrieves the API key for the given provider (e.g., 'openai' or 'claude') from the environment or config file.
    """
    provider = provider.lower()
    env_var_name = f"{provider.upper()}_API_KEY"
    api_key = os.getenv(env_var_name) or config.get("api_keys", {}).get(provider)

    if not api_key:
        logger.error("API key for %s not found.", provider)
        raise ValueError(f"{provider} API key not provided.")

    logger.info("Using API key for %s", provider)
    return api_key