from app.services.pdf_processor import pdf_processor, PDFProcessor
# Use fast_embeddings for better performance
from app.services.fast_embeddings import embedding_service, FastEmbeddingService
from app.services.chat_service import chat_service, ChatService
from app.services.ollama_generator import ollama_generator, OllamaGenerator

__all__ = [
    "pdf_processor", 
    "PDFProcessor",
    "embedding_service", 
    "FastEmbeddingService",
    "chat_service",
    "ChatService",
    "ollama_generator",
    "OllamaGenerator"
]