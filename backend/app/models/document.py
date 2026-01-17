from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)  # Size in bytes
    title = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    is_public = Column(Boolean, default=True, nullable=False)
    is_processed = Column(Boolean, default=False, nullable=False)
    
    # Foreign keys
    uploaded_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Timestamps
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    uploaded_by = relationship("User", backref="documents")
    
    def __repr__(self):
        return f"<Document(id={self.id}, filename='{self.filename}', is_public={self.is_public})>"


class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)  # Order of chunks
    chunk_text = Column(Text, nullable=False)
    page_number = Column(Integer, nullable=True)  # PDF page number
    token_count = Column(Integer, nullable=True)  # Approximate token count
    
    # Relationships
    document = relationship("Document", backref="chunks")
    
    def __repr__(self):
        return f"<DocumentChunk(id={self.id}, doc_id={self.document_id}, chunk={self.chunk_index})>"