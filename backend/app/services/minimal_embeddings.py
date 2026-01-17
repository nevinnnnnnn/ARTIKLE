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
        return text
    
    def create_embeddings(self, texts: List[str]) -> np.ndarray:
        """Create TF-IDF embeddings for texts"""
        logger.info(f"Creating embeddings for {len(texts)} texts")
        
        # Preprocess texts
        processed_texts = [self._preprocess_text(text) for text in texts]
        
        # Initialize vectorizer if not done
        if self.vectorizer is None:
            self.vectorizer = TfidfVectorizer(
                max_features=self.embedding_dim,
                stop_words='english',
                lowercase=False,  # Already lowercased
                ngram_range=(1, 2),
                min_df=1,  # Minimum document frequency
                max_df=0.95  # Maximum document frequency
            )
        
        # Fit and transform
        embeddings = self.vectorizer.fit_transform(processed_texts).toarray()
        
        # Normalize to unit vectors for cosine similarity
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1  # Avoid division by zero
        embeddings = embeddings / norms
        
        logger.info(f"Created embeddings with shape: {embeddings.shape}")
        return embeddings
    
    def create_single_embedding(self, text: str) -> np.ndarray:
        """Create embedding for a single text"""
        return self.create_embeddings([text])[0]
    
    def get_embedding_dimension(self) -> int:
        """Get the embedding dimension"""
        return self.embedding_dim

# Global instance
minimal_embedding_service = MinimalEmbeddingService()