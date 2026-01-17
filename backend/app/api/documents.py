from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import os

from app.database import get_db
from app.models.document import Document, DocumentChunk
from app.models.user import User, UserRole
from app.schemas.document import (
    Document as DocumentSchema, 
    DocumentCreate, 
    DocumentUpdate,
    DocumentWithChunks,
    UploadResponse
)
from app.schemas.user import User as UserSchema
from app.auth.dependencies import require_admin, require_user
from app.services.pdf_processor import pdf_processor
from app.utils import create_response, get_logger
from app.utils.vector_store import vector_store_manager
from app.services.embeddings_backup import embedding_service

router = APIRouter(prefix="/documents", tags=["documents"])
logger = get_logger(__name__)

@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(..., description="PDF file to upload"),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    is_public: bool = Form(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Upload a PDF document (admin only)"""
    
    # Check file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed"
        )
    
    # Check file size (max 50MB)
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to beginning
    
    if file_size > 50 * 1024 * 1024:  # 50MB
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds 50MB limit"
        )
    
    try:
        # Save uploaded file
        unique_filename, file_path, saved_file_size = pdf_processor.save_uploaded_file(
            file.file, file.filename
        )
        
        # Create document record
        db_document = Document(
            filename=unique_filename,
            original_filename=file.filename,
            file_path=file_path,
            file_size=saved_file_size,
            title=title or os.path.splitext(file.filename)[0],
            description=description,
            is_public=is_public,
            is_processed=False,
            uploaded_by_id=current_user.id
        )
        
        db.add(db_document)
        db.commit()
        db.refresh(db_document)
        
        logger.info(f"Document uploaded by {current_user.username}: {db_document.filename}")
        
        return UploadResponse(
            success=True,
            message="Document uploaded successfully",
            document_id=db_document.id,
            filename=db_document.original_filename,
            file_size=db_document.file_size
        )
        
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading document: {str(e)}"
        )

@router.get("", response_model=List[DocumentSchema])
async def get_documents(
    skip: int = 0,
    limit: int = 100,
    is_public: Optional[bool] = None,
    is_processed: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user)
):
    """Get list of documents"""
    query = db.query(Document)
    
    # Apply filters
    if is_public is not None:
        query = query.filter(Document.is_public == is_public)
    
    if is_processed is not None:
        query = query.filter(Document.is_processed == is_processed)
    
    # Non-admin users can only see public documents
    if current_user.role == UserRole.USER:
        query = query.filter(Document.is_public == True)
    
    # Admins and superadmins can see all documents
    # (admins can see private docs they uploaded, superadmins see all)
    elif current_user.role == UserRole.ADMIN:
        # Admins can see public docs + their own private docs
        query = query.filter(
            (Document.is_public == True) | 
            (Document.uploaded_by_id == current_user.id)
        )
    
    # Superadmins can see everything (no filter needed)
    
    documents = query.offset(skip).limit(limit).all()
    
    # Add username to response
    result = []
    for doc in documents:
        doc_dict = DocumentSchema.from_orm(doc)
        doc_dict.uploaded_by_username = doc.uploaded_by.username
        result.append(doc_dict)
    
    return result

@router.get("/{document_id}", response_model=DocumentWithChunks)
async def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user)
):
    """Get document by ID with chunks"""
    document = db.query(Document).filter(Document.id == document_id).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Check permissions
    if not document.is_public and current_user.role == UserRole.USER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this document"
        )
    
    if (document.is_public == False and 
        current_user.role == UserRole.ADMIN and 
        document.uploaded_by_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this document"
        )
    
    # Get chunks
    chunks = db.query(DocumentChunk).filter(
        DocumentChunk.document_id == document_id
    ).order_by(DocumentChunk.chunk_index).all()
    
    # Convert to schema
    doc_schema = DocumentWithChunks.from_orm(document)
    doc_schema.uploaded_by_username = document.uploaded_by.username
    doc_schema.chunks = chunks
    
    return doc_schema

@router.put("/{document_id}", response_model=DocumentSchema)
async def update_document(
    document_id: int,
    document_update: DocumentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Update document metadata (admin only)"""
    document = db.query(Document).filter(Document.id == document_id).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Check permissions
    if (current_user.role == UserRole.ADMIN and 
        document.uploaded_by_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update documents you uploaded"
        )
    
    # Update fields
    update_data = document_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(document, field, value)
    
    db.commit()
    db.refresh(document)
    
    logger.info(f"Document {document.id} updated by {current_user.username}")
    
    # Add username to response
    doc_schema = DocumentSchema.from_orm(document)
    doc_schema.uploaded_by_username = document.uploaded_by.username
    
    return doc_schema

@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Delete document (admin only)"""
    document = db.query(Document).filter(Document.id == document_id).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Check permissions
    if (current_user.role == UserRole.ADMIN and 
        document.uploaded_by_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete documents you uploaded"
        )
    
    # Delete file from storage
    try:
        if os.path.exists(document.file_path):
            os.remove(document.file_path)
    except Exception as e:
        logger.warning(f"Could not delete file {document.file_path}: {e}")
    
    # Delete from database
    db.delete(document)
    db.commit()
    
    logger.warning(f"Document {document.id} deleted by {current_user.username}")
    
    return create_response(
        success=True,
        message="Document deleted successfully"
    )

@router.post("/{document_id}/process")
async def process_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Process document - extract text and create chunks (admin only)"""
    document = db.query(Document).filter(Document.id == document_id).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    if document.is_processed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document is already processed"
        )
    
    # Check permissions
    if (current_user.role == UserRole.ADMIN and 
        document.uploaded_by_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only process documents you uploaded"
        )
    
    try:
        # Extract text from PDF
        full_text, page_parts = pdf_processor.extract_text_from_pdf(document.file_path)
        
        # Create chunks
        chunks = pdf_processor.chunk_text(full_text, page_parts)
        
        # Save chunks to database
        for chunk_index, (chunk_text, page_number) in enumerate(chunks):
            token_count = pdf_processor.estimate_tokens(chunk_text)
            
            db_chunk = DocumentChunk(
                document_id=document.id,
                chunk_index=chunk_index,
                chunk_text=chunk_text,
                page_number=page_number,
                token_count=token_count
            )
            db.add(db_chunk)
        
        # Update document status
        document.is_processed = True
        db.commit()
        
        logger.info(f"Document {document.id} processed: {len(chunks)} chunks created")
        
        return create_response(
            success=True,
            message=f"Document processed successfully. Created {len(chunks)} chunks.",
            data={
                "document_id": document.id,
                "chunks_created": len(chunks),
                "is_processed": True
            }
        )
        
    except Exception as e:
        logger.error(f"Error processing document {document.id}: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing document: {str(e)}"
        )
    
