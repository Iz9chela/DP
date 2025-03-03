import logging
from backend.config.config import load_config
from backend.llm_clients.clients import OpenAIClient, AnthropicClient
from backend.utils.path_utils import resolve_path

logger = logging.getLogger(__name__)


def get_ai_client(provider: str):
    """
    Returns an AI client instance based on the provider.
    """
    config = load_config(resolve_path("config.yaml"))
    api_key = config["api_keys"].get(provider)

    if not api_key:
        logger.error("API key for %s not found.", provider)
        raise ValueError(f"API key for {provider} not provided.")

    if provider.lower() == "openai":
        return OpenAIClient(api_key=api_key)
    elif provider.lower() == "claude":
        return AnthropicClient(api_key=api_key)
    else:
        logger.error("Unsupported AI provider: %s", provider)
        raise ValueError(f"Unsupported AI provider: {provider}")
