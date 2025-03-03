import logging
from typing import NoReturn

from fastapi import HTTPException

logger = logging.getLogger(__name__)

def handle_http_exception(status_code: int, detail: str) -> NoReturn:
    """
    Logs and raises an HTTPException with the given status code and message.
    """
    logger.error("HTTP Exception %d: %s", status_code, detail)
    raise HTTPException(status_code=status_code, detail=detail)

def handle_generic_exception(error: Exception, status_code: int = 500):
    """
    Logs and raises a generic exception as an HTTPException.
    """
    logger.exception("Unhandled Exception: %s", error)
    raise HTTPException(status_code=status_code, detail=str(error))
