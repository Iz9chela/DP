import logging
import sys
from typing import Dict, Any, Optional

from backend.config.config import load_config
from backend.llm_clients.ai_client_factory import get_ai_client
from backend.modules.evaluator_module import Evaluator
from backend.utils.path_utils import resolve_path
from backend.utils.render_prompt import load_and_render_prompt, build_user_message
from backend.utils.prompt_parser_validator import extract_json_from_response

logger = logging.getLogger(__name__)


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

        # Tracking
        self.final_optimized_query: str = ""
        self.optimized_output: Dict[str, Any] = {}
        self.is_optimizing: bool = False  # Simple concurrency lock

    async def evaluate_query(self, use_human_eval: bool, query_text: str) -> Dict[str, Any]:
        """
        Evaluate the given query using the Evaluator class. Returns a dict that includes:
        {
            "prompt_rating": <int>,
            "reasons": [<string>, ...]
        }

        The logic for storing in DB is inside Evaluator -> create_prompt_evaluation().
        Adjust as needed.
        """
        # Decide which evaluator prompt to use (human or LLM). We'll assume "llm" here.
        # If you need a user toggle, parameterize it.
        evaluator = Evaluator(
            prompt=query_text,
            provider=self.provider,
            model=self.model,
            human_evaluation=use_human_eval,
            prompts=self.prompts
        )
        logger.info("Evaluating query with the Evaluator module.")

        evaluation_result = await evaluator.evaluate()
        return evaluation_result

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

            # Prepare context for the prompt template
            prompt_context = {
                "user_query": self.user_query,
                "number_of_iterations": iters,
                "number_of_versions": iters
            }

            # Render the chosen technique's prompt
            rendered_prompt = load_and_render_prompt(technique_prompt_path, prompt_context)
            messages = build_user_message(rendered_prompt)

            logger.info(f"Optimizing user query with technique '{selected_technique}'...")
            # Call the LLM
            response_content = self.client.call_chat_completion(
                model=self.model,
                messages=messages
                # You can expand self.hyperparams if your LLM client supports them, e.g.:
                # **self.hyperparams
            )
            self.optimized_output = extract_json_from_response(response_content)

            # Depending on the prompt technique, the "optimized" query might appear in different places.
            # For instance, CoT has "Optimized_Query" in a single JSON object,
            # while SC might have multiple versions then a final "Optimized_Query" key.
            # We'll handle a few known patterns as examples:

            if selected_technique in ["CoT", "SC"]:
                self.final_optimized_query = self.optimized_output.get("Optimized_Query", "")
            elif selected_technique == "CoD":
                if isinstance(self.optimized_output, list) and len(self.optimized_output) > 0:
                    last_item = self.optimized_output[-1]
                    self.final_optimized_query = last_item.get("Optimized_Query", "")
            elif selected_technique == "PC":
                if isinstance(self.optimized_output, list):
                    last_item = self.optimized_output[-1]
                    self.final_optimized_query = last_item.get("Optimized_Query", "")
            elif selected_technique == "ReAct":
                if isinstance(self.optimized_output, list):
                    # The last element might be {"Optimized_Query": "..."}
                    if len(self.optimized_output) > 0 and "Optimized_Query" in self.optimized_output[-1]:
                        self.final_optimized_query = self.optimized_output[-1]["Optimized_Query"]

            # If the technique doesn't place the final query in a standard key, handle accordingly.

        finally:
            self.is_optimizing = False  # Unlock

        return self.optimized_output

    async def refine_and_evaluate(self, use_human_eval: bool, technique: str) -> Dict[str, Any]:
        """
        High-level orchestration:
          1. Evaluate the initial user query.
          2. Run the chosen optimization technique.
          3. Re-evaluate the final optimized query.
          4. Return all relevant info (including DB records if needed).
        """

        logger.info("Evaluating the original user query before optimization...")
        initial_eval = await self.evaluate_query(use_human_eval, self.user_query)

        # 2. Perform the optimization with the chosen technique
        logger.info(f"Optimizing user query with technique '{technique}'...")
        self.optimize_query(selected_technique=technique)

        # 3. Re-evaluate the newly optimized query
        logger.info("Evaluating the final optimized query...")
        final_eval = {}
        if self.final_optimized_query:
            final_eval = await self.evaluate_query(use_human_eval, self.final_optimized_query)

        # You can store these evaluations in MongoDB or any DB you prefer.
        # For instance:
        #   db.my_collection.insert_one({
        #       "original_query": self.user_query,
        #       "initial_eval": initial_eval["parsed_result"],
        #       "optimized_query": self.final_optimized_query,
        #       "final_eval": final_eval["parsed_result"]
        #   })

        return {
            "original_query": self.user_query,
            "initial_evaluation": initial_eval.get("parsed_result", {}),
            "technique_used": technique,
            "optimized_output": self.optimized_output,
            "final_optimized_query": self.final_optimized_query,
            "final_evaluation": final_eval.get("parsed_result", {})
        }


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
    model = config["models"].get(provider, {}).get("default")
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
    print(res)
    # Pick one technique among ["CoT", "SC", "CoD", "PC", "ReAct"]
    # chosen_technique = "CoT"
    # human_evaluation = True

    # Because we use async evaluation, we run our refine_and_evaluate inside an event loop.
    # async def run_refinement():
    #     result = await refinement_module.refine_and_evaluate(human_evaluation, chosen_technique)
    #     print("=== Final Result ===")
    #     print(result)
    #
    # asyncio.run(run_refinement())
