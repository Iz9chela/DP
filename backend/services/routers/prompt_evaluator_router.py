import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pymongo import ReturnDocument
from backend.services.data.prompt_evaluator_data import PromptEvaluator
from backend.services.db import get_database
from bson import ObjectId
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter()


def sanitize_document(doc: Dict[str, Any]) -> Dict[str, Any]:
    """
    Returns a copy of the document with the '_id' field removed.
    The 'id' field (string) is expected to already exist.
    """
    # Create a new dict with all keys except '_id'
    return {k: v for k, v in doc.items() if k != "_id"}


@router.post("/", response_model=PromptEvaluator)
async def create_prompt_evaluation(
        evaluation_data: Dict[str, Any]
        # db=Depends(get_database)
) -> Dict[str, Any]:
    """
    Inserts a new document into the 'prompt_evaluator' collection.
    Returns the inserted document with 'id' as a string.
    """
    try:
        db = get_database()
        # Validate input using Pydantic
        p_model = PromptEvaluator(**evaluation_data)
        doc = p_model.model_dump(by_alias=True)
        # Remove _id if provided so MongoDB can generate its own
        doc.pop("_id", None)
        # Ensure is_deleted is set to False if not provided
        if "is_deleted" not in doc:
            doc["is_deleted"] = False

        result = await db.prompt_evaluator.insert_one(doc)
        logger.info("Created new prompt evaluation with _id: %s", result.inserted_id)
        # Set the id field as string
        doc["id"] = str(result.inserted_id)
        # Remove any leftover '_id' key
        sanitized_doc = sanitize_document(doc)
        return sanitized_doc
    except Exception as e:
        logger.exception("Failed to create prompt evaluation: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error during creation")


@router.get("/{evaluation_id}", response_model=PromptEvaluator)
async def get_prompt_evaluation(
        evaluation_id: str,
        db=Depends(get_database)
) -> Optional[Dict[str, Any]]:
    """
    Retrieves a document by its id (string) from the 'prompt_evaluator' collection.
    Excludes any documents marked as deleted.
    """
    try:
        obj_id = ObjectId(evaluation_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid evaluation ID format")

    try:
        doc = await db.prompt_evaluator.find_one({"_id": obj_id, "is_deleted": False})
    except Exception as e:
        logger.exception("Error querying MongoDB: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error during retrieval")

    if not doc:
        raise HTTPException(status_code=404, detail="Evaluation not found")

    # Set 'id' as string and remove '_id'
    doc["id"] = str(doc["_id"])
    sanitized_doc = sanitize_document(doc)
    return sanitized_doc


@router.get("/", response_model=List[PromptEvaluator])
async def list_prompt_evaluations(
        limit: int = 10,
        db=Depends(get_database)
) -> List[Dict[str, Any]]:
    """
    Returns a list of evaluations, excluding those marked as deleted.
    """
    try:
        cursor = db.prompt_evaluator.find({"is_deleted": False}).limit(limit)
        docs = await cursor.to_list(length=limit)
        # For each document, set 'id' and remove '_id'
        sanitized_docs = []
        for d in docs:
            d["id"] = str(d["_id"])
            sanitized_docs.append(sanitize_document(d))
        return sanitized_docs
    except Exception as e:
        logger.exception("Error listing evaluations: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error during listing")


@router.put("/{evaluation_id}", response_model=PromptEvaluator)
async def update_prompt_evaluation(
        evaluation_id: str,
        update_data: Dict[str, Any],
        db=Depends(get_database)
) -> Optional[Dict[str, Any]]:
    """
    Updates an existing evaluation document by id, returning the updated document.
    """
    try:
        obj_id = ObjectId(evaluation_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid evaluation ID format")

    update_data["updated_at"] = datetime.utcnow()
    try:
        doc = await db.prompt_evaluator.find_one_and_update(
            {"_id": obj_id, "is_deleted": False},
            {"$set": update_data},
            return_document=ReturnDocument.AFTER
        )
    except Exception as e:
        logger.exception("Error updating evaluation: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error during update")

    if not doc:
        raise HTTPException(status_code=404, detail="Evaluation not found")

    doc["id"] = str(doc["_id"])
    sanitized_doc = sanitize_document(doc)
    return sanitized_doc


@router.delete("/{evaluation_id}")
async def delete_prompt_evaluation(
        evaluation_id: str,
        db=Depends(get_database)
) -> bool:
    """
    Soft-deletes a document by setting is_deleted=True.
    Returns True if the document was updated.
    """
    try:
        obj_id = ObjectId(evaluation_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid evaluation ID format")

    try:
        result = await db.prompt_evaluator.update_one(
            {"_id": obj_id, "is_deleted": False},
            {"$set": {"is_deleted": True, "updated_at": datetime.utcnow()}}
        )
    except Exception as e:
        logger.exception("Error deleting evaluation: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error during deletion")

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Evaluation not found or already deleted")

    return True
