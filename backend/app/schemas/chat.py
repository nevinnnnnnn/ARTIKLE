from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class ChatRequest(BaseModel):
    document_id: int = Field(..., description="ID of the document to chat with")
    query: str = Field(..., min_length=1, max_length=1000, description="User's question")
    stream: Optional[bool] = Field(True, description="Whether to stream the response")

class ChatResponseMetadata(BaseModel):
    document_id: int
    query: str
    is_relevant: bool
    context_chunks_retrieved: int
    top_similarity_score: float

class ChatResponseData(BaseModel):
    document_id: int
    query: str
    response: str
    metadata: ChatResponseMetadata

class ChatResponse(BaseModel):
    success: bool
    message: str
    data: ChatResponseData

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: Optional[str] = None

class ChatHistory(BaseModel):
    document_id: int
    messages: List[ChatMessage]
    created_at: Optional[str] = None
    updated_at: Optional[str] = None