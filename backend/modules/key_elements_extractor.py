import json
import logging
import sys
import asyncio
from backend.llm_clients.clients import OpenAIClient, get_api_key, AnthropicClient
from backend.config.config import load_config
from backend.utils.path_utils import resolve_path
from backend.utils.prompt_parser_validator import extract_json_from_response
from backend.utils.render_prompt import load_and_render_prompt, build_user_message

logger = logging.getLogger(__name__)


class KeyExtractor:
    """
    KeyExtractor module for extracting specific key elements from a user request.
    Expected JSON output:
    {
      "goal": "<extracted goal or an empty string if none>",
      "context": "<extracted context or an empty string if none>",
      "instructions": "<extracted instructions or an empty string if none>",
      "constraints": "<extracted constraints or an empty string if none>",
      "style": "<extracted style or an empty string if none>",
      "examples": [<list of extracted examples, or an empty list if none>]
    }
    """

    def __init__(self, user_query: str, client: OpenAIClient, model: str, prompts: dict):
        self.user_query = user_query
        self.client = client
        self.model = model
        self.prompts = prompts
        self.result = {}

    def extract_key_elements(self) -> dict:
        prompt_key = "key_extraction"
        prompt_path = self.prompts.get(prompt_key)
        if not prompt_path:
            raise ValueError(f"Prompt path for key '{prompt_key}' not provided in configuration.")

        prompt_context = {
            "user_query": self.user_query
        }

        rendered_prompt = load_and_render_prompt(prompt_path, prompt_context)

        messages = build_user_message(rendered_prompt)

        logger.info("Calling AI model '%s' for extraction key elements.", self.model)
        response_content = self.client.call_chat_completion(self.model, messages)
        self.result = extract_json_from_response(response_content)
        return self.result


if __name__ == "__main__":
    async def main():
        # Configure logging
        logging.basicConfig(level=logging.INFO)

        # Load configuration from YAML file
        CONFIG_PATH = resolve_path("config.yaml")
        config = load_config(CONFIG_PATH)

        # Determine provider from configuration
        provider = config.get("provider", "openai")

        # Retrieve the API key (environment variable takes precedence)
        open_api_key = get_api_key(provider, config)
        if not open_api_key:
            logger.error("No API key provided for provider: %s", provider)
            sys.exit(1)

        # Instantiate the appropriate AI client based on provider
        if provider.lower() == "openai":
            client = OpenAIClient(open_api_key)
        elif provider.lower() == "claude":
            client = AnthropicClient(open_api_key)
        else:
            logger.error("Provider %s not implemented.", provider)
            sys.exit(1)

        # Get the model from configuration; for example, use the key 'gpt-4o'
        model = config["models"].get(provider, {}).get("default")
        if not model:
            logger.error("No default model specified for provider %s in configuration.", provider)
            sys.exit(1)

        # Get prompt file paths from configuration (including our key_extraction prompt)
        prompts = config.get("prompts", {})

        # Get the user query for which key elements need to be extracted
        user_query = input("Enter your query: ").strip()

        extractor = KeyExtractor(user_query=user_query, client=client, model=model, prompts=prompts)
        extracted_keys = extractor.extract_key_elements()
        print(json.dumps(extracted_keys, indent=4))


    asyncio.run(main())
