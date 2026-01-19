import logging
from typing import List, Dict, Any, Optional, Generator

logger = logging.getLogger(__name__)

class ChatService:
    def __init__(self):
        self.relevance_threshold = 0.01  # Very low threshold - retrieve most content
        self.hallucination_warnings = [
            "i cannot find", "not in the document", "not mentioned", "unclear",
            "not certain", "unable to determine", "not specified", "insufficient information"
        ]
        
    def retrieve_context(self, document_id: int, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Retrieve relevant context from document"""
        try:
            # Import inside method to avoid circular import
            from app.utils.vector_store import vector_store_manager
            vector_store = vector_store_manager.get_store(document_id)
            results = vector_store.similarity_search(query, k=top_k, threshold=self.relevance_threshold)
            
            # Format results
            context_chunks = []
            for metadata, similarity in results:
                context_chunks.append({
                    "chunk_id": metadata["chunk_id"],
                    "chunk_index": metadata["chunk_index"],
                    "page_number": metadata.get("page_number"),
                    "text": metadata.get("text_preview", "").replace("...", ""),
                    "similarity_score": similarity
                })
            
            logger.info(f"Retrieved {len(context_chunks)} context chunks for query: {query[:50]}...")
            return context_chunks
            
        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            return []
    
    def is_query_relevant(self, context_chunks: List[Dict[str, Any]]) -> bool:
        """Check if query is relevant to the document"""
        # Always return true - let the model decide relevance
        return len(context_chunks) > 0
    
    def detect_hallucination(self, response: str, context_chunks: List[Dict[str, Any]]) -> bool:
        """Detect if response might be a hallucination"""
        response_lower = response.lower()
        
        # Check for hallucination indicators
        for warning in self.hallucination_warnings:
            if warning in response_lower:
                return True
        
        # If response is very different from context, might be hallucination
        if context_chunks:
            context_text = " ".join([c["text"].lower() for c in context_chunks])
            # Check if key terms from context appear in response (simple check)
            context_words = set(context_text.split())
            response_words = set(response_lower.split())
            # If very few context words in response, suspicious
            intersection = len(context_words & response_words)
            if intersection < 3 and len(response) > 50:
                return True
        
        return False
    
    def format_prompt(self, query: str, context_chunks: List[Dict[str, Any]]) -> str:
        """Format the prompt for RAG"""
        
        # Combine context chunks
        context_text = ""
        for i, chunk in enumerate(context_chunks, 1):
            page_info = f" [Page {chunk['page_number']}]" if chunk.get('page_number') else ""
            context_text += f"{chunk['text']}\n\n"
        
        # Simple, effective prompt
        prompt = f"""Based on the document content below, answer the user's question. Be direct and helpful.

Document content:
{context_text}

Question: {query}

Answer:"""
        
        return prompt
    
    def generate_response(self, query: str, context_chunks: List[Dict[str, Any]]) -> Generator[str, None, None]:
        """Generate AI response based on context"""
        try:
            from app.services.ollama_generator import ollama_generator

            # Use all available context - don't limit to top 3
            if not context_chunks:
                yield "I couldn't find information in the document to answer your question."
                return
            
            # Build context text from all chunks
            context_text = ""
            for chunk in context_chunks:
                context_text += f"{chunk['text']}\n\n"

            logger.info(f"Generating response for: {query[:50]}... (using {len(context_chunks)} context chunks)")

            # Generate response
            full_response = ""
            for token in ollama_generator.generate_response(context_text, query):
                full_response += token
                yield token

        except Exception as e:
            logger.error(f"Error generating response: {e}", exc_info=True)
            yield f"Error: {str(e)}"
    
    def get_chat_response(self, document_id: int, query: str, stream: bool = True) -> Dict[str, Any]:
        """Main method to get chat response"""
        
        # Retrieve context
        context_chunks = self.retrieve_context(document_id, query)
        
        # Check relevance
        is_relevant = self.is_query_relevant(context_chunks)
        
        # Prepare response metadata
        metadata = {
            "document_id": document_id,
            "query": query,
            "is_relevant": is_relevant,
            "context_chunks_retrieved": len(context_chunks),
            "top_similarity_score": max([c["similarity_score"] for c in context_chunks]) if context_chunks else 0
        }
        
        if stream:
            return {
                "metadata": metadata,
                "stream_generator": self.generate_response(query, context_chunks)
            }
        else:
            # For non-streaming, collect all generated text
            response_text = ""
            for chunk in self.generate_response(query, context_chunks):
                response_text += chunk
            
            return {
                "metadata": metadata,
                "response": response_text.strip()
            }

# Global instance
chat_service = ChatService()