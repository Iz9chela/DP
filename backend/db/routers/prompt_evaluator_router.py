import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Body, Depends

from backend.db.data.prompt_evaluator_data import PromptEvaluator
from backend.db.db import get_database
from backend.db.service.prompt_evaluation_service import create_prompt_evaluation, get_prompt_evaluation, \
    list_prompt_evaluations, update_prompt_evaluation, delete_prompt_evaluation, create_comparison
from backend.utils.auth_dependency import get_current_user

from backend.utils.http_error_handler import handle_generic_exception

logger = logging.getLogger(__name__)
router = APIRouter()

db = get_database()
@router.post("/", response_model=PromptEvaluator)
async def create_evaluation_endpoint(
        evaluation_data: Dict[str, Any] = Body(
        ...,
        examples=[{
            "prompt": "Write a Python function to reverse a string",
            "provider" : "openai",
            "model": "gpt-3.5-turbo",
            "evaluation_method": "human",
        }]
        ),
        user_id: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Inserts a new document into the 'prompt_evaluator' collection.
    Returns the inserted document with 'id' as a string.
    """
    try:
       return await create_prompt_evaluation(evaluation_data)
    except Exception as e:
        handle_generic_exception(e)

@router.post("/compare", response_model=PromptEvaluator)
async def create_comparison_endpoint(
        evaluation_data: Dict[str, Any] = Body(
        ...,
        examples=[{
            "prompt": "Write a Python function to reverse a string",
            "provider" : "openai",
            "model": "gpt-3.5-turbo",
            "optimized_prompt": "Write a Python enhanced version of function to reverse a string",
        }]
        ),
        user_id: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Inserts a new document into the 'prompt_evaluator' collection.
    Returns the inserted document with 'id' as a string.
    """
    try:
       return await create_comparison(evaluation_data)
    except Exception as e:
        handle_generic_exception(e)

@router.get("/{evaluation_id}", response_model=PromptEvaluator)
async def get_evaluation_endpoint(
        evaluation_id: str,
) -> Optional[Dict[str, Any]]:
    """
    Retrieves a document by its id (string) from the 'prompt_evaluator' collection.
    Excludes any documents marked as deleted.
    """
    try:
        doc = await get_prompt_evaluation(evaluation_id)
        return doc
    except Exception as e:
        handle_generic_exception(e)


@router.get("/", response_model=List[PromptEvaluator])
async def list_evaluation_endpoint(
        limit: int = 10,
) -> List[Dict[str, Any]]:
    """
    Returns a list of evaluations, excluding those marked as deleted.
    """
    try:
        docs = await list_prompt_evaluations(limit)
        return docs
    except Exception as e:
        handle_generic_exception(e)


@router.put("/{evaluation_id}", response_model=PromptEvaluator)
async def update_evaluation_endpoint(
        evaluation_id: str,
        update_data: Dict[str, Any] = Body(
        ...,
        examples=[{
            "model": "gpt-4o-mini",
            "parsed_result": {
                "prompt_rating": 6,
                "reasons": ["Improved clarity", "Better structure"]
            }
        }]
    ),
        user_id: str = Depends(get_current_user)
) -> Optional[Dict[str, Any]]:
    """
    Updates an existing evaluation document by id, returning the updated document.
    """
    try:
        updated_doc = await update_prompt_evaluation(evaluation_id, update_data)
        return updated_doc
    except Exception as e:
        handle_generic_exception(e)


@router.delete("/{evaluation_id}")
async def delete_evaluation_endpoint(
        evaluation_id: str,
        user_id: str = Depends(get_current_user)
) -> bool:
    """
    Soft-deletes a document by setting is_deleted=True.
    Returns True if the document was updated.
    """
    try:
        result = await delete_prompt_evaluation(evaluation_id)
        return result
    except Exception as e:
        handle_generic_exception(e)

