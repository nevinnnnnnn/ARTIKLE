"""
Chat History Persistence Service
Stores and retrieves chat conversations for all users
"""
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.chat_history import ChatHistory

logger = logging.getLogger(__name__)


class ChatPersistenceService:
    """Handle chat history persistence for users"""
    
    @staticmethod
    def save_chat(
        db: Session,
        user_id: int,
        document_id: int,
        question: str,
        response: str,
        relevance_score: float = 0.0,
        context_chunks: int = 0
    ) -> ChatHistory:
        """Save a chat interaction to the database"""
        try:
            chat_record = ChatHistory(
                user_id=user_id,
                document_id=document_id,
                user_question=question,
                ai_response=response,
                relevance_score=relevance_score,
                context_chunks=context_chunks
            )
            db.add(chat_record)
            db.commit()
            db.refresh(chat_record)
            logger.info(f"✓ Chat saved for user {user_id}, doc {document_id}")
            return chat_record
        except Exception as e:
            logger.error(f"Failed to save chat: {e}")
            db.rollback()
            return None
    
    @staticmethod
    def get_chat_history(
        db: Session,
        user_id: int,
        document_id: Optional[int] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Retrieve chat history for a user"""
        try:
            query = db.query(ChatHistory).filter(ChatHistory.user_id == user_id)
            
            if document_id:
                query = query.filter(ChatHistory.document_id == document_id)
            
            chats = query.order_by(ChatHistory.created_at.desc()).limit(limit).all()
            
            # Convert to dict format
            chat_list = []
            for chat in reversed(chats):  # Reverse to show oldest first
                chat_list.append({
                    "id": chat.id,
                    "question": chat.user_question,
                    "response": chat.ai_response,
                    "relevance_score": chat.relevance_score,
                    "context_chunks": chat.context_chunks,
                    "timestamp": chat.created_at.isoformat() if chat.created_at else None
                })
            
            logger.info(f"✓ Retrieved {len(chat_list)} chats for user {user_id}")
            return chat_list
        except Exception as e:
            logger.error(f"Failed to retrieve chat history: {e}")
            return []
    
    @staticmethod
    def clear_chat_history(
        db: Session,
        user_id: int,
        document_id: Optional[int] = None
    ) -> bool:
        """Clear chat history for a user (optionally for specific document)"""
        try:
            query = db.query(ChatHistory).filter(ChatHistory.user_id == user_id)
            
            if document_id:
                query = query.filter(ChatHistory.document_id == document_id)
            
            count = query.delete()
            db.commit()
            logger.info(f"✓ Cleared {count} chat records for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to clear chat history: {e}")
            db.rollback()
            return False
    
    @staticmethod
    def get_chat_statistics(
        db: Session,
        user_id: int
    ) -> Dict[str, Any]:
        """Get chat statistics for a user"""
        try:
            total_chats = db.query(ChatHistory).filter(
                ChatHistory.user_id == user_id
            ).count()
            
            # Get average relevance score
            avg_score_result = db.query(
                ChatHistory.relevance_score
            ).filter(
                ChatHistory.user_id == user_id
            ).all()
            
            avg_relevance = sum(r[0] for r in avg_score_result) / len(avg_score_result) \
                if avg_score_result else 0.0
            
            # Get unique documents chatted about
            unique_docs = db.query(
                ChatHistory.document_id
            ).filter(
                ChatHistory.user_id == user_id
            ).distinct().count()
            
            return {
                "total_chats": total_chats,
                "average_relevance_score": round(avg_relevance, 2),
                "documents_chatted": unique_docs
            }
        except Exception as e:
            logger.error(f"Failed to get chat statistics: {e}")
            return {
                "total_chats": 0,
                "average_relevance_score": 0.0,
                "documents_chatted": 0
            }


# Create singleton instance
chat_persistence = ChatPersistenceService()
