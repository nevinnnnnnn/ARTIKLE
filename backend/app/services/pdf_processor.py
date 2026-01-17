import os
import uuid
import logging
from typing import List, Tuple, Optional
import PyPDF2
import fitz  # PyMuPDF
from app.config import settings

logger = logging.getLogger(__name__)

class PDFProcessor:
    def __init__(self):
        self.upload_dir = settings.UPLOAD_DIR
        os.makedirs(self.upload_dir, exist_ok=True)
    
    def save_uploaded_file(self, file, filename: str) -> Tuple[str, str]:
        """Save uploaded file with unique filename"""
        # Generate unique filename
        file_ext = os.path.splitext(filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = os.path.join(self.upload_dir, unique_filename)
        
        # Save file
        with open(file_path, "wb") as buffer:
            buffer.write(file.read())
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
        logger.info(f"Saved uploaded file: {unique_filename} ({file_size} bytes)")
        return unique_filename, file_path, file_size
    
    def extract_text_from_pdf(self, file_path: str) -> Tuple[str, List[Tuple[str, int]]]:
        """Extract text from PDF with page numbers"""
        text_parts = []
        
        try:
            # Try PyMuPDF first (faster and more accurate)
            doc = fitz.open(file_path)
            for page_num, page in enumerate(doc, start=1):
                text = page.get_text()
                if text.strip():
                    text_parts.append((text.strip(), page_num))
            doc.close()
            
            if text_parts:
                logger.info(f"Extracted text from PDF using PyMuPDF: {len(text_parts)} pages")
                full_text = "\n\n".join([text for text, _ in text_parts])
                return full_text, text_parts
        except Exception as e:
            logger.warning(f"PyMuPDF failed, trying PyPDF2: {e}")
        
        # Fallback to PyPDF2
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text_parts = []
                
                for page_num, page in enumerate(pdf_reader.pages, start=1):
                    text = page.extract_text()
                    if text.strip():
                        text_parts.append((text.strip(), page_num))
                
                if text_parts:
                    logger.info(f"Extracted text from PDF using PyPDF2: {len(text_parts)} pages")
                    full_text = "\n\n".join([text for text, _ in text_parts])
                    return full_text, text_parts
                else:
                    raise ValueError("No text could be extracted from PDF")
        except Exception as e:
            logger.error(f"Failed to extract text from PDF: {e}")
            raise
    
    def chunk_text(self, text: str, page_parts: List[Tuple[str, int]] = None) -> List[Tuple[str, Optional[int]]]:
        """Split text into chunks for embedding"""
        chunks = []
        
        # If we have page parts, try to keep page boundaries
        if page_parts:
            current_chunk = ""
            current_page = None
            current_token_count = 0
            
            for page_text, page_num in page_parts:
                # Split page text by paragraphs
                paragraphs = page_text.split('\n\n')
                
                for paragraph in paragraphs:
                    if paragraph.strip():
                        # Very rough token estimation (4 chars ≈ 1 token)
                        para_token_est = len(paragraph) // 4
                        
                        # If adding this paragraph would exceed chunk size, start new chunk
                        if current_token_count + para_token_est > settings.CHUNK_SIZE:
                            if current_chunk:
                                chunks.append((current_chunk.strip(), current_page))
                            current_chunk = paragraph
                            current_page = page_num
                            current_token_count = para_token_est
                        else:
                            if current_chunk:
                                current_chunk += "\n\n" + paragraph
                            else:
                                current_chunk = paragraph
                                current_page = page_num
                            current_token_count += para_token_est
            
            # Add the last chunk
            if current_chunk:
                chunks.append((current_chunk.strip(), current_page))
        else:
            # Fallback: simple splitting by paragraphs
            paragraphs = text.split('\n\n')
            current_chunk = ""
            
            for paragraph in paragraphs:
                if paragraph.strip():
                    if len(current_chunk) + len(paragraph) > settings.CHUNK_SIZE:
                        if current_chunk:
                            chunks.append((current_chunk.strip(), None))
                        current_chunk = paragraph
                    else:
                        if current_chunk:
                            current_chunk += "\n\n" + paragraph
                        else:
                            current_chunk = paragraph
            
            if current_chunk:
                chunks.append((current_chunk.strip(), None))
        
        logger.info(f"Created {len(chunks)} text chunks")
        return chunks
    
    def estimate_tokens(self, text: str) -> int:
        """Rough token estimation (4 chars ≈ 1 token)"""
        return len(text) // 4

pdf_processor = PDFProcessor()