import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Body, Depends

from backend.db.data.optimized_prompt_data import OptimizedPrompt
from backend.db.service.optimization_prompt_service import (
    create_optimized_prompt,
    get_optimized_prompt,
    list_optimized_prompts,
    update_optimized_prompt,
    delete_optimized_prompt
)
from backend.utils.auth_dependency import get_current_user
from backend.utils.http_error_handler import handle_generic_exception

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/", response_model=OptimizedPrompt)
async def create_optimized_prompt_endpoint(
        prompt_data: Dict[str, Any] = Body(
        ...,
        examples=[{
            "user_query": "Optimize my resume summary",
            "provider": "openai",
            "model": "gpt-3.5-turbo",
            "technique": "CoT",
            "number_of_iterations": 3
        }]
    ),
        user_id: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """Create a new OptimizedPrompt document."""
    try:
        return await create_optimized_prompt(prompt_data)
    except Exception as e:
        handle_generic_exception(e)

@router.get("/{prompt_id}", response_model=OptimizedPrompt)
async def get_optimized_prompt_endpoint(prompt_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve an OptimizedPrompt by ID."""
    try:
        return await get_optimized_prompt(prompt_id)
    except Exception as e:
        handle_generic_exception(e)

@router.get("/", response_model=List[OptimizedPrompt])
async def list_optimized_prompts_endpoint(limit: int = 10) -> List[Dict[str, Any]]:
    """List optimized prompts, excluding deleted ones."""
    try:
        return await list_optimized_prompts(limit)
    except Exception as e:
        handle_generic_exception(e)

@router.put("/{prompt_id}", response_model=OptimizedPrompt)
async def update_optimized_prompt_endpoint(
        prompt_id: str,
        update_data: Dict[str, Any] = Body(
        ...,
        examples=[{
            "final_optimized_query": "Updated query after refinement",
            "optimized_output": {"iterations": [{"step": 1, "query": "Refined version"}]}
        }]
    ),
        user_id: str = Depends(get_current_user)
) -> Optional[Dict[str, Any]]:
    """Update an existing optimized prompt document by ID."""
    try:
        return await update_optimized_prompt(prompt_id, update_data)
    except Exception as e:
        handle_generic_exception(e)

@router.delete("/{prompt_id}")
async def delete_optimized_prompt_endpoint(prompt_id: str,
        user_id: str = Depends(get_current_user)) -> bool:
    """Soft-delete an optimized prompt by setting is_deleted=True."""
    try:
        return await delete_optimized_prompt(prompt_id)
    except Exception as e:
        handle_generic_exception(e)
