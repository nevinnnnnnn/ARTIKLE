from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from app.models.user import UserRole

# Base user schema
class UserBase(BaseModel):
    email: str = Field(..., pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = None

# Schema for creating a user
class UserCreate(UserBase):
    password: str = Field(..., min_length=6)
    role: Optional[UserRole] = UserRole.USER

# Schema for updating a user
class UserUpdate(BaseModel):
    email: Optional[str] = Field(None, pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    full_name: Optional[str] = None
    password: Optional[str] = Field(None, min_length=6)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None

# Schema for user in database
class UserInDB(UserBase):
    id: int
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Schema for returning user data (without password)
class User(UserInDB):
    pass