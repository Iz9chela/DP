import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Body
from datetime import datetime, timedelta
import jwt  # pyjwt
from pydantic import BaseModel

from backend.config.config import load_config
from backend.db.service.user_service import create_user, authenticate_user, get_user_by_id
from backend.utils.http_error_handler import handle_generic_exception
from backend.utils.path_utils import resolve_path

logger = logging.getLogger(__name__)
router = APIRouter()

config = load_config(resolve_path("config.yaml"))

SECRET_KEY = config.get("auth_secret_key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

@router.post("/register")
async def register_user(
    user_data: Dict[str, Any] = Body(
        ...,
        examples=[{
            "email": "user@example.com",
            "password": "123456",
            "full_name": "John Doe"
        }]
    )
) -> Dict[str, Any]:
    """
    Endpoint to register a new user.
    """
    try:
        doc = await create_user(user_data)
        # We do not return the hashed password back.
        doc.pop("password", None)
        return doc
    except Exception as e:
        handle_generic_exception(e)

@router.post("/login", response_model=TokenResponse)
async def login_user(
    login_data: Dict[str, Any] = Body(
        ...,
        examples=[{
            "email": "user@example.com",
            "password": "123456"
        }]
    )
) -> Dict[str, Any]:
    """
    Endpoint to login user. Returns a JWT access token.
    """
    try:
        user_doc = await authenticate_user(
            email=login_data["email"],
            password=login_data["password"]
        )
        # Generate JWT
        token_expiration = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        payload = {
            "sub": user_doc["id"],
            "exp": token_expiration
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

        return {
            "access_token": token,
            "token_type": "bearer"
        }
    except Exception as e:
        handle_generic_exception(e)


@router.get("/{user_id}")
async def get_user_endpoint(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a user by ID.
    """
    try:
        return await get_user_by_id(user_id)
    except Exception as e:
        handle_generic_exception(e)
