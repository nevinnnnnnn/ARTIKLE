import logging
import numpy as np
from typing import List, Optional
import os
import pickle
import time
from transformers import AutoTokenizer, AutoModel
import torch
from app.config import settings

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self):
        self.model_name = settings.EMBEDDING_MODEL
        self.tokenizer = None
        self.model = None
        self.embedding_dim = None
        self.device = self._get_device()
        self.load_model()
    
    def _get_device(self):
        """Get the best available device (GPU if available, else CPU)"""
        if torch.cuda.is_available():
            logger.info("Using CUDA (GPU) for embeddings")
            return torch.device("cuda")
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            logger.info("Using MPS (Apple Silicon) for embeddings")
            return torch.device("mps")
        else:
            logger.info("Using CPU for embeddings")
            return torch.device("cpu")
    
    def load_model(self):
        """Load the embedding model using transformers"""
        try:
            logger.info(f"Loading embedding model: {self.model_name}")
            start_time = time.time()
            
            # Use a local cache directory
            cache_dir = os.path.join(settings.VECTOR_STORE_DIR, "model_cache")
            os.makedirs(cache_dir, exist_ok=True)
            
            # Load tokenizer and model
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                cache_dir=cache_dir
            )
            
            self.model = AutoModel.from_pretrained(
                self.model_name,
                cache_dir=cache_dir
            ).to(self.device)
            
            # Set model to evaluation mode
            self.model.eval()
            
            # Get embedding dimension from model config
            self.embedding_dim = self.model.config.hidden_size
            
            load_time = time.time() - start_time
            logger.info(f"Model loaded in {load_time:.2f}s. Embedding dimension: {self.embedding_dim}")
            
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            # Try a smaller fallback model
            logger.info("Trying fallback model: 'sentence-transformers/all-MiniLM-L6-v2'")
            try:
                self.model_name = 'sentence-transformers/all-MiniLM-L6-v2'
                cache_dir = os.path.join(settings.VECTOR_STORE_DIR, "model_cache")
                
                self.tokenizer = AutoTokenizer.from_pretrained(
                    self.model_name,
                    cache_dir=cache_dir
                )
                
                self.model = AutoModel.from_pretrained(
                    self.model_name,
                    cache_dir=cache_dir
                ).to(self.device)
                
                self.model.eval()
                self.embedding_dim = self.model.config.hidden_size
                
                logger.info(f"Fallback model loaded. Embedding dimension: {self.embedding_dim}")
            except Exception as e2:
                logger.error(f"Fallback model also failed: {e2}")
                raise
    
    def _mean_pooling(self, model_output, attention_mask):
        """Apply mean pooling to get sentence embeddings"""
        token_embeddings = model_output.last_hidden_state
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        sum_embeddings = torch.sum(token_embeddings * input_mask_expanded, 1)
        sum_mask = torch.clamp(input_mask_expanded.sum(1), min=1e-9)
        return sum_embeddings / sum_mask
    
    def create_embeddings(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """Create embeddings for a list of texts"""
        if not self.model or not self.tokenizer:
            self.load_model()
        
        try:
            logger.info(f"Creating embeddings for {len(texts)} texts")
            start_time = time.time()
            
            all_embeddings = []
            
            # Process in batches to avoid memory issues
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                
                # Tokenize
                encoded_input = self.tokenizer(
                    batch_texts,
                    padding=True,
                    truncation=True,
                    max_length=512,
                    return_tensors='pt'
                ).to(self.device)
                
                # Generate embeddings
                with torch.no_grad():
                    model_output = self.model(**encoded_input)
                
                # Mean pooling
                batch_embeddings = self._mean_pooling(
                    model_output, 
                    encoded_input['attention_mask']
                )
                
                # Normalize embeddings
                batch_embeddings = torch.nn.functional.normalize(batch_embeddings, p=2, dim=1)
                
                all_embeddings.append(batch_embeddings.cpu().numpy())
            
            # Combine all batches
            embeddings = np.vstack(all_embeddings)
            
            embed_time = time.time() - start_time
            logger.info(f"Created {len(texts)} embeddings in {embed_time:.2f}s")
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Error creating embeddings: {e}")
            raise
    
    def create_single_embedding(self, text: str) -> np.ndarray:
        """Create embedding for a single text"""
        return self.create_embeddings([text])[0]
    
    def get_embedding_dimension(self) -> int:
        """Get the embedding dimension"""
        if not self.embedding_dim:
            # Create a test embedding to get dimension
            test_embedding = self.create_single_embedding("test")
            self.embedding_dim = test_embedding.shape[0]
        return self.embedding_dim

# Global instance
embedding_service = EmbeddingService()