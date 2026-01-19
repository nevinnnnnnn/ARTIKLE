"""
Optimized Embedding Service - Fast & Lightweight
"""
import logging
import numpy as np
from typing import List
import os
import warnings
from app.config import settings

logger = logging.getLogger(__name__)

# Suppress verbose library warnings
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Suppress huggingface warnings
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["TRANSFORMERS_CACHE"] = os.path.join(settings.VECTOR_STORE_DIR, "model_cache")

# Flag for sentence-transformers availability
HAS_SENTENCE_TRANSFORMERS = False

try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
    logger.info("✓ Embedding model (sentence-transformers) loaded successfully")
except (ImportError, OSError, Exception) as e:
    logger.debug(f"sentence-transformers unavailable, using fallback: {type(e).__name__}")

class FastEmbeddingService:
    def __init__(self):
        self.model_name = "all-MiniLM-L6-v2"
        self.model = None
        self.embedding_dim = 384
        self.load_model()
    
    def load_model(self):
        """Load the embedding model - optimized version"""
        try:
            if HAS_SENTENCE_TRANSFORMERS:
                logger.debug(f"Loading embedding model: {self.model_name}")
                
                # Use cache directory
                cache_dir = os.path.join(settings.VECTOR_STORE_DIR, "model_cache")
                os.makedirs(cache_dir, exist_ok=True)
                
                # Suppress transformer logging during load
                transformers_logger = logging.getLogger("transformers")
                old_level = transformers_logger.level
                transformers_logger.setLevel(logging.ERROR)
                
                try:
                    # Load with sentence-transformers (already optimized)
                    self.model = SentenceTransformer(
                        self.model_name,
                        cache_folder=cache_dir,
                        device="cpu"  # Use CPU for better compatibility
                    )
                    
                    self.embedding_dim = self.model.get_sentence_embedding_dimension()
                    logger.info(f"✓ Embedding model ready (dimension: {self.embedding_dim})")
                finally:
                    transformers_logger.setLevel(old_level)
            else:
                # Fallback to simple hash-based embeddings (for demo/testing)
                logger.info("✓ Using fallback embedding method (hash-based, dimension: 384)")
                self.embedding_dim = 384
                
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            logger.info("✓ Using fallback embedding method (hash-based, dimension: 384)")
            self.embedding_dim = 384
    
    def _create_fallback_embeddings(self, texts: List[str]) -> np.ndarray:
        """Create simple hash-based embeddings as fallback"""
        embeddings = []
        for text in texts:
            # Create a simple embedding by hashing the text
            # This is not ML-based but works for vector store operations
            hash_val = hash(text) & 0x7FFFFFFF  # Make positive
            # Create embedding by using hash to seed random-like values
            np.random.seed(hash_val % (2**31))
            embedding = np.random.randn(self.embedding_dim).astype(np.float32)
            # Normalize
            embedding = embedding / (np.linalg.norm(embedding) + 1e-8)
            embeddings.append(embedding)
        return np.array(embeddings)
    
    def create_embeddings(self, texts: List[str]) -> np.ndarray:
        """Create embeddings for texts - fast version"""
        if not texts:
            return np.array([]).reshape(0, self.embedding_dim)
        
        try:
            if HAS_SENTENCE_TRANSFORMERS and self.model is not None:
                # Batch encode for efficiency
                embeddings = self.model.encode(
                    texts,
                    batch_size=64,  # Larger batch for faster processing
                    show_progress_bar=False,
                    convert_to_numpy=True
                )
            else:
                # Use fallback
                embeddings = self._create_fallback_embeddings(texts)
            
            logger.info(f"Created {len(embeddings)} embeddings")
            return embeddings
            
        except Exception as e:
            logger.error(f"Error creating embeddings: {e}")
            logger.info("Falling back to hash-based embeddings")
            return self._create_fallback_embeddings(texts)
    
    def create_single_embedding(self, text: str) -> np.ndarray:
        """Create embedding for a single text"""
        try:
            if HAS_SENTENCE_TRANSFORMERS and self.model is not None:
                embedding = self.model.encode(
                    text,
                    convert_to_numpy=True
                )
            else:
                embedding = self._create_fallback_embeddings([text])[0]
            return embedding
        except Exception as e:
            logger.error(f"Error creating single embedding: {e}")
            return self._create_fallback_embeddings([text])[0]
    
    def get_embedding_dimension(self) -> int:
        """Get the embedding dimension"""
        return self.embedding_dim


# Create singleton instance
embedding_service = FastEmbeddingService()

