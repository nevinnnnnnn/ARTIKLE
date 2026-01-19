from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class ChatHistory(Base):
    """Store chat conversations for persistence"""
    __tablename__ = "chat_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    
    # Chat content
    user_question = Column(Text, nullable=False)
    ai_response = Column(Text, nullable=True)
    
    # Metadata
    relevance_score = Column(Float, default=0.0)
    context_chunks = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<ChatHistory(id={self.id}, user_id={self.user_id}, doc_id={self.document_id})>"