@router.post("/{document_id}/create-embeddings")
async def create_document_embeddings(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Create embeddings for document chunks and store in vector database (admin only)"""
    document = db.query(Document).filter(Document.id == document_id).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    if not document.is_processed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document must be processed first"
        )
    
    # Check permissions
    if (current_user.role == UserRole.ADMIN and 
        document.uploaded_by_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only create embeddings for documents you uploaded"
        )
    
    try:
        # Get document chunks
        chunks = db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document_id
        ).order_by(DocumentChunk.chunk_index).all()
        
        if not chunks:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No chunks found for this document"
            )
        
        # Prepare texts and metadata
        texts = []
        metadata_list = []
        
        for chunk in chunks:
            texts.append(chunk.chunk_text)
            metadata_list.append({
                "chunk_id": chunk.id,
                "document_id": document_id,
                "chunk_index": chunk.chunk_index,
                "page_number": chunk.page_number,
                "token_count": chunk.token_count
            })
        
        # Get or create vector store for this document
        vector_store = vector_store_manager.get_store(document_id)
        
        # Clear existing embeddings (if any)
        vector_store.clear()
        
        # Create and store embeddings
        logger.info(f"Creating embeddings for {len(texts)} chunks in document {document_id}")
        vector_store.add_texts(texts, metadata_list)
        
        # Save vector store
        vector_store.save()
        
        logger.info(f"Embeddings created for document {document_id}: {len(texts)} vectors")
        
        return create_response(
            success=True,
            message=f"Embeddings created successfully for {len(texts)} chunks",
            data={
                "document_id": document_id,
                "chunks_embedded": len(texts),
                "vector_store_stats": vector_store.get_stats()
            }
        )
        
    except Exception as e:
        logger.error(f"Error creating embeddings for document {document_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating embeddings: {str(e)}"
        )

@router.get("/{document_id}/vector-stats")
async def get_vector_stats(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user)
):
    """Get vector store statistics for a document"""
    document = db.query(Document).filter(Document.id == document_id).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Check permissions
    if not document.is_public and current_user.role == UserRole.USER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this document"
        )
    
    if (document.is_public == False and 
        current_user.role == UserRole.ADMIN and 
        document.uploaded_by_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this document"
        )
    
    try:
        vector_store = vector_store_manager.get_store(document_id)
        stats = vector_store.get_stats()
        
        return create_response(
            success=True,
            message="Vector store statistics retrieved",
            data=stats
        )
    except Exception as e:
        logger.error(f"Error getting vector stats for document {document_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving vector statistics: {str(e)}"
        )

@router.post("/{document_id}/similarity-search")
async def similarity_search(
    document_id: int,
    query: str = Form(..., description="Search query"),
    k: int = Form(5, description="Number of results to return"),
    threshold: float = Form(0.5, description="Similarity threshold (0.0 to 1.0)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user)
):
    """Search for similar content in a document using embeddings"""
    document = db.query(Document).filter(Document.id == document_id).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Check permissions
    if not document.is_public and current_user.role == UserRole.USER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to search this document"
        )
    
    if (document.is_public == False and 
        current_user.role == UserRole.ADMIN and 
        document.uploaded_by_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to search this document"
        )
    
    try:
        vector_store = vector_store_manager.get_store(document_id)
        
        # Perform similarity search
        results = vector_store.similarity_search(query, k, threshold)
        
        # Get full chunk details for results
        enhanced_results = []
        for metadata, similarity in results:
            chunk = db.query(DocumentChunk).filter(
                DocumentChunk.id == metadata["chunk_id"]
            ).first()
            
            if chunk:
                enhanced_results.append({
                    "chunk_id": chunk.id,
                    "chunk_index": chunk.chunk_index,
                    "page_number": chunk.page_number,
                    "text_preview": chunk.chunk_text[:200] + "..." if len(chunk.chunk_text) > 200 else chunk.chunk_text,
                    "text_length": len(chunk.chunk_text),
                    "similarity_score": similarity,
                    "document_id": document_id
                })
        
        logger.info(f"Similarity search for '{query}' in document {document_id}: {len(enhanced_results)} results")
        
        return create_response(
            success=True,
            message=f"Found {len(enhanced_results)} similar chunks",
            data={
                "query": query,
                "document_id": document_id,
                "results": enhanced_results,
                "total_results": len(enhanced_results)
            }
        )
        
    except Exception as e:
        logger.error(f"Error in similarity search for document {document_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error performing similarity search: {str(e)}"
        )