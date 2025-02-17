import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from bson import ObjectId
from pymongo import ReturnDocument

from backend.services.db import get_db
from backend.services.data.prompt_evaluator import PromptEvaluator

logger = logging.getLogger(__name__)


def create_prompt_evaluation(evaluation_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Inserts a new document into the 'prompt_evaluator' collection.
    Returns the inserted document (with _id).
    """
    db = get_db()

    # Use Pydantic for validation & defaults
    p_model = PromptEvaluator(**evaluation_data)
    doc = p_model.model_dump(by_alias=True)

    # Remove any leftover 'id' field so Mongo can set its own _id
    doc.pop("_id", None)

    result = db.prompt_evaluator.insert_one(doc)
    logger.info("Created new prompt evaluation with _id: %s", result.inserted_id)

    doc["_id"] = result.inserted_id
    doc["id"] = str(result.inserted_id)
    return doc


def get_prompt_evaluation(evaluation_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves a document by its _id (string) from the 'prompt_evaluator' collection.
    Excludes any documents marked is_deleted=True.
    """
    db = get_db()
    try:
        obj_id = ObjectId(evaluation_id)
    except Exception:
        logger.error("Invalid ObjectId: %s", evaluation_id)
        return None

    doc = db.prompt_evaluator.find_one({"_id": obj_id, "is_deleted": False})
    if doc:
        doc["id"] = str(doc["_id"])
    return doc


def list_prompt_evaluations(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Returns a list of evaluations, excluding those marked as deleted.
    """
    db = get_db()
    cursor = db.prompt_evaluator.find({"is_deleted": False}).limit(limit)
    docs = list(cursor)
    for d in docs:
        d["id"] = str(d["_id"])
    return docs


def update_prompt_evaluation(evaluation_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Updates an existing evaluation document by _id, returning the updated document.
    """
    db = get_db()
    try:
        obj_id = ObjectId(evaluation_id)
    except Exception:
        logger.error("Invalid ObjectId: %s", evaluation_id)
        return None

    # Force updated_at to now
    update_data["updated_at"] = datetime.utcnow()

    doc = db.prompt_evaluator.find_one_and_update(
        {"_id": obj_id, "is_deleted": False},
        {"$set": update_data},
        return_document=ReturnDocument.AFTER
    )
    if doc:
        doc["id"] = str(doc["_id"])
    return doc


def delete_prompt_evaluation(evaluation_id: str) -> bool:
    """
    Soft-deletes a document by setting is_deleted=True.
    Returns True if the document was updated, False otherwise.
    """
    db = get_db()
    try:
        obj_id = ObjectId(evaluation_id)
    except Exception:
        logger.error("Invalid ObjectId: %s", evaluation_id)
        return False

    result = db.prompt_evaluator.update_one(
        {"_id": obj_id, "is_deleted": False},
        {"$set": {"is_deleted": True, "updated_at": datetime.utcnow()}}
    )
    return result.modified_count > 0
