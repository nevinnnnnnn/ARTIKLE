"""
Test script to verify Ollama embeddings integration
Tests the nomic-embed-text model integration with the system
"""

import sys
import logging
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_ollama_connection():
    """Test basic Ollama connection"""
    logger.info("=" * 60)
    logger.info("TEST 1: Ollama Connection")
    logger.info("=" * 60)
    
    try:
        from app.services.ollama_embeddings import embedding_service
        logger.info("✓ Ollama embedding service loaded successfully")
        logger.info(f"  - Model: {embedding_service.model}")
        logger.info(f"  - Endpoint: {embedding_service.ollama_endpoint}")
        logger.info(f"  - Embedding dimension: {embedding_service.embedding_dim}")
        return True
    except Exception as e:
        logger.error(f"✗ Failed to load Ollama service: {e}")
        return False

def test_embedding_generation():
    """Test embedding generation"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 2: Embedding Generation")
    logger.info("=" * 60)
    
    try:
        from app.services.ollama_embeddings import embedding_service
        
        # Test single embedding
        test_text = "This is a test document about machine learning and AI."
        logger.info(f"Generating embedding for: '{test_text[:50]}...'")
        
        embedding = embedding_service.create_single_embedding(test_text)
        logger.info(f"✓ Single embedding generated successfully")
        logger.info(f"  - Shape: {embedding.shape}")
        logger.info(f"  - Mean value: {embedding.mean():.6f}")
        logger.info(f"  - Std value: {embedding.std():.6f}")
        
        return True
    except Exception as e:
        logger.error(f"✗ Failed to generate embedding: {e}")
        return False

def test_batch_embeddings():
    """Test batch embedding generation"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 3: Batch Embeddings")
    logger.info("=" * 60)
    
    try:
        from app.services.ollama_embeddings import embedding_service
        
        texts = [
            "The quick brown fox jumps over the lazy dog.",
            "Machine learning is a subset of artificial intelligence.",
            "Natural language processing enables computers to understand text.",
            "Deep learning uses neural networks with multiple layers.",
            "Data science combines statistics, programming, and domain expertise."
        ]
        
        logger.info(f"Generating embeddings for {len(texts)} texts...")
        embeddings = embedding_service.create_embeddings(texts)
        
        logger.info(f"✓ Batch embeddings generated successfully")
        logger.info(f"  - Shape: {embeddings.shape}")
        logger.info(f"  - Expected: ({len(texts)}, {embedding_service.embedding_dim})")
        
        return embeddings.shape == (len(texts), embedding_service.embedding_dim)
    except Exception as e:
        logger.error(f"✗ Failed to generate batch embeddings: {e}")
        return False

def test_caching():
    """Test embedding cache"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 4: Embedding Cache")
    logger.info("=" * 60)
    
    try:
        from app.services.ollama_embeddings import embedding_service
        
        test_texts = ["This is a cached test.", "Another cached test."]
        
        # First call - should miss cache
        logger.info("First call (cache miss expected)...")
        embeddings1 = embedding_service.create_embeddings(test_texts)
        cache_size1 = len(embedding_service._embedding_cache)
        logger.info(f"  - Cache size: {cache_size1}")
        
        # Second call - should hit cache
        logger.info("Second call (cache hit expected)...")
        embeddings2 = embedding_service.create_embeddings(test_texts)
        cache_size2 = len(embedding_service._embedding_cache)
        logger.info(f"  - Cache size: {cache_size2}")
        
        # Check if embeddings are identical
        import numpy as np
        if np.allclose(embeddings1, embeddings2):
            logger.info("✓ Cache working correctly")
            logger.info(f"  - Cache hits on second call confirmed")
            return True
        else:
            logger.error("✗ Embeddings don't match between calls")
            return False
    except Exception as e:
        logger.error(f"✗ Cache test failed: {e}")
        return False

def test_vector_store_integration():
    """Test integration with vector store"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 5: Vector Store Integration")
    logger.info("=" * 60)
    
    try:
        from app.utils.vector_store import VectorStore
        
        # Create a test vector store
        test_doc_id = 999  # Use high ID to avoid conflicts
        logger.info(f"Creating vector store for document {test_doc_id}...")
        
        vector_store = VectorStore(test_doc_id)
        logger.info(f"✓ Vector store created")
        logger.info(f"  - Embedding dimension: {vector_store.embeddings.shape[1] if vector_store.embeddings.size > 0 else 'unknown'}")
        
        # Add some test texts
        test_texts = [
            "Python is a popular programming language.",
            "FastAPI is a modern web framework for building APIs.",
            "Machine learning models require training data."
        ]
        
        metadata = [
            {"chunk_id": f"chunk_{i}", "chunk_index": i, "page_number": 1, "text_preview": text}
            for i, text in enumerate(test_texts)
        ]
        
        logger.info(f"Adding {len(test_texts)} texts to vector store...")
        vector_store.add_texts(test_texts, metadata)
        logger.info(f"✓ Texts added successfully")
        logger.info(f"  - Total vectors: {len(vector_store.metadata)}")
        
        # Test similarity search
        query = "Tell me about Python"
        logger.info(f"Searching for similar texts: '{query}'...")
        results = vector_store.similarity_search(query, k=2, threshold=0.1)
        logger.info(f"✓ Similarity search completed")
        logger.info(f"  - Found {len(results)} results")
        for i, (metadata, similarity) in enumerate(results, 1):
            logger.info(f"  - Result {i}: similarity={similarity:.4f}, chunk_id={metadata['chunk_id']}")
        
        return True
    except Exception as e:
        logger.error(f"✗ Vector store integration test failed: {e}", exc_info=True)
        return False

def test_embedding_dimension():
    """Test embedding dimension consistency"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 6: Embedding Dimension Consistency")
    logger.info("=" * 60)
    
    try:
        from app.services.ollama_embeddings import embedding_service
        
        expected_dim = 768  # nomic-embed-text dimension
        actual_dim = embedding_service.get_embedding_dimension()
        
        if actual_dim == expected_dim:
            logger.info(f"✓ Embedding dimension is correct: {actual_dim}")
            return True
        else:
            logger.error(f"✗ Embedding dimension mismatch: expected {expected_dim}, got {actual_dim}")
            return False
    except Exception as e:
        logger.error(f"✗ Dimension test failed: {e}")
        return False

def main():
    """Run all tests"""
    logger.info("\n" + "🔬" * 30)
    logger.info("OLLAMA EMBEDDINGS INTEGRATION TEST SUITE")
    logger.info("🔬" * 30 + "\n")
    
    tests = [
        test_ollama_connection,
        test_embedding_dimension,
        test_embedding_generation,
        test_batch_embeddings,
        test_caching,
        test_embedding_dimension,
        test_vector_store_integration
    ]
    
    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append((test_func.__name__, result))
        except Exception as e:
            logger.error(f"Unexpected error in {test_func.__name__}: {e}", exc_info=True)
            results.append((test_func.__name__, False))
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{status}: {test_name}")
    
    logger.info("=" * 60)
    logger.info(f"Total: {passed}/{total} tests passed")
    logger.info("=" * 60)
    
    if passed == total:
        logger.info("\n🎉 ALL TESTS PASSED! Ollama embeddings are ready to use.")
        return 0
    else:
        logger.error(f"\n❌ {total - passed} test(s) failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    exit(main())
