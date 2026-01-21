#!/usr/bin/env python
"""Run the FastAPI backend server"""

import os
import sys
import uvicorn

# Ensure we're in the right directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # No reload on Windows due to multiprocessing issues
        log_level="info"
    )
