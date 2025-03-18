import time
import logging

import anthropic
import openai
from abc import ABC, abstractmethod
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


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
        params = {
            "model": model,
            "temperature": 0.0,
            "messages": messages
        }
        attempt = 0
        while attempt < self.max_retries:
            try:
                start_time = time.time()
                if model == "o3-mini":
                    params["max_completion_tokens"] = 4096
                    del params["temperature"]
                else:
                    params["max_tokens"] = 2048
                response = self.client.chat.completions.create(**params)
                result = response.choices[0].message.content.strip()
                elapsed_time = time.time() - start_time
                logger.info("Received response from AI model. AI API call took %.2f seconds", elapsed_time)
                return result
            except Exception as e:
                attempt += 1
                sleep_time = self.backoff_factor * (2 ** (attempt - 1))
                logger.error("Error calling OpenAI API on attempt %d: %s. Retrying in %f seconds.", attempt, e,
                             sleep_time)
                time.sleep(sleep_time)
        raise Exception("Max retries exceeded for OpenAI API call.")


class AnthropicClient(AIClient):
    def __init__(self, api_key: str, max_retries: int = 3, backoff_factor: float = 1.0):
        """
        Initialize the Anthropic client with an API key and retry settings.
        """
        self.client = anthropic.Client(api_key=api_key)
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor

    def call_chat_completion(self, model: str, messages: List[Dict[str, str]]) -> str:
        """
        Calls the Anthropic Claude API in a chat-like manner,
        converting 'messages' (role/content) into the format
        Claude expects (HUMAN_PROMPT and AI_PROMPT).
        """

        attempt = 0
        while attempt < self.max_retries:
            try:
                start_time = time.time()
                response = self.client.messages.create(
                    model=model,
                    messages=messages,
                    max_tokens=2048,
                    temperature=0.0
                )
                elapsed_time = time.time() - start_time
                logger.info("Received response from Anthropic. API call took %.2f seconds", elapsed_time)

                return response.content[0].text

            except Exception as e:
                attempt += 1
                sleep_time = self.backoff_factor * (2 ** (attempt - 1))
                logger.error("Error calling Anthropic API on attempt %d: %s. Retrying in %f seconds.",
                             attempt, e, sleep_time)
                time.sleep(sleep_time)

        raise Exception("Max retries exceeded for Anthropic (Claude) API call.")
