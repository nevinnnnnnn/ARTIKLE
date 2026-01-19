import os
import uuid
import logging
import re
from typing import List, Tuple, Optional
import PyPDF2
import fitz  # PyMuPDF
from app.config import settings

logger = logging.getLogger(__name__)

# Simple regex-based token counter (faster than character counting)
TOKEN_PATTERN = re.compile(r'\b\w+\b')

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
        """Extract text from PDF with page numbers - optimized"""
        text_parts = []
        
        try:
            # Try PyMuPDF first (faster and more accurate)
            doc = fitz.open(file_path)
            for page_num, page in enumerate(doc, start=1):
                # Use faster text extraction without OCR
                text = page.get_text("text", sort=False).strip()
                if text:
                    text_parts.append((text, page_num))
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
                    text = page.extract_text().strip() if hasattr(page, 'extract_text') else ""
                    if text:
                        text_parts.append((text, page_num))
                
                if text_parts:
                    logger.info(f"Extracted text from PDF using PyPDF2: {len(text_parts)} pages")
                    full_text = "\n\n".join([text for text, _ in text_parts])
                    return full_text, text_parts
                else:
                    raise ValueError("No text could be extracted from PDF")
        except Exception as e:
            logger.error(f"Failed to extract text from PDF: {e}")
            raise
    
    def chunk_text(self, text: str, page_parts: List[Tuple[str, int]] = None, max_overlap: int = 50) -> List[Tuple[str, Optional[int]]]:
        """Split text into chunks for embedding - optimized with overlap"""
        chunks = []
        chunk_size = settings.CHUNK_SIZE
        
        # If we have page parts, try to keep page boundaries
        if page_parts:
            current_chunk = ""
            current_page = None
            current_token_count = 0
            
            for page_text, page_num in page_parts:
                # Split page text by paragraphs (more efficient split)
                paragraphs = [p.strip() for p in page_text.split('\n\n') if p.strip()]
                
                for paragraph in paragraphs:
                    para_tokens = self.estimate_tokens(paragraph)
                    
                    # If adding this paragraph would exceed chunk size, start new chunk
                    if current_token_count + para_tokens > chunk_size:
                        if current_chunk:
                            chunks.append((current_chunk.strip(), current_page))
                        current_chunk = paragraph
                        current_page = page_num
                        current_token_count = para_tokens
                    else:
                        if current_chunk:
                            current_chunk += "\n\n" + paragraph
                        else:
                            current_chunk = paragraph
                            current_page = page_num
                        current_token_count += para_tokens
            
            # Add the last chunk
            if current_chunk:
                chunks.append((current_chunk.strip(), current_page))
        else:
            # Fallback: simple splitting by paragraphs
            paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
            current_chunk = ""
            current_tokens = 0
            
            for paragraph in paragraphs:
                para_tokens = self.estimate_tokens(paragraph)
                
                if current_tokens + para_tokens > chunk_size:
                    if current_chunk:
                        chunks.append((current_chunk.strip(), None))
                    current_chunk = paragraph
                    current_tokens = para_tokens
                else:
                    if current_chunk:
                        current_chunk += "\n\n" + paragraph
                    else:
                        current_chunk = paragraph
                    current_tokens += para_tokens
            
            if current_chunk:
                chunks.append((current_chunk.strip(), None))
        
        logger.info(f"Created {len(chunks)} text chunks (optimized)")
        return chunks
    
    def estimate_tokens(self, text: str) -> int:
        """Fast token estimation using regex (more accurate than char count)"""
        # Count words as a better approximation of tokens
        words = len(TOKEN_PATTERN.findall(text))
        # Add 30% for punctuation/special tokens
        return max(1, int(words * 1.3))

pdf_processor = PDFProcessor()