import os
from typing import Optional

class Settings:
    PROJECT_NAME: str = "ARTIKLE"
    PROJECT_VERSION: str = "1.0.0"
    
    # API settings
    API_V1_PREFIX: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "EOEEqBPlwuZRV1nxzPzcRCLFz9K79KMfxoXHSAukVSM")
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
    
    # Gemini API settings
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = "gemini-1.5-flash"
    
    def __init__(self):
        # Create necessary directories
        os.makedirs(self.UPLOAD_DIR, exist_ok=True)
        os.makedirs(self.VECTOR_STORE_DIR, exist_ok=True)
        
        # Validate Gemini API key
        if not self.GEMINI_API_KEY:
            print("WARNING: GEMINI_API_KEY not set. Please set it in .env file or environment variables.")

settings = Settings()