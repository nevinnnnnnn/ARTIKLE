from pydantic import BaseModel, Field
from typing import Optional

class Token(BaseModel):
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    user_id: int = Field(..., description="User ID")
    role: str = Field(..., description="User role")
    
    model_config = {"json_schema_extra": {"example": {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "token_type": "bearer",
        "user_id": 1,
        "role": "superadmin"
    }}}

class TokenData(BaseModel):
    user_id: Optional[int] = None
    role: Optional[str] = None

class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, description="Username or email")
    password: str = Field(..., min_length=6, description="Password")