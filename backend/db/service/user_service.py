import logging
from datetime import datetime
from typing import Dict, Any

from bson import ObjectId
from bson.errors import InvalidId
from passlib.context import CryptContext

from backend.db.db import get_database
from backend.db.data.user_data import User
from backend.utils.http_error_handler import handle_http_exception
from backend.utils.validators import validate_required_fields

logger = logging.getLogger(__name__)

# Create a CryptContext for hashing. This example uses bcrypt.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def sanitize_document(doc: Dict[str, Any]) -> Dict[str, Any]:
    """
    Replaces '_id' with 'id' in the returned doc.
    """
    if "_id" in doc:
        doc["id"] = str(doc["_id"])
        del doc["_id"]
    return doc

async def create_user(user_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Registers a new user:
      1. Check if email is already used.
      2. Hash password.
      3. Insert into 'users' collection.
      4. Return the inserted user doc.
    """
    db = get_database()
    users_coll = db.users

    required_fields = ["email", "password"]
    validate_required_fields(user_data, required_fields)

    # Check for existing email
    existing = await users_coll.find_one({"email": user_data["email"], "is_deleted": False})
    if existing:
        handle_http_exception(400, f"Email '{user_data['email']}' is already in use.")

    # Hash the password
    hashed_password = pwd_context.hash(user_data["password"])
    user_data["password"] = hashed_password

    user_data["created_at"] = datetime.utcnow()
    user_data["updated_at"] = datetime.utcnow()
    user_data["is_deleted"] = False

    # Build the Pydantic model
    user_model = User.model_validate(user_data)
    doc = user_model.model_dump(by_alias=True)
    doc.pop("_id", None)  # Ensure no conflict with MongoDB

    # Insert into DB
    result = await users_coll.insert_one(doc)
    logger.info("Created new user with _id: %s", result.inserted_id)

    doc["id"] = str(result.inserted_id)
    return sanitize_document(doc)

async def authenticate_user(email: str, password: str) -> Dict[str, Any]:
    """
    Verifies that the user exists and the password is correct.
    Returns the user doc if valid, otherwise raises HTTPException.
    """
    db = get_database()
    users_coll = db.users

    user_doc = await users_coll.find_one({"email": email, "is_deleted": False})
    if not user_doc:
        handle_http_exception(401, "Invalid email or password.")

    # Compare hashed passwords
    hashed_password = user_doc["password"]
    if not pwd_context.verify(password, hashed_password):
        handle_http_exception(401, "Invalid email or password.")

    return sanitize_document(user_doc)

async def get_user_by_id(user_id: str) -> Dict[str, Any]:
    """
    Retrieve a user by MongoDB _id.
    """
    db = get_database()
    users_coll = db.users

    try:
        obj_id = ObjectId(user_id)
    except InvalidId:
        handle_http_exception(400, "Invalid user ID format.")

    doc = await users_coll.find_one({"_id": obj_id, "is_deleted": False})
    if not doc:
        handle_http_exception(404, "User not found.")

    return sanitize_document(doc)
