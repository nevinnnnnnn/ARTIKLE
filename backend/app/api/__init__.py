from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.documents import router as documents_router
from app.api.chat import router as chat_router

__all__ = ["auth_router", "users_router", "documents_router", "chat_router"]