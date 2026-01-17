import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.api import auth, users, documents, chat  # Add chat
from app.auth.dependencies import require_user, require_admin, require_superadmin

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="PDF AI Chatbot API",
    description="Backend API for PDF-based AI chatbot system",
    version="1.0.0"
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Will be restricted in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")  # Add chat router

@app.get("/")
async def root():
    return {
        "message": "PDF AI Chatbot API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "pdf-chatbot-api",
        "database": "connected"
    }

@app.get("/api/v1/public/test")
async def public_test():
    """Public endpoint for testing without authentication"""
    return {
        "message": "This is a public endpoint",
        "status": "accessible"
    }

@app.get("/api/v1/protected/test")
async def protected_test(
    current_user = Depends(require_user)
):
    """Protected endpoint for testing authentication"""
    return {
        "message": f"Hello {current_user.username}!",
        "role": current_user.role.value,
        "status": "authenticated"
    }

@app.get("/api/v1/admin/test")
async def admin_test(
    current_user = Depends(require_admin)
):
    """Admin-only endpoint for testing role-based access"""
    return {
        "message": f"Welcome Admin {current_user.username}!",
        "role": current_user.role.value,
        "status": "admin_authorized"
    }

@app.get("/api/v1/superadmin/test")
async def superadmin_test(
    current_user = Depends(require_superadmin)
):
    """Superadmin-only endpoint for testing role-based access"""
    return {
        "message": f"Welcome Superadmin {current_user.username}!",
        "role": current_user.role.value,
        "status": "superadmin_authorized"
    }