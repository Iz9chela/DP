import json
import logging
import asyncio
import random
from typing import Dict, Any, Optional
from backend.config.config import load_config
from backend.llm_clients.ai_client_factory import get_ai_client
from backend.llm_clients.clients import AIClient
from backend.utils.http_error_handler import handle_http_exception
from backend.utils.prompt_parser_validator import extract_json_from_response
from backend.utils.path_utils import resolve_path
from backend.utils.render_prompt import load_and_render_prompt, build_user_message

logger = logging.getLogger(__name__)

class Evaluator:
    """
    Evaluator class for assessing prompts using either human-defined or LLM evaluation criteria.
    """
    def __init__(self, user_query: str, provider: str, model: str,
                 human_evaluation: bool = False, prompts: Dict[str, str] = None,
                 optimized_user_query: str = None) -> None:
        """
        Initialize the Evaluator.

        Parameters:
            user_query (str): The user query to evaluate.
            provider (str): The name of the provider.
            model (str): The model identifier to use for evaluation.
            human_evaluation (bool): Whether to use human-defined evaluation criteria.
            prompts (Dict[str, str]): A dictionary of prompt file paths.
            optimized_user_query (str): Optimized user query for comparison.
        """
        self.user_query = user_query
        self.provider = provider
        self.client: AIClient = get_ai_client(provider)
        self.model = model
        self.human_evaluation:Optional[bool] = human_evaluation
        self.prompts = prompts or {}
        self.evaluation_result: Dict[str, Any] = {}
        self.optimized_user_query: Optional[str] = optimized_user_query
        self.user_verdict_after_comparison: Optional[str] = None
        self.parsed_result_after_comparison: Dict[str, Any] = {}
        self.blind_results: Optional[list] = []
        self.chosen_model_after_blind_results: Optional[str] = None

    async def evaluate(self) -> Dict[str, Any]:
        """
        Evaluate the input prompt using the selected evaluation method.
        """
        prompt_key = "evaluator_human" if self.human_evaluation else "evaluator_llm"
        prompt_path = self.prompts.get(prompt_key)
        if not prompt_path:
            raise ValueError("Prompt path for key '%s' not provided in configuration." % prompt_key)

        prompt_context = {
            "user_query": self.user_query
        }

        rendered_prompt = load_and_render_prompt(prompt_path, prompt_context)

        messages = build_user_message(rendered_prompt)

        logger.info("Calling AI model '%s' for evaluation using '%s' criteria.", self.model, prompt_key)
        response_dict = self.client.call_chat_completion(self.model, messages)
        response_text = response_dict["text"]
        self.evaluation_result = extract_json_from_response(response_text)

        return self.evaluation_result

    async def compare(self) -> Dict[str, Any]:

        messages1 = build_user_message(self.user_query)

        messages2 = build_user_message(self.optimized_user_query)

        logger.info("Calling AI model '%s' for comparison between two queries", self.model)

        response1_dict, response2_dict = await asyncio.gather(
            asyncio.to_thread(self.client.call_chat_completion, self.model, messages1),
            asyncio.to_thread(self.client.call_chat_completion, self.model, messages2)
        )

        resp1_text = response1_dict["text"]
        resp2_text = response2_dict["text"]

        self.parsed_result_after_comparison = { "default_query_response": resp1_text, "optimized_query_response": resp2_text }

        return self.parsed_result_after_comparison

    async def generate_blind_results(
            self,
            user_text: str,
            num_versions: int
    ):
        if num_versions < 2 or num_versions > 4:
            handle_http_exception(400, "num_versions must be between 2 and 4.")


        config = load_config(resolve_path("config.yaml"))
        openai_models = config["models"].get("openai", {})
        claude_models = config["models"].get("claude", {})

        openai_list = [("openai", mval) for mval in openai_models.values()]
        claude_list = [("claude", mval) for mval in claude_models.values()]

        all_models = openai_list + claude_list
        if len(all_models) < num_versions:
            handle_http_exception(500,
                                  "Not enough distinct models available to produce the requested number of versions.")

        chosen_combos = random.sample(all_models, num_versions)

        version_results = []
        for (prov, model_name) in chosen_combos:

            client: AIClient = get_ai_client(prov)

            messages = build_user_message(user_text)
            logger.info("Calling %s model='%s'", prov, model_name)

            try:
                response_dict = client.call_chat_completion(
                    model=model_name,
                    messages=messages
                )
                response_text = response_dict["text"]
            except Exception as e:
                logger.error("Error calling %s model '%s': %s", prov, model_name, e)
                handle_http_exception(500, f"Error calling {prov} model '{model_name}': {e}")

            version_results.append({
                "model": model_name,
                "response": response_text
            })
        self.blind_results = version_results

        return self.blind_results



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

        user_query = input("Enter query to evaluate: ").strip()
        evaluation_method = input("Choose evaluation method ('human' or 'llm'): ").strip().lower()
        if evaluation_method not in ['human', 'llm']:
            print("Invalid choice! Please enter 'human' or 'llm'.")
            sys.exit(1)
        human_evaluation = (evaluation_method == "human")

        optimized_user_query = "Hello amigo!"

        evaluator = Evaluator(
            user_query=user_query,
            provider=provider,
            model=model,
            human_evaluation=human_evaluation,
            prompts=prompts,
            optimized_user_query=optimized_user_query
        )
        result = await evaluator.generate_blind_results("Hello, how are you?", num_versions=2)
        print(json.dumps(result, indent=2, default=str))


    asyncio.run(main())
