"""
Gemini Service - Handles embeddings and LLM chat via Google's Gemini API
"""

import google.generativeai as genai
from functools import lru_cache
from typing import List
import os
from app.config import settings

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", settings.gemini_api_key if hasattr(settings, 'gemini_api_key') else None)
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


class GeminiEmbeddings:
    """Generate embeddings using Google Gemini API"""
    
    MODEL_NAME = "models/embedding-001"
    DIMENSION = 768  # Gemini embedding dimension
    
    @staticmethod
    @lru_cache(maxsize=1024)
    def create_embedding(text: str) -> List[float]:
        """
        Create an embedding for the given text using Gemini API
        
        Args:
            text: The text to embed
            
        Returns:
            List of float values representing the embedding
        """
        try:
            result = genai.embed_content(
                model=GeminiEmbeddings.MODEL_NAME,
                content=text,
                task_type="retrieval_document",
                title="Document"
            )
            return result['embedding']
        except Exception as e:
            print(f"Error generating embedding: {e}")
            raise
    
    @staticmethod
    def get_dimension() -> int:
        """Get the dimension of Gemini embeddings"""
        return GeminiEmbeddings.DIMENSION


class GeminiChat:
    """Handle LLM chat responses using Google Gemini API"""
    
    MODEL_NAME = "gemini-1.5-flash"  # Fast model for quick responses
    
    @staticmethod
    def generate_response(
        query: str,
        context_text: str,
        temperature: float = 0.3,
        max_tokens: int = 1024
    ) -> str:
        """
        Generate a response using Gemini API with provided context
        
        Args:
            query: The user's question
            context_text: The retrieved context from documents
            temperature: Controls randomness (0.0 to 1.0)
            max_tokens: Maximum length of response
            
        Returns:
            The generated response as a string
        """
        try:
            system_prompt = """You are a helpful assistant that answers questions based ONLY on the provided context. 
If the answer is not in the context, clearly state that you don't have that information.
Do not make up or hallucinate information.
Provide accurate, concise answers directly from the context provided."""
            
            full_prompt = f"""Context from documents:
{context_text}

User Question: {query}

Answer the question using ONLY the context provided above. If the answer is not in the context, say you don't have that information."""
            
            model = genai.GenerativeModel(
                model_name=GeminiChat.MODEL_NAME,
                system_instruction=system_prompt,
                generation_config={
                    "temperature": temperature,
                    "top_p": 0.9,
                    "top_k": 30,
                    "max_output_tokens": max_tokens,
                }
            )
            
            response = model.generate_content(full_prompt)
            
            if response.text:
                return response.text
            else:
                return "I couldn't generate a response. Please try again."
                
        except Exception as e:
            print(f"Error generating response: {e}")
            raise


# Convenience functions for backward compatibility
def create_embeddings(text: str) -> List[float]:
    """Create embeddings using Gemini"""
    return GeminiEmbeddings.create_embedding(text)


def get_embedding_dimension() -> int:
    """Get Gemini embedding dimension"""
    return GeminiEmbeddings.get_dimension()


def generate_response(
    query: str,
    context_text: str,
    temperature: float = 0.3,
    max_tokens: int = 1024
) -> str:
    """Generate a chat response using Gemini"""
    return GeminiChat.generate_response(query, context_text, temperature, max_tokens)
