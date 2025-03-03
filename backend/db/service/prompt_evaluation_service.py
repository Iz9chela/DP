import logging
from datetime import datetime

from bson.errors import InvalidId
from typing import Dict, Any, List

from bson import ObjectId

from backend.config.config import load_config
from backend.db.data.prompt_evaluator_data import PromptEvaluator
from backend.db.db import get_database
from backend.modules.evaluator_module import Evaluator
from backend.utils.http_error_handler import handle_http_exception
from backend.utils.path_utils import resolve_path
from backend.utils.validators import validate_required_fields, validate_provider_and_model

logger = logging.getLogger(__name__)

config = load_config(resolve_path("config.yaml"))

def sanitize_document(doc: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remove internal _id from the document, set 'id' from it.
    """
    if "_id" in doc:
        doc["id"] = str(doc["_id"])
        del doc["_id"]
    return doc

async def create_prompt_evaluation(evaluation_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Inserts a new prompt evaluation into the database, validates input, and performs AI evaluation.
    """
    # Validate input data
    required_fields = ["prompt", "provider", "model", "evaluation_method"]
    validate_required_fields(evaluation_data, required_fields)
    validate_provider_and_model(evaluation_data["provider"], evaluation_data["model"])

    db = get_database()

    # Perform evaluation using AI
    provider = evaluation_data["provider"]
    evaluator = Evaluator(
        prompt=evaluation_data["prompt"],
        provider=provider,
        model=evaluation_data["model"],
        human_evaluation=(evaluation_data["evaluation_method"] == "human"),
        prompts=config.get("prompts", {})
    )

    evaluation_result = await evaluator.evaluate()
    evaluation_data["parsed_result"] = evaluation_result
    evaluation_data["created_at"] = datetime.utcnow()
    evaluation_data["updated_at"] = datetime.utcnow()
    evaluation_data["is_deleted"] = False

    # Prepare document
    p_model = PromptEvaluator.model_validate(evaluation_data)
    doc = p_model.model_dump(by_alias=True)
    doc.pop("_id", None)

    # Insert into MongoDB
    result = await db.prompt_evaluator.insert_one(doc)

    doc.pop("_id", None)
    doc["id"] = str(result.inserted_id)
    logger.info("Created new prompt evaluation with _id: %s", result.inserted_id)

    return doc

async def get_prompt_evaluation(evaluation_id: str) -> Dict[str, Any]:
    """
    Retrieves a prompt evaluation document by ID.
    """
    db = get_database()

    if not evaluation_id:
        handle_http_exception(400, "Evaluation ID is required.")

    try:
        obj_id = ObjectId(evaluation_id)
    except InvalidId:
        handle_http_exception(400, "Invalid evaluation ID format.")

    doc = await db.prompt_evaluator.find_one({"_id": obj_id, "is_deleted": False})

    if not doc:
        handle_http_exception(404, "Evaluation not found.")

    return sanitize_document(doc)

async def list_prompt_evaluations(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Return a list of prompt evaluations, excluding deleted, up to 'limit'.
    """
    db = get_database()
    cursor = db.prompt_evaluator.find({"is_deleted": False}).limit(limit)
    docs = await cursor.to_list(length=limit)
    return [sanitize_document(d) for d in docs]

async def update_prompt_evaluation(evaluation_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Updates an existing prompt evaluation document.
    """
    db = get_database()

    if not evaluation_id:
        handle_http_exception(400, "Evaluation ID is required.")
    if not update_data:
        handle_http_exception(400, "Update data cannot be empty.")

    try:
        obj_id = ObjectId(evaluation_id)
    except InvalidId:
        handle_http_exception(400, "Invalid evaluation ID format.")

    update_data["updated_at"] = datetime.utcnow()
    doc = await db.prompt_evaluator.find_one_and_update(
        {"_id": obj_id, "is_deleted": False},
        {"$set": update_data},
        return_document=True
    )

    if not doc:
        handle_http_exception(404, "Evaluation not found.")

    return sanitize_document(doc)

async def delete_prompt_evaluation(evaluation_id: str) -> bool:
    """
    Soft-deletes a prompt evaluation by setting `is_deleted=True`.
    """
    db = get_database()

    if not evaluation_id:
        handle_http_exception(400, "Evaluation ID is required.")

    try:
        obj_id = ObjectId(evaluation_id)
    except InvalidId:
        handle_http_exception(400, "Invalid evaluation ID format.")

    result = await db.prompt_evaluator.update_one(
        {"_id": obj_id, "is_deleted": False},
        {"$set": {"is_deleted": True, "updated_at": datetime.utcnow()}}
    )

    if result.modified_count == 0:
        handle_http_exception(404, "Evaluation not found or already deleted.")

    return True
