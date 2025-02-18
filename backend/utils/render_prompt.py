import os
import logging
from jinja2 import Template
from typing import Dict, Any
from backend.utils.path_utils import resolve_path

logger = logging.getLogger(__name__)

def load_and_render_prompt(prompt_path: str, context: Dict[str, Any] = None) -> str:
        """
        Load a prompt from a file and render it using Jinja2 if a context is provided.
        """
        try:
            # Move up one directory before looking for 'prompts/'
            absolute_path = resolve_path(prompt_path)

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