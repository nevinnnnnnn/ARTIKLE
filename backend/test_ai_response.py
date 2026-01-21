"""Test script to verify AI is working with context"""
import requests
import json
import time
from app.services.chat_service import chat_service

print("TEST: AI RESPONSE WITH CONTEXT")
print("=" * 70)

document_id = 1
query = "What is AI?"

print(f"\nQuestion: {query}")
print(f"Document: Test PDF (ID: {document_id})")
print("\n" + "=" * 70)

# Step 1: Retrieve context
print("\n1️⃣  RETRIEVING CONTEXT FROM VECTOR STORE")
print("-" * 70)
context = chat_service.retrieve_context(document_id, query, top_k=5)

if not context:
    print("❌ ERROR: No context retrieved!")
else:
    print(f"✅ Retrieved {len(context)} chunk(s)")
    for i, chunk in enumerate(context, 1):
        print(f"\nChunk {i}:")
        print(f"  Similarity: {chunk['similarity_score']:.4f}")
        print(f"  Page: {chunk['page_number']}")
        print(f"  Content length: {len(chunk['text'])} chars")
        print(f"  Preview: {chunk['text'][:100]}...")

# Step 2: Test direct Ollama API
print("\n" + "=" * 70)
print("2️⃣  TESTING OLLAMA MODEL DIRECTLY")
print("-" * 70)

prompt = f"""Based ONLY on this document, answer the question:

Document:
{context[0]['text'] if context else 'NO CONTEXT'}

Question: {query}

Answer (use ONLY the document):"""

print("\nSending request to Ollama (llama3-chatqa:8b)...")
print("Please wait... (this may take 30-120 seconds)")

start = time.time()
try:
    response = requests.post(
        'http://localhost:11434/api/generate',
        json={
            'model': 'llama3-chatqa:8b',
            'prompt': prompt,
            'stream': True,
            'options': {
                'temperature': 0.01,
                'top_p': 0.95,
                'top_k': 20,
                'repeat_penalty': 1.5,
                'num_predict': 256
            }
        },
        stream=True,
        timeout=180
    )
    
    if response.status_code == 200:
        print("\n✅ Response received from Ollama:")
        print("-" * 70)
        full_response = ""
        for line in response.iter_lines():
            if line:
                try:
                    data = json.loads(line)
                    if 'response' in data:
                        chunk = data['response']
                        print(chunk, end='', flush=True)
                        full_response += chunk
                    if data.get('done'):
                        break
                except:
                    pass
        
        elapsed = time.time() - start
        print()
        print("-" * 70)
        print(f"\n📊 RESULTS:")
        print(f"   Response length: {len(full_response)} characters")
        print(f"   Time taken: {elapsed:.1f} seconds")
        
        # Analyze response
        if "cannot find" in full_response.lower() or "not in the document" in full_response.lower():
            print("   Status: ⚠️  Model says info not in document")
        elif "ai" in full_response.lower() and len(full_response) > 50:
            print("   Status: ✅ Good - Model answered about AI from context")
        else:
            print("   Status: ❓ Check response quality above")
            
    else:
        print(f"❌ Ollama returned: {response.status_code}")
        
except requests.exceptions.Timeout:
    print(f"❌ TIMEOUT after {time.time()-start:.0f} seconds")
    print("   The model is taking too long - check if Ollama is busy")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 70)
print("TEST COMPLETE")
print("=" * 70)
