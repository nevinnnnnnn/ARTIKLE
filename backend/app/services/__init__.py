from app.services.pdf_processor import pdf_processor, PDFProcessor
# Use embeddings_backup instead of minimal_embeddings
from app.services.embeddings_backup import embedding_service, EmbeddingService
from app.services.chat_service import chat_service, ChatService
from app.services.gpt4all_generator import gpt4all_generator, GPT4AllGenerator

__all__ = [
    "pdf_processor", 
    "PDFProcessor",
    "embedding_service", 
    "EmbeddingService",
    "chat_service",
    "ChatService",
    "gpt4all_generator",
    "GPT4AllGenerator"
]