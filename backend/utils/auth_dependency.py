import logging
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from datetime import datetime

from backend.config.config import load_config
from backend.utils.http_error_handler import handle_http_exception
from backend.utils.path_utils import resolve_path

config = load_config(resolve_path("config.yaml"))

SECRET_KEY = config.get("auth_secret_key")
ALGORITHM = "HS256"

logger = logging.getLogger(__name__)

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    Extract and validate the JWT from Authorization header: Bearer <token>.
    Returns the user_id (str) if valid.
    """
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        exp: int = payload.get("exp")
        if not user_id or not exp:
            handle_http_exception(status_code=401, detail="Invalid token payload.")
        # Check token expiry
        if datetime.utcnow().timestamp() > exp:
            handle_http_exception(status_code=401, detail="Token has expired.")
        return user_id
    except jwt.ExpiredSignatureError:
        handle_http_exception(status_code=401, detail="Token has expired.")
    except jwt.PyJWTError:
        handle_http_exception(status_code=401, detail="Token is invalid.")
