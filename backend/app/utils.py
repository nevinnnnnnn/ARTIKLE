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