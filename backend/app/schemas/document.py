from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum

class DocumentVisibility(str, Enum):
    PUBLIC = "public"
    PRIVATE = "private"

class DocumentBase(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    is_public: bool = Field(default=True)

class DocumentCreate(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    is_public: bool = Field(default=True)

class DocumentUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    is_public: Optional[bool] = None

class DocumentInDB(DocumentBase):
    id: int
    filename: str
    original_filename: str
    file_size: int
    is_processed: bool
    uploaded_by_id: int
    uploaded_at: datetime
    processed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class Document(DocumentInDB):
    uploaded_by_username: Optional[str] = None

class DocumentChunkBase(BaseModel):
    chunk_text: str
    chunk_index: int
    page_number: Optional[int] = None

class DocumentChunk(DocumentChunkBase):
    id: int
    document_id: int
    
    class Config:
        from_attributes = True

class DocumentWithChunks(Document):
    chunks: List[DocumentChunk] = []

class UploadResponse(BaseModel):
    success: bool
    message: str
    document_id: Optional[int] = None
    filename: Optional[str] = None
    file_size: Optional[int] = None