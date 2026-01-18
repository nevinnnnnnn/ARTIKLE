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
    embeddings_created_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    uploaded_by = relationship("User", backref="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Document(id={self.id}, filename='{self.filename}', is_public={self.is_public})>"


class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    chunk_index = Column(Integer, nullable=False)  # Position of this chunk in the document
    content = Column(Text, nullable=False)  # The actual text content of the chunk
    page_number = Column(Integer, nullable=True)  # Page number if document is paginated
    token_count = Column(Integer, nullable=True)  # Number of tokens in this chunk
    
    # Vector embedding related fields
    embedding = Column(Text, nullable=True)  # JSON string of the embedding vector
    embedding_model = Column(String, nullable=True)  # Which model was used to create the embedding
    
    # Foreign keys
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    document = relationship("Document", back_populates="chunks")
    
    def __repr__(self):
        return f"<DocumentChunk(id={self.id}, document_id={self.document_id}, chunk_index={self.chunk_index})>"