import logging
import numpy as np
from typing import List
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from app.config import settings

logger = logging.getLogger(__name__)

class MinimalEmbeddingService:
    """Minimal embedding service using TF-IDF - no external model downloads"""
    
    def __init__(self):
        self.embedding_dim = 384  # Fixed dimension
        self.vectorizer = None
        logger.info(f"Initialized minimal embedding service (dimension: {self.embedding_dim})")
    
    def _preprocess_text(self, text: str) -> str:
        """Simple text preprocessing"""
        # Convert to lowercase
        text = text.lower()
        # Remove extra whitespace
        text = ' '.join(text.split())
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s.,!?]', '', text)
        return text
    
    def create_embeddings(self, texts: List[str]) -> np.ndarray:
        """Create TF-IDF embeddings for texts"""
        logger.info(f"Creating embeddings for {len(texts)} texts")
        
        if len(texts) == 0:
            logger.warning("No texts to create embeddings for")
            return np.array([]).reshape(0, self.embedding_dim)
        
        # Preprocess texts
        processed_texts = [self._preprocess_text(text) for text in texts]
        
        # Initialize vectorizer if not done
        if self.vectorizer is None:
            # Use parameters that work with small datasets
            self.vectorizer = TfidfVectorizer(
                max_features=self.embedding_dim,
                stop_words='english',
                lowercase=False,  # Already lowercased
                ngram_range=(1, 2),
                min_df=1,  # Minimum document frequency - allow terms that appear in at least 1 document
                max_df=1.0,  # Maximum document frequency - allow terms that appear in all documents
                norm='l2'
            )
        
        try:
            # Fit and transform
            embeddings = self.vectorizer.fit_transform(processed_texts).toarray()
            
            # If we have fewer texts than embedding dimension, pad with zeros
            if embeddings.shape[1] < self.embedding_dim:
                padding = np.zeros((embeddings.shape[0], self.embedding_dim - embeddings.shape[1]))
                embeddings = np.hstack([embeddings, padding])
            
            # Normalize to unit vectors for cosine similarity
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            norms[norms == 0] = 1  # Avoid division by zero
            embeddings = embeddings / norms
            
            logger.info(f"Created embeddings with shape: {embeddings.shape}")
            return embeddings
            
        except Exception as e:
            logger.error(f"Error creating embeddings: {e}")
            # Fallback: create random embeddings (for testing only)
            logger.warning("Using random embeddings as fallback")
            embeddings = np.random.randn(len(texts), self.embedding_dim)
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            embeddings = embeddings / norms
            return embeddings
    
    def create_single_embedding(self, text: str) -> np.ndarray:
        """Create embedding for a single text"""
        return self.create_embeddings([text])[0]
    
    def get_embedding_dimension(self) -> int:
        """Get the embedding dimension"""
        return self.embedding_dim

# Global instance
minimal_embedding_service = MinimalEmbeddingService()