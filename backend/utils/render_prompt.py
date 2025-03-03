import os
import logging
from jinja2 import Template
from typing import Dict, Any
from backend.utils.path_utils import resolve_path

logger = logging.getLogger(__name__)

def load_prompt(prompt_path: str) -> str:
    """
    Load a prompt from a file.
    """
    absolute_path = resolve_path(prompt_path)

    if not os.path.exists(absolute_path):
        logger.error("Prompt file not found: %s", absolute_path)
        raise FileNotFoundError(f"Prompt file not found: {absolute_path}")

    with open(absolute_path, "r", encoding="utf-8") as f:
        return f.read().strip()

def render_prompt(prompt_text: str, context: Dict[str, Any] = None) -> str:
    """
    Render a prompt using Jinja2 with the provided context.
    """
    if context:
        template = Template(prompt_text)
        return template.render(**context)
    return prompt_text

def load_and_render_prompt(prompt_path: str, context: Dict[str, Any] = None) -> str:
    """
    Load and render a prompt from a file.
    """
    prompt_text = load_prompt(prompt_path)
    return render_prompt(prompt_text, context)

def build_user_message(rendered_prompt: str) -> list:
    """
    Wraps the rendered prompt in a standardized message format.
    """
    return [{"role": "user", "content": rendered_prompt}]