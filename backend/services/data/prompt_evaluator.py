from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class PromptEvaluator(BaseModel):
    """
    Represents the schema for a prompt evaluation document in MongoDB.
    """
    id: Optional[str] = Field(default=None, alias="_id")

    prompt: str
    evaluation_method: str
    model: str
    parsed_result: Dict[str, Any]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_deleted: bool = False

    class Config:
        populate_by_name = True
        from_attributes = True