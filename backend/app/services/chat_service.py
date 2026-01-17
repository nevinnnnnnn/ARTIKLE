import logging
from typing import List, Dict, Any, Optional, Generator

logger = logging.getLogger(__name__)

class ChatService:
    def __init__(self):
        self.relevance_threshold = 0.3  # Minimum similarity score for relevance
        
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
        if not context_chunks:
            return False
        
        # Check if any chunk has similarity above threshold
        for chunk in context_chunks:
            if chunk["similarity_score"] >= self.relevance_threshold:
                return True
        
        return False
    
    def format_prompt(self, query: str, context_chunks: List[Dict[str, Any]]) -> str:
        """Format the prompt with strict instructions"""
        
        # Combine context chunks
        context_text = ""
        for i, chunk in enumerate(context_chunks, 1):
            page_info = f" [Page {chunk['page_number']}]" if chunk.get('page_number') else ""
            context_text += f"[Context {i}{page_info}]: {chunk['text']}\n\n"
        
        # Strict prompt template
        prompt = f"""You are a helpful assistant that answers questions based ONLY on the provided document context.

DOCUMENT CONTEXT:
{context_text}

USER QUESTION: {query}

STRICT RULES:
1. Answer the question using ONLY information from the document context above.
2. If the answer is not found in the context, respond with: "The question is irrelevant to the document content."
3. Do not use any external knowledge or make assumptions.
4. If the context contains the answer, provide it clearly and concisely.
5. Reference specific context numbers [Context X] when possible.
6. Do not mention that you're using context or following rules.

ANSWER:"""
        
        return prompt
    
    def generate_response(self, query: str, context_chunks: List[Dict[str, Any]]) -> Generator[str, None, None]:
        """Generate response based on context (simulated for now - will integrate with actual LLM later)"""
        
        if not self.is_query_relevant(context_chunks):
            yield "The question is irrelevant to the document content."
            return
        
        # Simulate AI response generation
        # Extract key information from context
        relevant_info = []
        for chunk in context_chunks:
            if chunk["similarity_score"] >= self.relevance_threshold:
                relevant_info.append(chunk["text"])
        
        # Simple rule-based response for demonstration
        if relevant_info:
            response_parts = [
                "Based on the document:",
                "",
                f"{relevant_info[0][:300]}...",
                "",
                "This information addresses your question from the provided context."
            ]
            
            for part in response_parts:
                yield part + "\n"
        else:
            yield "The question is irrelevant to the document content."
    
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