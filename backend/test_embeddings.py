#!/usr/bin/env python3
"""
Test script to check if embeddings service works
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.embeddings_backup import embedding_service

def test_embeddings():
    print("🔍 Testing embeddings service...")
    
    try:
        # Test with sample text
        test_texts = [
            "Artificial intelligence is the simulation of human intelligence processes by machines.",
            "Machine learning algorithms build mathematical models based on sample data.",
            "Deep learning is a subset of machine learning using neural networks with multiple layers."
        ]
        
        print(f"Creating embeddings for {len(test_texts)} texts...")
        
        # This will load the model if not already loaded
        embeddings = embedding_service.create_embeddings(test_texts)
        
        print(f"✅ Success! Embeddings shape: {embeddings.shape}")
        print(f"   Embedding dimension: {embedding_service.get_embedding_dimension()}")
        print(f"   Sample embedding (first 5 values): {embeddings[0][:5]}")
        
        # Test similarity
        import numpy as np
        from sklearn.metrics.pairwise import cosine_similarity
        
        sim = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
        print(f"   Similarity between text 1 and 2: {sim:.4f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if test_embeddings():
        print("\n🎉 Embeddings service is working!")
    else:
        print("\n⚠️ Embeddings service failed. Trying offline mode...")
        
        # Try with a simpler model that might be cached
        print("\nTrying with smaller model...")
        try:
            from transformers import AutoTokenizer, AutoModel
            import torch
            
            # Try a very small model that's often cached
            model_name = "sentence-transformers/paraphrase-MiniLM-L3-v2"
            
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModel.from_pretrained(model_name)
            
            print(f"✅ Loaded model: {model_name}")
            print(f"   Hidden size: {model.config.hidden_size}")
            
        except Exception as e:
            print(f"❌ Could not load any model: {e}")