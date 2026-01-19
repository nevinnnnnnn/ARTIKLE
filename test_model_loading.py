#!/usr/bin/env python3
"""Test if model loading works"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

print("=" * 60)
print("TESTING MODEL LOADING SYSTEM")
print("=" * 60)

# Test imports
print("\n1. Testing imports...")
try:
    from app.services.gpt4all_generator import GPT4AllGenerator
    print("✓ GPT4AllGenerator imported successfully")
except Exception as e:
    print(f"✗ Failed to import GPT4AllGenerator: {e}")
    sys.exit(1)

# Test model loading
print("\n2. Attempting to load model...")
try:
    generator = GPT4AllGenerator()
    print(f"✓ Model loaded successfully!")
    print(f"  Model Type: {generator.model_type}")
    if generator.model:
        print(f"  Model Status: Ready")
    else:
        print(f"  Model Status: Not loaded (all backends failed)")
except Exception as e:
    print(f"✗ Failed to load model: {e}")
    sys.exit(1)

# Test formatting
print("\n3. Testing prompt formatting...")
try:
    context = "The Earth is a planet. It orbits the Sun."
    question = "Is Earth a planet?"
    prompt = generator.format_prompt(context, question)
    print(f"✓ Prompt formatted successfully")
    print(f"  Prompt length: {len(prompt)} characters")
except Exception as e:
    print(f"✗ Failed to format prompt: {e}")
    sys.exit(1)

# Test response generation (if model is loaded)
if generator.model:
    print("\n4. Testing response generation...")
    try:
        context = "The Python programming language was created by Guido van Rossum."
        question = "Who created Python?"
        
        print(f"  Question: {question}")
        print(f"  Generating response...")
        
        response = ""
        chunk_count = 0
        for chunk in generator.generate_response(context, question):
            response += chunk
            chunk_count += 1
            if chunk_count <= 5:
                print(f"    Chunk {chunk_count}: {repr(chunk[:50])}")
        
        print(f"\n✓ Response generated successfully!")
        print(f"  Total chunks: {chunk_count}")
        print(f"  Response length: {len(response)} characters")
        print(f"\n  Full response:\n{response}\n")
    except Exception as e:
        print(f"✗ Failed to generate response: {e}")
        import traceback
        traceback.print_exc()
else:
    print("\n4. Skipping response generation test (model not loaded)")

print("\n" + "=" * 60)
print("MODEL LOADING TEST COMPLETE")
print("=" * 60)
