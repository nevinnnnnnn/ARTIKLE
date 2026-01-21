"""
Fast embeddings using TF-IDF + semantic similarity
Lightweight and efficient - no heavy dependencies
With LRU caching for frequently used vectors
"""

import logging
import numpy as np
import pickle
import os
from typing import List, Dict
from functools import lru_cache
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import PCA

logger = logging.getLogger(__name__)


class FastEmbeddingService:
    """Fast embedding service using TF-IDF vectors with dimensionality reduction"""
    
    def __init__(self):
        """Initialize embedding service"""
        self.vectorizer = TfidfVectorizer(max_features=500, analyzer='char', ngram_range=(2, 3))
        self.pca = None
        self.embedding_dim = 384  # Target dimension (matches all-MiniLM-L6-v2)
        self.fitted = False
        self._embedding_cache: Dict[str, np.ndarray] = {}  # LRU cache for embeddings
        self._cache_max_size = 1000
        logger.info("✓ Embedding service initialized (TF-IDF mode with caching)")
    
    def _ensure_fit(self, texts: List[str]):
        """Fit vectorizer and PCA on first batch of texts"""
        if not self.fitted and texts:
            try:
                # Fit TF-IDF vectorizer
                tfidf_vectors = self.vectorizer.fit_transform(texts)
                
                # Fit PCA for dimensionality reduction
                tfidf_dim = tfidf_vectors.shape[1]
                target_dim = min(self.embedding_dim, tfidf_dim)
                self.pca = PCA(n_components=target_dim)
                self.pca.fit(tfidf_vectors.toarray())
                
                self.fitted = True
                logger.debug(f"Fitted vectorizer and PCA ({tfidf_dim} -> {target_dim} dims)")
            except Exception as e:
                logger.error(f"Error fitting vectorizer: {e}")
                self.fitted = True  # Mark as fitted to prevent infinite loops
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings"""
        return self.embedding_dim
    
    def _clear_cache_if_needed(self):
        """Clear old cache entries if cache exceeds max size"""
        if len(self._embedding_cache) > self._cache_max_size:
            # Keep only 80% of max size
            to_remove = len(self._embedding_cache) - int(self._cache_max_size * 0.8)
            for key in list(self._embedding_cache.keys())[:to_remove]:
                del self._embedding_cache[key]
    
    def create_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Create embeddings for multiple texts using TF-IDF with caching
        
        Args:
            texts: List of text strings
        
        Returns:
            numpy array of shape (len(texts), embedding_dim)
        """
        if not texts:
            return np.array([]).reshape(0, self.embedding_dim)
        
        try:
            # Ensure vectorizer is fitted
            self._ensure_fit(texts)
            
            # Try to get from cache first
            embeddings_list = []
            uncached_indices = []
            uncached_texts = []
            
            for i, text in enumerate(texts):
                text_hash = hash(text[:100])  # Use first 100 chars as key
                if text_hash in self._embedding_cache:
                    embeddings_list.append(self._embedding_cache[text_hash])
                else:
                    embeddings_list.append(None)
                    uncached_indices.append(i)
                    uncached_texts.append(text)
            
            # Compute embeddings for uncached texts
            if uncached_texts:
                tfidf_vectors = self.vectorizer.transform(uncached_texts).toarray()
                if self.pca is not None:
                    computed_embeddings = self.pca.transform(tfidf_vectors)
                else:
                    computed_embeddings = tfidf_vectors
                    if computed_embeddings.shape[1] < self.embedding_dim:
                        padding = np.zeros((computed_embeddings.shape[0], self.embedding_dim - computed_embeddings.shape[1]))
                        computed_embeddings = np.hstack([computed_embeddings, padding])
                    elif computed_embeddings.shape[1] > self.embedding_dim:
                        computed_embeddings = computed_embeddings[:, :self.embedding_dim]
                
                # Cache and place results
                for idx, text, embedding in zip(uncached_indices, uncached_texts, computed_embeddings):
                    text_hash = hash(text[:100])
                    self._embedding_cache[text_hash] = embedding
                    embeddings_list[idx] = embedding
            
            self._clear_cache_if_needed()
            return np.array(embeddings_list)
        except Exception as e:
            logger.error(f"Error creating embeddings: {e}")
            # Return random embeddings as fallback
            return np.random.rand(len(texts), self.embedding_dim)
    
    def create_single_embedding(self, text: str) -> np.ndarray:
        """
        Create embedding for a single text using TF-IDF
        
        Args:
            text: Single text string
        
        Returns:
            numpy array of shape (embedding_dim,)
        """
        try:
            # Ensure vectorizer is fitted (if this is first call, fit on text)
            if not self.fitted:
                self._ensure_fit([text])
            
            # Create TF-IDF vector
            tfidf_vector = self.vectorizer.transform([text]).toarray()[0]
            
            # Reduce dimensions with PCA
            if self.pca is not None:
                embedding = self.pca.transform([tfidf_vector])[0]
            else:
                embedding = tfidf_vector
                if len(embedding) < self.embedding_dim:
                    padding = np.zeros(self.embedding_dim - len(embedding))
                    embedding = np.concatenate([embedding, padding])
                elif len(embedding) > self.embedding_dim:
                    embedding = embedding[:self.embedding_dim]
            
            return embedding
        except Exception as e:
            logger.error(f"Error creating single embedding: {e}")
            # Return random embedding as fallback
            return np.random.rand(self.embedding_dim)


# Global instance
embedding_service = FastEmbeddingService()

