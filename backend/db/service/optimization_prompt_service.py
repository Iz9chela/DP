import logging
from datetime import datetime
from bson.errors import InvalidId
from typing import Dict, Any, List
from bson import ObjectId

from backend.config.config import load_config
from backend.db.db import get_database
from backend.db.data.optimized_prompt_data import OptimizedPrompt
from backend.modules.automated_refinement_module import AutomatedRefinementModule
from backend.utils.http_error_handler import handle_http_exception
from backend.utils.path_utils import resolve_path
from backend.utils.validators import validate_required_fields, validate_provider_and_model

logger = logging.getLogger(__name__)

config = load_config(resolve_path("config.yaml"))

def sanitize_document(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Remove MongoDB '_id' and set 'id' from it."""
    if "_id" in doc:
        doc["id"] = str(doc["_id"])
        del doc["_id"]
    return doc

async def create_optimized_prompt(prompt_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Inserts a new optimized prompt into the database, validates input, and performs query optimization.
    """
    required_fields = ["user_query", "provider", "model", "technique", "number_of_iterations"]
    validate_required_fields(prompt_data, required_fields)
    validate_provider_and_model(prompt_data["provider"], prompt_data["model"])

    db = get_database()

    # Perform query optimization
    refinement_module = AutomatedRefinementModule(
        user_query=prompt_data["user_query"],
        provider=prompt_data["provider"],
        model=prompt_data["model"],
        prompts=config.get("prompts", {}),
        max_iterations=prompt_data["number_of_iterations"]
    )

    optimized_data = refinement_module.optimize_query(
        selected_technique=prompt_data["technique"],
        iterations=prompt_data["number_of_iterations"]
    )

    prompt_data["optimized_output"] = optimized_data
    prompt_data["final_optimized_query"] = refinement_module.final_optimized_query
    prompt_data["created_at"] = datetime.utcnow()
    prompt_data["updated_at"] = datetime.utcnow()
    prompt_data["is_deleted"] = False

    # Prepare document
    p_model = OptimizedPrompt.model_validate(prompt_data)
    doc = p_model.model_dump(by_alias=True)
    doc.pop("_id", None)

    result = await db.optimized_prompts.insert_one(doc)

    doc.pop("_id", None)
    doc["id"] = str(result.inserted_id)
    logger.info("Created new optimized prompt with _id: %s", result.inserted_id)

    return doc

async def get_optimized_prompt(prompt_id: str) -> Dict[str, Any]:
    """Retrieves an optimized prompt document by ID."""
    db = get_database()

    if not prompt_id:
        handle_http_exception(400, "Prompt ID is required.")

    try:
        obj_id = ObjectId(prompt_id)
    except InvalidId:
        handle_http_exception(400, "Invalid prompt ID format.")

    doc = await db.optimized_prompts.find_one({"_id": obj_id, "is_deleted": False})

    if not doc:
        handle_http_exception(404, "Optimized prompt not found.")

    return sanitize_document(doc)

async def list_optimized_prompts(limit: int = 10) -> List[Dict[str, Any]]:
    """Returns a list of optimized prompts, excluding deleted, up to 'limit'."""
    db = get_database()
    cursor = db.optimized_prompts.find({"is_deleted": False}).limit(limit)
    docs = await cursor.to_list(length=limit)
    return [sanitize_document(d) for d in docs]

async def update_optimized_prompt(prompt_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
    """Updates an existing optimized prompt document."""
    db = get_database()

    if not prompt_id:
        handle_http_exception(400, "Prompt ID is required.")
    if not update_data:
        handle_http_exception(400, "Update data cannot be empty.")

    try:
        obj_id = ObjectId(prompt_id)
    except InvalidId:
        handle_http_exception(400, "Invalid prompt ID format.")

    update_data["updated_at"] = datetime.utcnow()
    doc = await db.optimized_prompts.find_one_and_update(
        {"_id": obj_id, "is_deleted": False},
        {"$set": update_data},
        return_document=True
    )

    if not doc:
        handle_http_exception(404, "Optimized prompt not found.")

    return sanitize_document(doc)

async def delete_optimized_prompt(prompt_id: str) -> bool:
    """Soft-deletes an optimized prompt by setting `is_deleted=True`."""
    db = get_database()

    if not prompt_id:
        handle_http_exception(400, "Prompt ID is required.")

    try:
        obj_id = ObjectId(prompt_id)
    except InvalidId:
        handle_http_exception(400, "Invalid prompt ID format.")

    result = await db.optimized_prompts.update_one(
        {"_id": obj_id, "is_deleted": False},
        {"$set": {"is_deleted": True, "updated_at": datetime.utcnow()}}
    )

    if result.modified_count == 0:
        handle_http_exception(404, "Optimized prompt not found or already deleted.")

    return True
