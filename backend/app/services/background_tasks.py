import asyncio
import logging
import time
from typing import Dict, Any
from concurrent.futures import ThreadPoolExecutor
from app.database import SessionLocal
from app.models.document import Document, DocumentChunk
from app.services.pdf_processor import pdf_processor
from app.utils.vector_store import vector_store_manager
from datetime import datetime

logger = logging.getLogger(__name__)

# Thread pool for parallel operations
executor = ThreadPoolExecutor(max_workers=4)

class BackgroundTaskManager:
    """Manager for background processing tasks"""
    
    def __init__(self):
        self.processing_tasks: Dict[int, asyncio.Task] = {}
        logger.info("Background task manager initialized")
    
    async def process_document_async(self, document_id: int, user_id: int):
        """Process document asynchronously - optimized"""
        try:
            db = SessionLocal()
            start_time = time.time()
            
            # Get document
            document = db.query(Document).filter(Document.id == document_id).first()
            if not document:
                logger.error(f"Document {document_id} not found")
                db.close()
                return
            
            logger.info(f"Starting optimized async processing for document {document_id}: {document.title}")
            
            # Step 1: Extract text (runs in thread pool to not block)
            logger.info(f"Extracting text from {document.filename}")
            extract_start = time.time()
            full_text, page_parts = await asyncio.get_event_loop().run_in_executor(
                executor,
                pdf_processor.extract_text_from_pdf,
                document.file_path
            )
            extract_time = time.time() - extract_start
            logger.info(f"Text extraction completed in {extract_time:.2f}s")
            
            # Step 2: Create chunks
            chunk_start = time.time()
            chunks = pdf_processor.chunk_text(full_text, page_parts)
            chunk_time = time.time() - chunk_start
            logger.info(f"Chunking completed in {chunk_time:.2f}s: {len(chunks)} chunks")
            
            # Step 3: Save chunks in batch (faster than individual inserts)
            insert_start = time.time()
            db_chunks = []
            for chunk_index, (chunk_text, page_number) in enumerate(chunks):
                token_count = pdf_processor.estimate_tokens(chunk_text)
                db_chunk = DocumentChunk(
                    document_id=document.id,
                    chunk_index=chunk_index,
                    content=chunk_text,
                    page_number=page_number,
                    token_count=token_count
                )
                db_chunks.append(db_chunk)
            
            # Batch insert
            db.bulk_save_objects(db_chunks)
            db.commit()
            insert_time = time.time() - insert_start
            logger.info(f"Batch chunk insert completed in {insert_time:.2f}s")
            
            # Step 4: Update document as processed
            document.is_processed = True
            document.processed_at = datetime.utcnow()
            db.commit()
            
            # Step 5: Create embeddings (parallel processing)
            embed_start = time.time()
            
            # Fetch chunks again (they have IDs now)
            chunks_db = db.query(DocumentChunk).filter(
                DocumentChunk.document_id == document_id
            ).order_by(DocumentChunk.chunk_index).all()
            
            texts = [chunk.content for chunk in chunks_db]
            metadata_list = [{
                "chunk_id": chunk.id,
                "document_id": document_id,
                "chunk_index": chunk.chunk_index,
                "page_number": chunk.page_number,
                "token_count": chunk.token_count
            } for chunk in chunks_db]
            
            # Process embeddings in parallel batches
            vector_store = vector_store_manager.get_store(document_id)
            vector_store.clear()
            
            # Batch embeddings by processing multiple chunks concurrently
            batch_size = 10
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i+batch_size]
                batch_metadata = metadata_list[i:i+batch_size]
                vector_store.add_texts(batch_texts, batch_metadata)
            
            vector_store.save()
            embed_time = time.time() - embed_start
            logger.info(f"Embedding creation completed in {embed_time:.2f}s")
            
            # Step 6: Mark embeddings as created
            document.embeddings_created_at = datetime.utcnow()
            db.commit()
            
            total_time = time.time() - start_time
            logger.info(f"✅ Optimized async processing complete for document {document_id}")
            logger.info(f"   Total time: {total_time:.2f}s | Extract: {extract_time:.2f}s | Chunk: {chunk_time:.2f}s | Insert: {insert_time:.2f}s | Embed: {embed_time:.2f}s")
            logger.info(f"   Chunks: {len(chunks_db)}, Embeddings: created")
            
        except Exception as e:
            logger.error(f"Error in async processing for document {document_id}: {e}", exc_info=True)
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