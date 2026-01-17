import os
from typing import Optional

class Settings:
    PROJECT_NAME: str = "PDF AI Chatbot"
    PROJECT_VERSION: str = "1.0.0"
    
    # API settings
    API_V1_PREFIX: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./pdf_chatbot.db")
    
    # File storage
    UPLOAD_DIR: str = "uploads"
    VECTOR_STORE_DIR: str = "vector_stores"
    
    # AI Model settings
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"  # Free, local model
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    
    def __init__(self):
        # Create necessary directories
        os.makedirs(self.UPLOAD_DIR, exist_ok=True)
        os.makedirs(self.VECTOR_STORE_DIR, exist_ok=True)

settings = Settings()