from app.schemas.user import User, UserCreate, UserUpdate, UserInDB
from app.schemas.auth import Token, TokenData, LoginRequest
from app.schemas.document import (
    Document, DocumentCreate, DocumentUpdate, DocumentInDB,
    DocumentChunk, DocumentWithChunks, UploadResponse,
    DocumentVisibility
)
from app.schemas.chat import (
    ChatRequest, ChatResponse, ChatResponseData, 
    ChatResponseMetadata, ChatMessage, ChatHistory
)

__all__ = [
    # Existing
    "User", "UserCreate", "UserUpdate", "UserInDB",
    "Token", "TokenData", "LoginRequest",
    "Document", "DocumentCreate", "DocumentUpdate", "DocumentInDB",
    "DocumentChunk", "DocumentWithChunks", "UploadResponse",
    "DocumentVisibility",
    # New
    "ChatRequest", "ChatResponse", "ChatResponseData",
    "ChatResponseMetadata", "ChatMessage", "ChatHistory"
]