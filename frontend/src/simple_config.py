"""
Simple configuration without properties
"""

import yaml
from pathlib import Path

# Default values
DEFAULTS = {
    "backend_url": "http://localhost:8000",
    "page_title": "PDF AI Chatbot",
    "page_icon": "🤖",
    "layout": "wide",
    "initial_sidebar_state": "expanded"
}

def load_config():
    """Load configuration from YAML file"""
    config_path = Path("config.yaml")
    
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                user_config = yaml.safe_load(f) or {}
                config = {**DEFAULTS, **user_config}
        except Exception as e:
            print(f"Warning: Could not load config.yaml: {e}")
            config = DEFAULTS.copy()
    else:
        config = DEFAULTS.copy()
    
    return config

# Load configuration
_config = load_config()

# Export config values
BACKEND_URL = _config["backend_url"]
PAGE_TITLE = _config["page_title"]
PAGE_ICON = _config["page_icon"]
LAYOUT = _config["layout"]
INITIAL_SIDEBAR_STATE = _config["initial_sidebar_state"]