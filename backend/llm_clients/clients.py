import time
import logging
import openai
import os
from abc import ABC, abstractmethod
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

def get_openai_api_key(config: Dict[str, Any]) -> str:
    """
    Retrieve the OpenAI API key from an environment variable or configuration.

    Parameters:
        config (Dict[str, Any]): The configuration dictionary.

    Returns:
        str: The OpenAI API key.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        logger.info("Using API key from environment variable.")
        return api_key
    elif "api_keys" in config and "openai" in config["api_keys"]:
        logger.info("Using API key from configuration file.")
        return config["api_keys"]["openai"]
    else:
        logger.error("OpenAI API key not found in environment variables or configuration.")
        raise ValueError("OpenAI API key not provided.")

class AIClient(ABC):
    @abstractmethod
    def call_chat_completion(self, model: str, messages: List[Dict[str, str]]) -> str:
        """
        Abstract method to call a chat completion API.
        """
        pass

class OpenAIClient(AIClient):
    def __init__(self, api_key: str, max_retries: int = 3, backoff_factor: float = 1.0):
        """
        Initialize the OpenAI client with an API key and retry settings.
        """
        self.client = openai.OpenAI(api_key=api_key)
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor

    def call_chat_completion(self, model: str, messages: List[Dict[str, str]]) -> str:
        """
        Call the OpenAI chat completion API with retry logic.
        """
        attempt = 0
        while attempt < self.max_retries:
            try:
                response = self.client.chat.completions.create(
                    model=model,
                    max_tokens=1024,
                    temperature=0.0,
                    messages=messages
                )
                start_time = time.time()
                result = response.choices[0].message.content.strip()
                elapsed_time = time.time() - start_time
                logger.info("Received response from AI model. AI API call took %.2f seconds", elapsed_time)
                return result
            except Exception as e:
                attempt += 1
                sleep_time = self.backoff_factor * (2 ** (attempt - 1))
                logger.error("Error calling OpenAI API on attempt %d: %s. Retrying in %f seconds.", attempt, e, sleep_time)
                time.sleep(sleep_time)
        raise Exception("Max retries exceeded for OpenAI API call.")

# Additional client implementations (e.g., for Claude, BERT) can be added here.
