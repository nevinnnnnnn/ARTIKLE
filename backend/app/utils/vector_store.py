import numpy as np
import pickle
import os
import logging
from typing import List, Tuple, Optional, Dict, Any
from datetime import datetime
from sklearn.metrics.pairwise import cosine_similarity
from app.config import settings
from app.services.embeddings import embedding_service

logger = logging.getLogger(__name__)

class VectorStore:
    """Vector store using numpy arrays for similarity search"""
    
    def __init__(self, document_id: int):
        self.document_id = document_id
        self.store_dir = settings.VECTOR_STORE_DIR
        self.embeddings_path = os.path.join(self.store_dir, f"doc_{document_id}_embeddings.npy")
        self.metadata_path = os.path.join(self.store_dir, f"doc_{document_id}_metadata.pkl")
        
        os.makedirs(self.store_dir, exist_ok=True)
        
        self.embeddings = None
        self.metadata = []
        self.load()
    
    def load(self):
        """Load existing vector store if it exists"""
        if os.path.exists(self.embeddings_path) and os.path.exists(self.metadata_path):
            try:
                logger.info(f"Loading vector store for document {self.document_id}")
                
                # Load embeddings
                self.embeddings = np.load(self.embeddings_path)
                
                # Load metadata
                with open(self.metadata_path, 'rb') as f:
                    self.metadata = pickle.load(f)
                
                logger.info(f"Loaded vector store with {len(self.metadata)} vectors")
                
            except Exception as e:
                logger.error(f"Error loading vector store: {e}")
                self._initialize_new_store()
        else:
            self._initialize_new_store()
    
    def _initialize_new_store(self):
        """Initialize a new empty vector store"""
        # Initialize with correct dimension
        embedding_dim = embedding_service.get_embedding_dimension()
        self.embeddings = np.array([]).reshape(0, embedding_dim)
        self.metadata = []
        
        logger.info(f"Initialized new vector store for document {self.document_id}")
    
    def add_embeddings(self, embeddings: np.ndarray, metadata_list: List[Dict[str, Any]]):
        """Add embeddings and their metadata to the vector store"""
        if len(embeddings) != len(metadata_list):
            raise ValueError("Number of embeddings must match number of metadata entries")
        
        if self.embeddings.size == 0:
            self.embeddings = embeddings
        else:
            self.embeddings = np.vstack([self.embeddings, embeddings])
        
        self.metadata.extend(metadata_list)
        
        logger.info(f"Added {len(embeddings)} vectors to document {self.document_id}")
    
    def add_texts(self, texts: List[str], metadata_list: List[Dict[str, Any]]):
        """Add texts by creating embeddings and storing them"""
        embeddings = embedding_service.create_embeddings(texts)
        self.add_embeddings(embeddings, metadata_list)
    
    def similarity_search(self, query: str, k: int = 5, threshold: float = 0.5) -> List[Tuple[Dict[str, Any], float]]:
        """Search for similar texts using cosine similarity"""
        if len(self.embeddings) == 0:
            return []
        
        # Create embedding for query
        query_embedding = embedding_service.create_single_embedding(query)
        query_embedding = query_embedding.reshape(1, -1)
        
        # Calculate cosine similarity
        similarities = cosine_similarity(query_embedding, self.embeddings)[0]
        
        # Get top k results above threshold
        top_indices = np.argsort(similarities)[::-1][:k]
        
        results = []
        for idx in top_indices:
            similarity = float(similarities[idx])
            if similarity >= threshold:
                results.append((self.metadata[idx], similarity))
        
        logger.info(f"Found {len(results)} similar texts for query: '{query[:50]}...'")
        return results
    
    def save(self):
        """Save the vector store to disk"""
        try:
            # Save embeddings
            np.save(self.embeddings_path, self.embeddings)
            
            # Save metadata
            with open(self.metadata_path, 'wb') as f:
                pickle.dump(self.metadata, f)
            
            logger.info(f"Saved vector store for document {self.document_id}")
            
        except Exception as e:
            logger.error(f"Error saving vector store: {e}")
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store"""
        embedding_dim = self.embeddings.shape[1] if self.embeddings.size > 0 else 0
        return {
            "document_id": self.document_id,
            "vector_count": len(self.metadata),
            "embedding_dimension": embedding_dim,
            "index_type": "numpy array with cosine similarity",
            "last_updated": datetime.now().isoformat()
        }
    
    def clear(self):
        """Clear the vector store"""
        embedding_dim = embedding_service.get_embedding_dimension()
        self.embeddings = np.array([]).reshape(0, embedding_dim)
        self.metadata = []
        
        # Remove saved files
        if os.path.exists(self.embeddings_path):
            os.remove(self.embeddings_path)
        if os.path.exists(self.metadata_path):
            os.remove(self.metadata_path)
        
        logger.info(f"Cleared vector store for document {self.document_id}")


class VectorStoreManager:
    """Manager for multiple vector stores"""
    
    def __init__(self):
        self.store_dir = settings.VECTOR_STORE_DIR
        os.makedirs(self.store_dir, exist_ok=True)
        self.stores = {}  # document_id -> VectorStore
    
    def get_store(self, document_id: int) -> VectorStore:
        """Get or create vector store for a document"""
        if document_id not in self.stores:
            self.stores[document_id] = VectorStore(document_id)
        return self.stores[document_id]
    
    def save_all(self):
        """Save all vector stores"""
        for store in self.stores.values():
            store.save()
    
    def get_all_stats(self) -> Dict[int, Dict[str, Any]]:
        """Get statistics for all vector stores"""
        stats = {}
        for doc_id, store in self.stores.items():
            stats[doc_id] = store.get_stats()
        return stats
    
    def delete_store(self, document_id: int):
        """Delete vector store for a document"""
        if document_id in self.stores:
            self.stores[document_id].clear()
            del self.stores[document_id]
            logger.info(f"Deleted vector store for document {document_id}")

# Global instance
vector_store_manager = VectorStoreManager()