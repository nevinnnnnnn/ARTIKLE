#!/usr/bin/env python3
"""Test Ollama integration"""

import sys
import os
import json

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

print("=" * 60)
print("TESTING OLLAMA MODEL GENERATION")
print("=" * 60)

# Test imports
print("\n1. Testing imports...")
try:
    from app.services.gpt4all_generator import GPT4AllGenerator
    print("SUCCESS: GPT4AllGenerator imported")
except Exception as e:
    print(f"FAILED: {e}")
    sys.exit(1)

# Test model loading
print("\n2. Attempting to load model...")
try:
    generator = GPT4AllGenerator()
    print(f"SUCCESS: Model loaded")
    print(f"  Model Type: {generator.model_type}")
    if generator.model:
        print(f"  Model object: {type(generator.model)}")
except Exception as e:
    print(f"FAILED: {e}")
    sys.exit(1)

# Test response generation
if generator.model and generator.model_type == "ollama":
    print("\n3. Testing Ollama response generation...")
    try:
        context = "Python was created by Guido van Rossum. It is a powerful programming language."
        question = "Who created Python?"
        
        print(f"  Context: {context[:50]}...")
        print(f"  Question: {question}")
        print(f"  Generating response...")
        print("  " + "-" * 40)
        
        response_chunks = []
        for chunk in generator.generate_response(context, question):
            response_chunks.append(chunk)
            print(f"  Got chunk: {repr(chunk[:60])}")
        
        full_response = "".join(response_chunks)
        print("  " + "-" * 40)
        print(f"SUCCESS: Response generated")
        print(f"  Total chunks: {len(response_chunks)}")
        print(f"  Response length: {len(full_response)} chars")
        print(f"\n  FULL RESPONSE:\n  {full_response}\n")
        
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()
else:
    print("\n3. SKIPPED: Ollama not loaded")

print("=" * 60)
print("TEST COMPLETE")
print("=" * 60)
