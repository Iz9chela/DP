import sys
import logging
import os

from backend.config.config import load_config
from backend.services.db import init_db
from backend.llm_clients.clients import OpenAIClient
from backend.modules.evaluator_module import Evaluator
from backend.utils.path_utils import resolve_path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    # 1) Initialize MongoDB
    init_db()

    # 2) Load config
    CONFIG_PATH = resolve_path("config.yaml")
    config = load_config(CONFIG_PATH)

    # 3) Determine provider (assuming openai for now)
    provider = config.get("provider", "openai").lower()

    # 4) API key
    api_key = os.getenv("OPENAI_API_KEY") or config["api_keys"].get("openai")
    if not api_key:
        logger.error("No API key found.")
        sys.exit(1)

    # 5) Create the appropriate client
    if provider == "openai":
        client = OpenAIClient(api_key=api_key)
    else:
        logger.error("Provider '%s' not implemented.", provider)
        sys.exit(1)

    # 6) Determine model and prompts
    model = config["models"][provider]["default"]
    prompts = config["prompts"]

    # 7) Get user input
    input_prompt = input("Enter the prompt to evaluate: ").strip()
    method_choice = input("Choose evaluation method ('human' or 'llm'): ").strip().lower()
    human_evaluation = (method_choice == "human")

    # 8) Evaluate
    evaluator = Evaluator(
        input_prompt=input_prompt,
        client=client,
        model=model,
        prompts=prompts,
        human_evaluation=human_evaluation
    )

    result = evaluator.evaluate()
    logger.info("Evaluation stored in MongoDB with data:\n%s", result)

if __name__ == "__main__":
    main()
