import asyncio
import logging
from typing import Dict, Any
from app.database import SessionLocal
from app.models.document import Document, DocumentChunk
from app.services.pdf_processor import pdf_processor
from app.utils.vector_store import vector_store_manager
from datetime import datetime

logger = logging.getLogger(__name__)

class BackgroundTaskManager:
    """Manager for background processing tasks"""
    
    def __init__(self):
        self.processing_tasks: Dict[int, asyncio.Task] = {}
        logger.info("Background task manager initialized")
    
    async def process_document_async(self, document_id: int, user_id: int):
        """Process document asynchronously"""
        try:
            db = SessionLocal()
            
            # Get document
            document = db.query(Document).filter(Document.id == document_id).first()
            if not document:
                logger.error(f"Document {document_id} not found")
                db.close()
                return
            
            logger.info(f"Starting async processing for document {document_id}: {document.title}")
            
            # Step 1: Extract text
            logger.info(f"Extracting text from {document.filename}")
            full_text, page_parts = pdf_processor.extract_text_from_pdf(document.file_path)
            
            # Step 2: Create chunks
            chunks = pdf_processor.chunk_text(full_text, page_parts)
            logger.info(f"Created {len(chunks)} chunks")
            
            # Step 3: Save chunks
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
            
            # Step 4: Update document
            document.is_processed = True
            document.processed_at = datetime.utcnow()
            db.commit()
            
            # Step 5: Create embeddings
            chunks_db = db.query(DocumentChunk).filter(
                DocumentChunk.document_id == document_id
            ).order_by(DocumentChunk.chunk_index).all()
            
            texts = [chunk.chunk_text for chunk in chunks_db]
            metadata_list = [{
                "chunk_id": chunk.id,
                "document_id": document_id,
                "chunk_index": chunk.chunk_index,
                "page_number": chunk.page_number,
                "token_count": chunk.token_count
            } for chunk in chunks_db]
            
            vector_store = vector_store_manager.get_store(document_id)
            vector_store.clear()
            vector_store.add_texts(texts, metadata_list)
            vector_store.save()
            
            # Step 6: Mark embeddings as created
            document.embeddings_created_at = datetime.utcnow()
            db.commit()
            
            logger.info(f"✅ Async processing complete for document {document_id}")
            logger.info(f"   Chunks: {len(chunks_db)}, Embeddings: created")
            
        except Exception as e:
            logger.error(f"Error in async processing for document {document_id}: {e}")
        finally:
            db.close()
            # Remove task from tracking
            if document_id in self.processing_tasks:
                del self.processing_tasks[document_id]
    
    def start_processing(self, document_id: int, user_id: int):
        """Start background processing for a document"""
        task = asyncio.create_task(self.process_document_async(document_id, user_id))
        self.processing_tasks[document_id] = task
        return task

# Global instance
background_task_manager = BackgroundTaskManager()