#!/usr/bin/env python
"""Test streaming chat response to verify AI is working correctly"""
import requests
import json
import time

BACKEND_URL = "http://localhost:8000"

# Test credentials
TOKEN = None
DOCUMENT_ID = None

def login():
    """Login to get token"""
    global TOKEN
    
    url = f"{BACKEND_URL}/api/v1/auth/login"
    payload = {
        "username": "superadmin",
        "password": "superadmin123"
    }
    
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        data = response.json()
        TOKEN = data.get("access_token")
        print(f"✅ Login successful")
        print(f"Token: {TOKEN[:50]}...")
        return True
    else:
        print(f"❌ Login failed: {response.status_code}")
        print(response.text)
        return False

def get_processed_document():
    """Get a processed document for testing"""
    global DOCUMENT_ID
    
    url = f"{BACKEND_URL}/api/v1/chat/documents"
    headers = {"Authorization": f"Bearer {TOKEN}"}
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        documents = data.get("data", [])
        
        if documents:
            doc = documents[0]
            DOCUMENT_ID = doc.get("id")
            print(f"✅ Found document: {doc.get('title')} (ID: {DOCUMENT_ID})")
            return True
    
    print(f"❌ No processed documents found")
    return False

def test_streaming_response():
    """Test the streaming chat endpoint"""
    
    if not TOKEN or not DOCUMENT_ID:
        print("❌ Not authenticated or no document selected")
        return False
    
    url = f"{BACKEND_URL}/api/v1/chat/stream"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "text/event-stream"
    }
    
    payload = {
        "document_id": DOCUMENT_ID,
        "query": "What is the main topic of this document?"
    }
    
    print(f"\n{'='*60}")
    print(f"Testing streaming response")
    print(f"{'='*60}")
    print(f"URL: {url}")
    print(f"Document ID: {DOCUMENT_ID}")
    print(f"Query: {payload['query']}")
    print()
    
    try:
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            stream=True,
            timeout=180
        )
        
        if response.status_code != 200:
            print(f"❌ Error: HTTP {response.status_code}")
            print(response.text)
            return False
        
        print("Response stream:")
        print("-" * 60)
        
        full_response = ""
        metadata = {}
        event_count = 0
        
        for line in response.iter_lines():
            if not line:
                continue
            
            try:
                line_str = line.decode() if isinstance(line, bytes) else line
                
                # Remove "data: " prefix if present
                if line_str.startswith("data:"):
                    line_str = line_str[5:].strip()
                
                data = json.loads(line_str)
                event_count += 1
                
                if data.get("type") == "metadata":
                    metadata = data.get("data", {})
                    print(f"\n📊 METADATA:")
                    print(f"  Context chunks: {metadata.get('context_chunks_retrieved')}")
                    print(f"  Similarity score: {metadata.get('top_similarity_score'):.2f}")
                    print(f"\n📝 RESPONSE STREAMING:")
                
                elif data.get("type") == "text":
                    chunk = data.get("data", "")
                    full_response += chunk
                    print(chunk, end="", flush=True)
                
                elif data.get("type") == "complete":
                    print("\n\n✅ Stream completed")
                    break
                
                elif data.get("type") == "error":
                    print(f"\n❌ Error: {data.get('data', {}).get('message')}")
                    return False
                    
            except json.JSONDecodeError as e:
                print(f"\n⚠️ JSON decode error: {e}")
                print(f"Line: {line_str[:100] if line_str else 'empty'}")
                continue
        
        print(f"-" * 60)
        print(f"\n📈 SUMMARY:")
        print(f"  Total events received: {event_count}")
        print(f"  Response length: {len(full_response)} characters")
        print(f"  First 100 chars: {full_response[:100]}")
        
        if full_response:
            print(f"\n✅ TEST PASSED - AI is responding!")
            return True
        else:
            print(f"\n❌ TEST FAILED - No response from AI")
            return False
        
    except requests.exceptions.Timeout:
        print(f"❌ Request timed out after 180 seconds")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n" + "="*60)
    print("STREAMLIT CHAT STREAMING TEST")
    print("="*60 + "\n")
    
    print("STEP 1: Login")
    if not login():
        exit(1)
    
    print("\nSTEP 2: Get processed document")
    if not get_processed_document():
        exit(1)
    
    print("\nSTEP 3: Test streaming response")
    if test_streaming_response():
        print("\n🎉 All tests passed!")
        exit(0)
    else:
        print("\n❌ Tests failed")
        exit(1)
