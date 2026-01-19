from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
import json
import time
import asyncio

from app.database import get_db
from app.models.document import Document
from app.models.user import User, UserRole
from app.schemas.chat import ChatRequest, ChatResponse  # We'll create this
from app.auth.dependencies import require_user
from app.services.chat_service import chat_service
from app.services.chat_persistence import chat_persistence
from app.utils import get_logger

router = APIRouter(prefix="/chat", tags=["chat"])
logger = get_logger(__name__)

@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user)
):
    """Streaming chat endpoint with RAG + persistence"""
    
    # Validate document exists and user has access
    document = db.query(Document).filter(Document.id == request.document_id).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Check permissions
    if not document.is_public and current_user.role == UserRole.USER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to chat with this document"
        )
    
    if (document.is_public == False and 
        current_user.role == UserRole.ADMIN and 
        document.uploaded_by_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to chat with this document"
        )
    
    # Check if document is processed
    if not document.is_processed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document must be processed before chatting"
        )
    
    logger.info(f"Chat request from {current_user.username} for document {document.id}: {request.query[:50]}...")
    
    # Get chat response with timeout
    try:
        chat_result = await asyncio.wait_for(
            asyncio.to_thread(
                chat_service.get_chat_response,
                document_id=request.document_id,
                query=request.query,
                stream=True
            ),
            timeout=120  # 2 minute timeout
        )
    except asyncio.TimeoutError:
        logger.error("Chat generation timeout")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Chat generation took too long. Please try again."
        )
    
    # Create streaming response
    async def event_stream():
        """Generator for Server-Sent Events"""
        
        full_response = ""
        metadata = chat_result["metadata"]
        
        # Send metadata first
        metadata_event = {
            "type": "metadata",
            "data": metadata
        }
        yield f"data: {json.dumps(metadata_event)}\n\n"
        
        # Send response chunks
        try:
            for chunk in chat_result["stream_generator"]:
                if chunk:
                    full_response += chunk
                    text_event = {
                        "type": "text",
                        "data": chunk
                    }
                    yield f"data: {json.dumps(text_event)}\n\n"
            
            # Send completion event
            completion_event = {
                "type": "complete",
                "data": {"status": "completed"}
            }
            yield f"data: {json.dumps(completion_event)}\n\n"
            
            # Save to database (async)
            try:
                chat_persistence.save_chat(
                    db=db,
                    user_id=current_user.id,
                    document_id=request.document_id,
                    question=request.query,
                    response=full_response,
                    relevance_score=metadata.get("top_similarity_score", 0.0),
                    context_chunks=metadata.get("context_chunks_retrieved", 0)
                )
            except Exception as e:
                logger.warning(f"Failed to save chat to DB: {e}")
            
        except Exception as e:
            logger.error(f"Error in chat stream: {e}")
            error_event = {
                "type": "error",
                "data": {"message": "Error generating response"}
            }
            yield f"data: {json.dumps(error_event)}\n\n"
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable buffering for nginx
            "Timeout": "120"  # 2 minute timeout
        }
    )

@router.post("/message", response_model=ChatResponse)
async def chat_message(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user)
):
    """Non-streaming chat endpoint (for simple requests)"""
    
    # Validate document exists and user has access
    document = db.query(Document).filter(Document.id == request.document_id).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Check permissions
    if not document.is_public and current_user.role == UserRole.USER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to chat with this document"
        )
    
    if (document.is_public == False and 
        current_user.role == UserRole.ADMIN and 
        document.uploaded_by_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to chat with this document"
        )
    
    # Check if document is processed
    if not document.is_processed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document must be processed before chatting"
        )
    
    logger.info(f"Chat message from {current_user.username} for document {document.id}")
    
    # Get chat response (non-streaming)
    chat_result = chat_service.get_chat_response(
        document_id=request.document_id,
        query=request.query,
        stream=False
    )
    
    return ChatResponse(
        success=True,
        message="Chat response generated",
        data={
            "document_id": request.document_id,
            "query": request.query,
            "response": chat_result["response"],
            "metadata": chat_result["metadata"]
        }
    )

@router.get("/documents")
async def get_chatable_documents(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user)
):
    """Get list of documents that are ready for chatting (processed)"""
    
    query = db.query(Document).filter(Document.is_processed == True)
    
    # Non-admin users can only see public documents
    if current_user.role == UserRole.USER:
        query = query.filter(Document.is_public == True)
    
    # Admins can see public docs + their own private docs
    elif current_user.role == UserRole.ADMIN:
        query = query.filter(
            (Document.is_public == True) | 
            (Document.uploaded_by_id == current_user.id)
        )
    
    # Superadmins can see everything
    
    documents = query.offset(skip).limit(limit).all()
    
    # Format response
    result = []
    for doc in documents:
        result.append({
            "id": doc.id,
            "title": doc.title or doc.original_filename,
            "filename": doc.original_filename,
            "is_public": doc.is_public,
            "uploaded_by": doc.uploaded_by.username,
            "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None,
            "processed_at": doc.processed_at.isoformat() if doc.processed_at else None
        })
    
    return {
        "success": True,
        "message": f"Found {len(result)} chatable documents",
        "data": result
    }


@router.get("/history/{document_id}")
async def get_chat_history(
    document_id: int,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user)
):
    """Get persistent chat history for a document"""
    
    # Validate document access
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
            detail="You don't have permission to access this document"
        )
    
    if (document.is_public == False and 
        current_user.role == UserRole.ADMIN and 
        document.uploaded_by_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this document"
        )
    
    # Get chat history
    history = chat_persistence.get_chat_history(
        db=db,
        user_id=current_user.id,
        document_id=document_id,
        limit=limit
    )
    
    return {
        "success": True,
        "message": f"Retrieved {len(history)} chat messages",
        "data": history
    }


@router.get("/history")
async def get_all_chat_history(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user)
):
    """Get all persistent chat history for current user"""
    
    history = chat_persistence.get_chat_history(
        db=db,
        user_id=current_user.id,
        limit=limit
    )
    
    # Get statistics
    stats = chat_persistence.get_chat_statistics(db=db, user_id=current_user.id)
    
    return {
        "success": True,
        "message": f"Retrieved {len(history)} chat messages",
        "statistics": stats,
        "data": history
    }


@router.delete("/history/{document_id}")
async def clear_chat_history(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user)
):
    """Clear chat history for a specific document"""
    
    # Validate document access
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Check permissions (only superadmin and document owner)
    if current_user.role not in [UserRole.SUPERADMIN, UserRole.ADMIN] or \
       (current_user.role == UserRole.ADMIN and document.uploaded_by_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to clear this history"
        )
    
    # Clear history
    success = chat_persistence.clear_chat_history(
        db=db,
        user_id=current_user.id,
        document_id=document_id
    )
    
    return {
        "success": success,
        "message": "Chat history cleared successfully" if success else "Failed to clear history"
    }