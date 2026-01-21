#!/usr/bin/env python
"""
Quick test to verify LLaMA3-ChatQA model is working
"""

import os
import sys

# Add parent to path
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.getcwd())

print("=" * 70)
print("LLaMA3-ChatQA Migration Verification")
print("=" * 70)

try:
    from app.services.ollama_generator import ollama_generator
    
    print(f"\n✓ Service loaded")
    print(f"  Model: {ollama_generator.available_model}")
    print(f"  Endpoint: {ollama_generator.endpoint}")
    
    if ollama_generator.available_model and 'llama3-chatqa' in ollama_generator.available_model.lower():
        print(f"\n✓ LLaMA3-ChatQA model confirmed!")
        print(f"\nMigration Status: SUCCESS ✅")
        sys.exit(0)
    elif ollama_generator.available_model:
        print(f"\n⚠ Using fallback model: {ollama_generator.available_model}")
        print(f"  (LLaMA3-ChatQA may not be available)")
        sys.exit(1)
    else:
        print(f"\n✗ No model available. Is Ollama running?")
        sys.exit(1)
        
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
