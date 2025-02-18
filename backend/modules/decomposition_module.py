import json
import sys
import logging
from typing import Dict
from backend.utils.path_utils import resolve_path
from backend.config.config import load_config
from backend.llm_clients.clients import OpenAIClient, get_openai_api_key
from backend.prompt_parser_validator import extract_json_from_response
from backend.utils.render_prompt import load_and_render_prompt

logger = logging.getLogger(__name__)

class PromptDecomposer:
    def __init__(self, prompt: str, client: OpenAIClient, model: str,
                 automated: bool = False, prompts: Dict[str, str] = None):
        self.prompt = prompt
        self.prompts = prompts
        self.client = client
        self.model = model
        self.automated = automated
        self.result = None  # Store final result

    def decompose_automatic(self) -> dict:
        prompt_key = "decomposition_auto"
        prompt_path = self.prompts.get(prompt_key)
        if not prompt_path:
            raise ValueError(f"Prompt path for key '{prompt_key}' not provided in configuration.")

        system_prompt = load_and_render_prompt(prompt_path)

        user_prompt = f"Decompose the following task: {self.prompt}"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        response_content = self.client.call_chat_completion(self.model, messages)
        self.result = extract_json_from_response(response_content)
        return self.result


    def decompose_interactively(self) -> dict:
        prompt_key = "decomposition_user"
        prompt_path = self.prompts.get(prompt_key)
        if not prompt_path:
            raise ValueError(f"Prompt path for key '{prompt_key}' not provided in configuration.")

        system_prompt = load_and_render_prompt(prompt_path)

        initial_prompt = f"Decompose the following task: {self.prompt}"
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": initial_prompt}
        ]
        
        initial_response = self.client.call_chat_completion(self.model, messages)
        json_result = extract_json_from_response(initial_response)

        if "error" not in json_result:
            self.result = json_result
            return self.result

        print("The model has asked the following clarifying questions:")
        print(initial_response)

        clarifications = input("Please answer the above questions to clarify the task:\n").strip()
        
        if not clarifications:
            print("No clarifications provided. Using the initial response.")
            self.result = json_result
            return self.result

        final_prompt = (
            f"Based on the original request: '{self.prompt}'\n"
            f"and the following clarifications: {clarifications}\n"
            "Now produce the final JSON decomposition strictly following this schema:\n"
            '{ "prompt": string, "subtasks": [array of strings] }.\n'
            "Your final answer must be valid JSON with no extra commentary."
        )

        messages.append({"role": "user", "content": final_prompt})
        final_response = self.client.call_chat_completion(self.model, messages)
        
        json_result = extract_json_from_response(final_response)

        if "error" in json_result:
            print("Final answer did not produce valid JSON. Raw response:")
            print(final_response)

        self.result = json_result
        return self.result



# Example Usage
if __name__ == "__main__":
    # Configure logging

    logging.basicConfig(level=logging.INFO)

    # Load configuration from the YAML file
    CONFIG_PATH = resolve_path("config.yaml")
    config = load_config(CONFIG_PATH)

    # Determine provider from configuration
    provider = config.get("provider", "openai")

    # Retrieve the API key (environment variable takes precedence)
    open_api_key = get_openai_api_key(config)
    if not open_api_key:
        logger.error("No API key provided for provider: %s", provider)
        sys.exit(1)

    # Instantiate the appropriate AI client based on provider
    if provider.lower() == "openai":
        client = OpenAIClient(open_api_key)
    else:
        logger.error("Provider %s not implemented.", provider)
        sys.exit(1)

    # Get the model from configuration
    model = config["models"].get(provider, {}).get("default")
    if not model:
        logger.error("No default model specified for provider %s in configuration.", provider)
        sys.exit(1)

    # Get prompt file paths from configuration
    prompts = config.get("prompts", {})

    # Get user input
    user_input = input("Enter your query: ")

    automated_mode = input("Run in automated mode? (yes/no): ").strip().lower()
    # if automated_mode not in ['yes', 'no']:
    #     print("Invalid choice! Please enter 'yes' or 'no'.")
    #     exit()
    automate = (automated_mode == 'yes')

    decomposer = PromptDecomposer(user_input, client, model, automate, prompts)

    if automated_mode == "yes":
        final_result = decomposer.decompose_automatic()
    else:
        final_result = decomposer.decompose_interactively()

    print("\nFinal Confirmed Breakdown:")
    print(json.dumps(final_result, indent=4))