import os
import sys
import json
import logging
from typing import Dict, Any
from jinja2 import Template
from backend.config.config import load_config
from backend.llm_clients.clients import AIClient, OpenAIClient, get_openai_api_key
from backend.prompt_parser_validator import extract_json_from_response

logger = logging.getLogger(__name__)

class Evaluator:
    """
    Evaluator class for assessing prompts using either human-defined or LLM evaluation criteria.
    """
    def __init__(self, input_prompt: str, client: AIClient, model: str,
                 human_evaluation: bool = False, prompts: Dict[str, str] = None) -> None:
        """
        Initialize the Evaluator.

        Parameters:
            input_prompt (str): The prompt to evaluate.
            client (AIClient): An instance of an AI client (e.g., OpenAIClient).
            model (str): The model identifier to use for evaluation.
            human_evaluation (bool): Whether to use human-defined evaluation criteria.
            prompts (Dict[str, str]): A dictionary of prompt file paths.
        """
        self.input_prompt = input_prompt
        self.client = client
        self.model = model
        self.human_evaluation = human_evaluation
        self.prompts = prompts or {}
        self.result: Dict[str, Any] = {}

    def load_and_render_prompt(self, prompt_path: str, context: Dict[str, Any] = None) -> str:
        """
        Load a prompt from a file and render it using Jinja2 if a context is provided.
        """
        try:
            # Move up one directory before looking for 'prompts/'
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            absolute_path = os.path.join(base_dir, prompt_path)

            if not os.path.exists(absolute_path):
                raise FileNotFoundError(f"Prompt file not found: {absolute_path}")

            with open(absolute_path, "r", encoding="utf-8") as f:
                prompt_text = f.read()
            if context:
                template = Template(prompt_text)
                rendered = template.render(**context)
                logger.info("Rendered prompt from %s with context.", prompt_path)
                return rendered
            logger.info("Loaded prompt from %s.", prompt_path)
            return prompt_text.strip()
        except Exception as e:
            logger.error("Failed to load or render prompt from %s: %s", prompt_path, e)
            raise

    def evaluate(self) -> Dict[str, Any]:
        """
        Evaluate the input prompt using the selected evaluation method.
        """
        prompt_key = "evaluator_human" if self.human_evaluation else "evaluator_llm"
        prompt_path = self.prompts.get(prompt_key)
        if not prompt_path:
            raise ValueError("Prompt path for key '%s' not provided in configuration." % prompt_key)

        system_prompt = self.load_and_render_prompt(prompt_path)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": self.input_prompt}
        ]
        logger.info("Calling AI model '%s' for evaluation using '%s' criteria.", self.model, prompt_key)
        response_content = self.client.call_chat_completion(self.model, messages)
        self.result = extract_json_from_response(response_content)
        return self.result


if __name__ == "__main__":
    # Configure logging

    logging.basicConfig(level=logging.INFO)

    # Load configuration from the YAML file
    config = load_config("../config.yaml")

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
    model = config["models"].get(provider, {}).get("gpt-4o")
    if not model:
        logger.error("No default model specified for provider %s in configuration.", provider)
        sys.exit(1)

    # Get prompt file paths from configuration
    prompts = config.get("prompts", {})

    # Get the prompt to evaluate and the evaluation method from the user
    input_prompt = input("Enter prompt to evaluate: ").strip()
    evaluation_method = input("Choose evaluation method ('human' or 'llm'): ").strip().lower()
    if evaluation_method not in ['human', 'llm']:
        print("Invalid choice! Please enter 'human' or 'llm'.")
        exit()
    human_evaluation = (evaluation_method == "human")

    evaluator = Evaluator(
        input_prompt=input_prompt,
        client=client,
        model=model,
        human_evaluation=human_evaluation,
        prompts=prompts
    )
    result = evaluator.evaluate()
    print(json.dumps(result, indent=2))
