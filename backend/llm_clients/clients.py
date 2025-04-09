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

    def call_chat_completion(self, model: str, messages: List[Dict[str, str]]) -> Dict[str, Any]:
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
                    params["max_tokens"] = 4096
                response = self.client.chat.completions.create(**params)
                elapsed_time = time.time() - start_time
                result_text = response.choices[0].message.content.strip()
                usage_obj = response.usage
                tokens_spent = usage_obj.total_tokens if usage_obj else None
                usage_data = {
                    "tokens_spent": tokens_spent,
                    "time_in_seconds": round(elapsed_time, 3)
                }
                logger.info("Received response from AI model. AI API call took %.2f seconds", elapsed_time)
                return {
                    "text": result_text,
                    "usage": usage_data
                }
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

    def call_chat_completion(self, model: str, messages: List[Dict[str, str]]) -> Dict[str, Any]:
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
                    max_tokens=4096,
                    temperature=0.0
                )
                elapsed_time = time.time() - start_time
                logger.info("Received response from Anthropic. API call took %.2f seconds", elapsed_time)

                result_text = response.content[0].text.strip() if response.content else ""

                prompt_word_count = sum(len(msg["content"].split()) for msg in messages)
                prompt_tokens = int(prompt_word_count * 1.33)
                completion_word_count = len(result_text.split())
                completion_tokens = int(completion_word_count * 1.33)
                tokens_spent = prompt_tokens + completion_tokens

                usage_data = {
                    "tokens_spent": tokens_spent,
                    "time_in_seconds": round(elapsed_time, 3)
                }

                return {
                    "text": result_text,
                    "usage": usage_data
                }

            except Exception as e:
                attempt += 1
                sleep_time = self.backoff_factor * (2 ** (attempt - 1))
                logger.error("Error calling Anthropic API on attempt %d: %s. Retrying in %f seconds.",
                             attempt, e, sleep_time)
                time.sleep(sleep_time)

        raise Exception("Max retries exceeded for Anthropic (Claude) API call.")
