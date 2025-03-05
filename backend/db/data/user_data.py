from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class User(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    email: EmailStr = Field(..., description="User's unique email address", examples=["locik@gmail.com"])
    password: str = Field(..., description="Hashed user password", examples=["password12345"])
    full_name: Optional[str] = Field(default=None, description="User's full name", examples=["Andrew Terrington"])
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when the user was last updated"
    )
    is_deleted: bool = Field(
        default=False,
        description="Flag for soft deletion"
    )

    class Config:
        populate_by_name = True
        from_attributes = True
