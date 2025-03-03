from typing import Dict, Any

from backend.config.config import load_config
from backend.utils.http_error_handler import handle_http_exception
from backend.utils.path_utils import resolve_path

config = load_config(resolve_path("config.yaml"))

def validate_required_fields(data: Dict[str, Any], required_fields: list):
    """
    Ensures required fields are present and not empty.
    """
    for field in required_fields:
        if field not in data or not data[field]:
            handle_http_exception(status_code=400, detail=f"'{field}' is required.")

def validate_provider_and_model(provider: str, model: str):
    """
    Validate if the provider and model exist in config.yaml.
    """
    available_providers = config.get("models", {}).keys()

    if provider not in available_providers:
        handle_http_exception(400, f"Invalid provider '{provider}'. Available: {list(available_providers)}")

    available_models = config["models"].get(provider, {}).keys()

    if model not in available_models:
        handle_http_exception(400, f"Invalid model '{model}' for provider '{provider}'. Available: {list(available_models)}")
