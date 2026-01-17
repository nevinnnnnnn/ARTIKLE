import logging
from typing import Any, Dict
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance"""
    return logging.getLogger(name)

def create_response(
    success: bool,
    message: str,
    data: Any = None,
    errors: list = None
) -> Dict[str, Any]:
    """Standardized API response format"""
    response = {
        "success": success,
        "message": message,
        "timestamp": datetime.now().isoformat()
    }
    
    if data is not None:
        response["data"] = data
    
    if errors is not None:
        response["errors"] = errors
    
    return response

# Import vector store components
try:
    from app.utils.vector_store import VectorStore, VectorStoreManager, vector_store_manager
except ImportError:
    # Define dummy classes if vector_store fails to import
    class VectorStore:
        pass
    
    class VectorStoreManager:
        pass
    
    vector_store_manager = None

__all__ = [
    "get_logger",
    "create_response",
    "VectorStore",
    "VectorStoreManager",
    "vector_store_manager"
]