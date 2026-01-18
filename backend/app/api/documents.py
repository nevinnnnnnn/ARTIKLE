from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import os
from datetime import datetime

from app.database import get_db, SessionLocal
from app.models.document import Document, DocumentChunk
from app.models.user import User, UserRole
from app.schemas.document import (
    Document as DocumentSchema,
    DocumentUpdate,
    DocumentWithChunks,
    UploadResponse
)
from app.auth.dependencies import require_admin, require_user
from app.services.pdf_processor import pdf_processor
from app.utils import create_response, get_logger
from app.utils.vector_store import vector_store_manager

router = APIRouter(prefix="/documents", tags=["documents"])
logger = get_logger(__name__)

# =========================================================
# BACKGROUND AUTO-PROCESSING TASK
# (Used by background_task_manager)
# =========================================================

async def auto_process_document(document_id: int, user_id: int):
    """Auto-process document after upload (runs in background)"""

    db = SessionLocal()

    try:
        logger.info(f"Starting auto-processing for document {document_id}")

        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            logger.error(f"Document {document_id} not found for auto-processing")
            return

        # ---- Extract text ----
        logger.info(f"Extracting text from document {document_id}")
        full_text, page_parts = pdf_processor.extract_text_from_pdf(
            document.file_path
        )

        # ---- Chunking ----
        chunks = pdf_processor.chunk_text(full_text, page_parts)
        if not chunks:
            logger.error(f"No chunks created for document {document_id}")
            return

        for idx, (chunk_text, page_number) in enumerate(chunks):
            token_count = pdf_processor.estimate_tokens(chunk_text)
            db.add(
                DocumentChunk(
                    document_id=document.id,
                    chunk_index=idx,
                    chunk_text=chunk_text,
                    page_number=page_number,
                    token_count=token_count
                )
            )

        document.is_processed = True
        document.processed_at = datetime.utcnow()
        db.commit()

        logger.info(f"Created {len(chunks)} chunks for document {document_id}")

        # ---- Embeddings ----
        chunks = db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document_id
        ).order_by(DocumentChunk.chunk_index).all()

        texts = []
        metadata = []

        for chunk in chunks:
            texts.append(chunk.chunk_text)
            metadata.append({
                "chunk_id": chunk.id,
                "document_id": document_id,
                "chunk_index": chunk.chunk_index,
                "page_number": chunk.page_number,
                "token_count": chunk.token_count
            })

        vector_store = vector_store_manager.get_store(document_id)
        vector_store.clear()
        vector_store.add_texts(texts, metadata)
        vector_store.save()

        document.embeddings_created_at = datetime.utcnow()
        db.commit()

        logger.info(f"✅ Auto-processing complete for document {document_id}")

    except Exception as e:
        logger.error(f"Auto-processing failed for document {document_id}: {e}")
        db.rollback()
    finally:
        db.close()

# =========================================================
# UPLOAD DOCUMENT (BACKGROUND MANAGER ENABLED)
# =========================================================

@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(..., description="PDF file to upload"),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    is_public: bool = Form(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Upload a PDF document with auto-processing"""

    # ---- Validation ----
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed"
        )

    file.file.seek(0, os.SEEK_END)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size > 50 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds 50MB limit"
        )

    try:
        # ---- Save file ----
        unique_filename, file_path, saved_file_size = (
            pdf_processor.save_uploaded_file(file.file, file.filename)
        )

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

        logger.info(
            f"Document uploaded by {current_user.username}: {db_document.filename}"
        )

        # 🔥 START AUTO-PROCESSING USING BACKGROUND MANAGER
        from app.services.background_tasks import background_task_manager
        background_task_manager.start_processing(
            db_document.id,
            current_user.id
        )

        return UploadResponse(
            success=True,
            message="Document uploaded successfully. Processing started in background.",
            document_id=db_document.id,
            filename=db_document.original_filename,
            file_size=db_document.file_size
        )

    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error uploading document"
        )

# =========================================================
# DOCUMENT PROCESSING STATUS
# =========================================================

@router.get("/{document_id}/status")
async def get_document_status(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user)
):
    """Get document processing status"""

    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Permissions
    if not document.is_public and current_user.role == UserRole.USER:
        raise HTTPException(status_code=403, detail="Access denied")

    if (
        not document.is_public
        and current_user.role == UserRole.ADMIN
        and document.uploaded_by_id != current_user.id
    ):
        raise HTTPException(status_code=403, detail="Access denied")

    chunk_count = db.query(DocumentChunk).filter(
        DocumentChunk.document_id == document_id
    ).count()

    vector_stats = None
    if document.embeddings_created_at:
        try:
            vector_store = vector_store_manager.get_store(document_id)
            vector_stats = vector_store.get_stats()
        except Exception:
            pass

    status_label = (
        "ready"
        if document.embeddings_created_at
        else "processing"
        if document.is_processed
        else "uploaded"
    )

    return {
        "success": True,
        "data": {
            "document_id": document.id,
            "title": document.title,
            "is_processed": document.is_processed,
            "processed_at": document.processed_at.isoformat()
            if document.processed_at else None,
            "embeddings_created_at": document.embeddings_created_at.isoformat()
            if document.embeddings_created_at else None,
            "chunk_count": chunk_count,
            "vector_stats": vector_stats,
            "status": status_label
        }
    }

# =========================================================
# GET DOCUMENTS
# =========================================================

@router.get("", response_model=List[DocumentSchema])
async def get_documents(
    skip: int = 0,
    limit: int = 100,
    is_public: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user)
):
    query = db.query(Document)

    if is_public is not None:
        query = query.filter(Document.is_public == is_public)

    if current_user.role == UserRole.USER:
        query = query.filter(Document.is_public == True)
    elif current_user.role == UserRole.ADMIN:
        query = query.filter(
            (Document.is_public == True) |
            (Document.uploaded_by_id == current_user.id)
        )

    documents = query.offset(skip).limit(limit).all()

    result = []
    for doc in documents:
        schema = DocumentSchema.from_orm(doc)
        schema.uploaded_by_username = doc.uploaded_by.username
        result.append(schema)

    return result

# =========================================================
# GET DOCUMENT WITH CHUNKS
# =========================================================

@router.get("/{document_id}", response_model=DocumentWithChunks)
async def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user)
):
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if not document.is_public and current_user.role == UserRole.USER:
        raise HTTPException(status_code=403, detail="Access denied")

    chunks = db.query(DocumentChunk).filter(
        DocumentChunk.document_id == document_id
    ).order_by(DocumentChunk.chunk_index).all()

    schema = DocumentWithChunks.from_orm(document)
    schema.uploaded_by_username = document.uploaded_by.username
    schema.chunks = chunks
    return schema

# =========================================================
# DELETE DOCUMENT
# =========================================================

@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if current_user.role == UserRole.ADMIN and document.uploaded_by_id != current_user.id:
        raise HTTPException(status_code=403, detail="Permission denied")

    try:
        if os.path.exists(document.file_path):
            os.remove(document.file_path)
    except Exception:
        logger.warning("File deletion failed")

    db.delete(document)
    db.commit()

    return create_response(success=True, message="Document deleted successfully")