"""
Test script to verify Gemini API integration
Run this after setting GEMINI_API_KEY environment variable
"""

import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

def test_gemini_api_key():
    """Test if Gemini API key is configured"""
    print("\n=== Testing Gemini API Key ===")
    
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        print("❌ GEMINI_API_KEY not set in environment")
        print("   Please set it: export GEMINI_API_KEY=your_api_key")
        return False
    
    if api_key.startswith("sk-"):
        print("⚠️  Key appears to be an OpenAI key (starts with 'sk-')")
        return False
    
    if len(api_key) < 10:
        print("❌ API key is too short")
        return False
    
    print("✓ GEMINI_API_KEY is set")
    return True


def test_gemini_imports():
    """Test if Gemini service can be imported"""
    print("\n=== Testing Gemini Service Imports ===")
    
    try:
        import google.generativeai as genai
        print("✓ google.generativeai imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import google.generativeai: {e}")
        print("   Run: pip install google-generativeai")
        return False
    
    try:
        from app.services.gemini_service import GeminiEmbeddings, GeminiChat
        print("✓ Gemini service modules imported successfully")
        print(f"  - GeminiEmbeddings (dim: {GeminiEmbeddings.DIMENSION})")
        print(f"  - GeminiChat (model: {GeminiChat.MODEL_NAME})")
    except Exception as e:
        print(f"❌ Failed to import Gemini service: {e}")
        return False
    
    return True


def test_gemini_embeddings():
    """Test Gemini embeddings generation"""
    print("\n=== Testing Gemini Embeddings ===")
    
    if not os.getenv("GEMINI_API_KEY"):
        print("⊘  Skipping (API key not set)")
        return None
    
    try:
        from app.services.gemini_service import GeminiEmbeddings
        
        test_text = "This is a test document for embeddings."
        print(f"Generating embedding for: '{test_text}'")
        
        embedding = GeminiEmbeddings.create_embedding(test_text)
        
        if not isinstance(embedding, list):
            print(f"❌ Embedding is not a list: {type(embedding)}")
            return False
        
        if len(embedding) != GeminiEmbeddings.DIMENSION:
            print(f"❌ Embedding dimension mismatch: {len(embedding)} != {GeminiEmbeddings.DIMENSION}")
            return False
        
        if not all(isinstance(x, (int, float)) for x in embedding[:5]):
            print(f"❌ Embedding values are not numeric")
            return False
        
        print(f"✓ Successfully generated embedding")
        print(f"  - Dimension: {len(embedding)}")
        print(f"  - First 3 values: {embedding[:3]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to generate embeddings: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_gemini_chat():
    """Test Gemini chat generation"""
    print("\n=== Testing Gemini Chat ===")
    
    if not os.getenv("GEMINI_API_KEY"):
        print("⊘  Skipping (API key not set)")
        return None
    
    try:
        from app.services.gemini_service import GeminiChat
        
        query = "What is artificial intelligence?"
        context = """Artificial Intelligence (AI) refers to the simulation of human intelligence 
in machines that are programmed to think like humans and mimic their actions. AI can be used in 
various fields such as healthcare, finance, transportation, and more."""
        
        print(f"Query: {query}")
        print(f"Context: {context[:100]}...")
        
        response = GeminiChat.generate_response(query, context, temperature=0.3, max_tokens=256)
        
        if not response:
            print("❌ No response generated")
            return False
        
        if len(response) < 10:
            print(f"❌ Response is too short: {response}")
            return False
        
        print(f"✓ Successfully generated response")
        print(f"  - Response length: {len(response)} chars")
        print(f"  - Response: {response[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to generate chat response: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("Gemini Integration Test Suite")
    print("=" * 60)
    
    results = {
        "API Key": test_gemini_api_key(),
        "Imports": test_gemini_imports(),
        "Embeddings": test_gemini_embeddings(),
        "Chat": test_gemini_chat(),
    }
    
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for test_name, result in results.items():
        if result is None:
            status = "⊘  Skipped"
        elif result:
            status = "✓ Passed"
        else:
            status = "❌ Failed"
        print(f"{test_name:.<40} {status}")
    
    # Overall result
    passed = sum(1 for r in results.values() if r is True)
    total = len(results)
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Gemini integration is ready.")
        return 0
    elif passed > total // 2:
        print("\n⚠️  Some tests passed. Check configuration and dependencies.")
        return 1
    else:
        print("\n❌ Most tests failed. Set GEMINI_API_KEY and check setup.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
