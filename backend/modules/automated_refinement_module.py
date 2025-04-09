import logging
import sys
import random
from typing import Dict, Any, Optional

from backend.config.config import load_config
from backend.llm_clients.ai_client_factory import get_ai_client
from backend.utils.path_utils import resolve_path
from backend.utils.render_prompt import load_and_render_prompt, build_user_message
from backend.utils.prompt_parser_validator import extract_json_from_response

logger = logging.getLogger(__name__)

emotional_stimuli_list = [
    "Write your answer and give me a confidence score between 0-1 for your answer.",
    "This is very important to my career.",
    "You'd better be sure.",
    "Stay focused and dedicated to your goals. Your consistent efforts will lead to outstanding achievements.",
    "Take pride in your work and give it your best. Your commitment to excellence sets you apart.",
    "Remember that progress is made one step at a time. Stay determined and keep moving forward.",
    "Are you sure?",
    "Are you sure that's your final answer? It might be worth taking another look."
]

class AutomatedRefinementModule:
    """
    A module to refine a user query using one of 5 available optimization techniques:
    (CoT, SC, CoD, PromptChain, ReAct).

    Attributes:
        user_query (str): The original query from the user.
        provider (str): The provider from the user.
        model (str): The model identifier to use.
        prompts (dict): Mapping of technique names -> their prompt template paths.
        max_iterations (int): Maximum number of optimization iterations (default: 3).
        hyperparams (dict): Hyperparameters for LLM calls.
        is_optimizing (bool): Simple lock preventing parallel optimization.
    """

    def __init__(
        self,
        user_query: str,
        provider: str,
        model: str,
        prompts: Dict[str, str],
        max_iterations: int = 3,
        hyperparams: Optional[dict] = None
    ):
        self.user_query = user_query
        self.provider = provider
        self.client = get_ai_client(provider)
        self.model = model
        self.prompts = prompts
        self.max_iterations = max_iterations
        self.hyperparams = hyperparams or {
            "max_tokens": 1024,
            "temperature": 0.7,
            "top_p": 1.0,
            "frequency_penalty": 0,
            "presence_penalty": 0,
            "stop_sequences": []
        }
        self.emotional_stimuli = emotional_stimuli_list
        self.expert_persona_text: Optional[str] = f"You are {self.expert_finder()} with extensive experience."
        self.emotional_stimuli_text: Optional[str] = random.choice(self.emotional_stimuli)

        # Tracking
        self.final_optimized_query: str = ""
        self.raw_output: Dict[str, Any] = {}
        self.is_optimizing: bool = False  # Simple concurrency lock
        self.is_expert_present: bool = False

    def expert_finder(self):
        full_expert_finder_path = self.prompts.get("expert_finder")
        prompt_context = {
            "user_query": self.user_query,
        }

        # Render the chosen technique's prompt
        rendered_prompt = load_and_render_prompt(full_expert_finder_path, prompt_context)
        messages = build_user_message(rendered_prompt)

        logger.info(f"Finding expert based on query: {self.user_query}  ...")

        response_dict = self.client.call_chat_completion(self.model, messages)
        response_text = response_dict["text"]

        content = extract_json_from_response(response_text)

        if isinstance(content, dict) and "Expert" in content:
            self.is_expert_present = True
            return content["Expert"]
        else:
            self.is_expert_present = False
            return None

    def optimize_query(
        self, selected_technique: str, iterations: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Optimize the user query using the specified technique over a number of iterations.
        Each technique has its own prompt template and output structure.

        Returns the raw JSON extracted from the LLM response.
        """
        if self.is_optimizing:
            raise RuntimeError("An optimization process is already in progress. Please wait.")

        self.is_optimizing = True
        try:
            technique_prompt_path = self.prompts.get(selected_technique)
            if not technique_prompt_path:
                raise ValueError(f"Technique '{selected_technique}' is not supported.")

            iters = iterations or self.max_iterations

            prompt_context = {
                "user_query": self.user_query,
                "number_of_iterations": iters,
                "number_of_versions": iters
            }

            rendered_prompt = load_and_render_prompt(technique_prompt_path, prompt_context)
            messages = build_user_message(rendered_prompt)

            logger.info(f"Optimizing user query with technique '{selected_technique}'...")

            response_dict = self.client.call_chat_completion(
                model=self.model,
                messages=messages
            )
            response_text = response_dict["text"]
            usage_info = response_dict["usage"]
            self.raw_output = extract_json_from_response(response_text)
            self.raw_output["usage"] = usage_info

            if selected_technique in ["CoT", "SC", "ReAct", "PC", "CoD", "SC_ReAct"]:
                self.final_optimized_query = self.raw_output.get("Final_Optimized_Query", "")

        finally:
            self.is_optimizing = False

        return self.raw_output


if __name__ == "__main__":
    """
    Example usage when running this module directly.
    Make sure your config.yaml has the required structure for 'provider',
    API keys, and prompt file paths for each technique.
    """
    logging.basicConfig(level=logging.INFO)

    config = load_config(resolve_path("config.yaml"))

    provider = config.get("provider", "openai")

    client = get_ai_client(provider)

    # Example model
    model = config["models"].get(provider, {}).get("gpt-3.5-turbo")
    if not model:
        logger.error("No default model specified for provider %s in configuration.", provider)
        sys.exit(1)

    prompts = config.get("prompts", {})

    user_query = input("Enter your query: ")
    refinement_module = AutomatedRefinementModule(
        user_query=user_query,
        provider=provider,
        model=model,
        prompts=prompts
    )

    res = refinement_module.optimize_query(selected_technique="CoT", iterations=3)

    print("=== Final Result ===")
    print("STIMULI >> ", refinement_module.emotional_stimuli_text)
    print("Expert >>", refinement_module.expert_persona_text)
    print(res)
