import json
import logging
import asyncio
from typing import Dict, Any
from backend.config.config import load_config
from backend.llm_clients.ai_client_factory import get_ai_client
from backend.llm_clients.clients import AIClient
from backend.utils.prompt_parser_validator import extract_json_from_response
from backend.utils.path_utils import resolve_path
from backend.utils.render_prompt import load_and_render_prompt, build_user_message

logger = logging.getLogger(__name__)

class Evaluator:
    """
    Evaluator class for assessing prompts using either human-defined or LLM evaluation criteria.
    """
    def __init__(self, prompt: str, provider: str, model: str,
                 human_evaluation: bool = False, prompts: Dict[str, str] = None) -> None:
        """
        Initialize the Evaluator.

        Parameters:
            prompt (str): The prompt to evaluate.
            provider (str): The name of the provider.
            model (str): The model identifier to use for evaluation.
            human_evaluation (bool): Whether to use human-defined evaluation criteria.
            prompts (Dict[str, str]): A dictionary of prompt file paths.
        """
        self.prompt = prompt
        self.provider = provider
        self.client: AIClient = get_ai_client(provider)
        self.model = model
        self.human_evaluation = human_evaluation
        self.prompts = prompts or {}
        self.result: Dict[str, Any] = {}

    async def evaluate(self) -> Dict[str, Any]:
        """
        Evaluate the input prompt using the selected evaluation method.
        """
        prompt_key = "evaluator_human" if self.human_evaluation else "evaluator_llm"
        prompt_path = self.prompts.get(prompt_key)
        if not prompt_path:
            raise ValueError("Prompt path for key '%s' not provided in configuration." % prompt_key)

        prompt_context = {
            "user_query": self.prompt
        }

        rendered_prompt = load_and_render_prompt(prompt_path, prompt_context)

        messages = build_user_message(rendered_prompt)

        logger.info("Calling AI model '%s' for evaluation using '%s' criteria.", self.model, prompt_key)
        response_content = self.client.call_chat_completion(self.model, messages)
        self.result = extract_json_from_response(response_content)

        return self.result


if __name__ == "__main__":
    async def main():
        import sys
        logging.basicConfig(level=logging.INFO)

        config = load_config(resolve_path("config.yaml"))

        provider = config.get("provider", "openai")

        model = config["models"].get(provider, {}).get("gpt-3.5-turbo")
        if not model:
            logger.error("No default model specified for provider %s in configuration.", provider)
            sys.exit(1)

        prompts = config.get("prompts", {})

        prompt = input("Enter prompt to evaluate: ").strip()
        evaluation_method = input("Choose evaluation method ('human' or 'llm'): ").strip().lower()
        if evaluation_method not in ['human', 'llm']:
            print("Invalid choice! Please enter 'human' or 'llm'.")
            sys.exit(1)
        human_evaluation = (evaluation_method == "human")

        evaluator = Evaluator(
            prompt=prompt,
            provider=provider,
            model=model,
            human_evaluation=human_evaluation,
            prompts=prompts
        )
        result = await evaluator.evaluate()
        print(json.dumps(result, indent=2, default=str))


    asyncio.run(main())
