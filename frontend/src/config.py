import os
import yaml
from pathlib import Path
from typing import Dict, Any

class Config:
    """Configuration manager for the frontend"""
    
    # Default configuration
    DEFAULTS = {
        "backend_url": "http://localhost:8000",
        "page_title": "PDF AI Chatbot",
        "page_icon": "🤖",
        "layout": "wide",
        "initial_sidebar_state": "expanded",
        "max_file_size_mb": 50,
        "allowed_file_types": [".pdf"],
        "chunk_size": 1000,
        "similarity_threshold": 0.5
    }
    
    def __init__(self):
        self._config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        config_path = Path("config.yaml")
        
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    user_config = yaml.safe_load(f) or {}
                    return {**self.DEFAULTS, **user_config}
            except Exception as e:
                print(f"Warning: Could not load config.yaml: {e}")
                return self.DEFAULTS.copy()
        
        return self.DEFAULTS.copy()
    
    def get(self, key: str, default=None):
        """Get configuration value"""
        return self._config.get(key, default)
    
    # Properties for convenient access
    @property
    def BACKEND_URL(self):
        return self.get("backend_url")
    
    @property
    def PAGE_TITLE(self):
        return self.get("page_title")
    
    @property
    def PAGE_ICON(self):
        return self.get("page_icon")
    
    @property
    def LAYOUT(self):
        return self.get("layout")
    
    @property
    def INITIAL_SIDEBAR_STATE(self):
        return self.get("initial_sidebar_state")
    
    @property
    def MAX_FILE_SIZE_MB(self):
        return self.get("max_file_size_mb")
    
    @property
    def ALLOWED_FILE_TYPES(self):
        return self.get("allowed_file_types")
    
    @property
    def CHUNK_SIZE(self):
        return self.get("chunk_size")
    
    @property
    def SIMILARITY_THRESHOLD(self):
        return self.get("similarity_threshold")

# Create global config instance
config = Config()