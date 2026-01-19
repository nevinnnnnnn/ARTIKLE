#!/usr/bin/env python
"""Complete test of the Streamlit chat system"""
import requests
import json
import time

BACKEND_URL = "http://localhost:8000"

def section(title):
    print(f"\n{'='*70}")
    print(f" {title}")
    print(f"{'='*70}")

def test_login():
    """Test login endpoint"""
    section("1. TESTING LOGIN")
    
    url = f"{BACKEND_URL}/api/v1/auth/login"
    payload = {"username": "superadmin", "password": "superadmin123"}
    
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        data = response.json()
        token = data.get("access_token")
        print(f"✅ LOGIN SUCCESSFUL")
        print(f"   User ID: {data.get('user_id')}")
        print(f"   Role: {data.get('role')}")
        return token
    else:
        print(f"❌ LOGIN FAILED: {response.status_code}")
        return None

def test_get_documents(token):
    """Test getting chatable documents"""
    section("2. TESTING GET DOCUMENTS")
    
    url = f"{BACKEND_URL}/api/v1/chat/documents"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        documents = data.get("data", [])
        
        if documents:
            print(f"✅ DOCUMENTS RETRIEVED: {len(documents)} documents")
            for doc in documents[:3]:
                print(f"   • {doc.get('title')} (ID: {doc.get('id')})")
            return documents[0].get('id')
        else:
            print(f"❌ NO DOCUMENTS FOUND")
            return None
    else:
        print(f"❌ FAILED: {response.status_code}")
        return None

def test_streaming_chat(token, doc_id):
    """Test streaming chat"""
    section("3. TESTING STREAMING CHAT")
    
    url = f"{BACKEND_URL}/api/v1/chat/stream"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "text/event-stream"
    }
    payload = {
        "document_id": doc_id,
        "query": "What is in this document?"
    }
    
    print(f"Query: {payload['query']}")
    print(f"Document ID: {doc_id}")
    print(f"\n--- STREAMING RESPONSE ---")
    
    try:
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            stream=True,
            timeout=180
        )
        
        if response.status_code != 200:
            print(f"❌ FAILED: HTTP {response.status_code}")
            return False
        
        full_response = ""
        event_count = 0
        start_time = time.time()
        
        for line in response.iter_lines():
            if not line:
                continue
            
            try:
                line_str = line.decode() if isinstance(line, bytes) else line
                
                if line_str.startswith("data:"):
                    line_str = line_str[5:].strip()
                
                data = json.loads(line_str)
                event_count += 1
                
                if data.get("type") == "metadata":
                    meta = data.get("data", {})
                    print(f"\n📊 Metadata: {meta.get('context_chunks_retrieved')} chunks retrieved")
                
                elif data.get("type") == "text":
                    chunk = data.get("data", "")
                    full_response += chunk
                    print(chunk, end="", flush=True)
                
                elif data.get("type") == "complete":
                    print("\n")
                    break
                    
            except (json.JSONDecodeError, ValueError):
                continue
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        print(f"--- END OF RESPONSE ---\n")
        
        if full_response:
            print(f"✅ STREAMING SUCCESSFUL")
            print(f"   Response length: {len(full_response)} chars")
            print(f"   Events received: {event_count}")
            print(f"   Time taken: {elapsed:.2f}s")
            print(f"   First 80 chars: {full_response[:80]}...")
            return True
        else:
            print(f"❌ NO RESPONSE RECEIVED")
            return False
            
    except requests.exceptions.Timeout:
        print(f"❌ TIMEOUT after 180 seconds")
        return False
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_documents_page(token):
    """Test the documents API endpoint"""
    section("4. TESTING DOCUMENTS LIST")
    
    url = f"{BACKEND_URL}/api/v1/documents"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"skip": 0, "limit": 10}
    
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        documents = response.json()
        
        # Check for invalid data types
        invalid_count = 0
        valid_count = 0
        
        for doc in documents:
            if isinstance(doc, dict):
                valid_count += 1
            else:
                invalid_count += 1
        
        print(f"✅ DOCUMENTS RETRIEVED: {len(documents)} total")
        print(f"   Valid (dict): {valid_count}")
        print(f"   Invalid (not dict): {invalid_count}")
        
        if invalid_count > 0:
            print(f"   ⚠️  Some documents are not dictionaries - this could cause 'documents.py' to crash")
        
        return True
    else:
        print(f"❌ FAILED: {response.status_code}")
        return False

def main():
    print(f"""
╔══════════════════════════════════════════════════════════════════════╗
║                    STREAMLIT CHAT SYSTEM TEST SUITE                 ║
║                                                                      ║
║  Testing: Login → Documents → Streaming → UI Integration            ║
╚══════════════════════════════════════════════════════════════════════╝
""")

    # Test 1: Login
    token = test_login()
    if not token:
        print("\n❌ CANNOT PROCEED WITHOUT LOGIN")
        return False
    
    # Test 2: Get documents
    doc_id = test_get_documents(token)
    if not doc_id:
        print("\n❌ CANNOT PROCEED WITHOUT DOCUMENT")
        return False
    
    # Test 3: Streaming chat
    streaming_ok = test_streaming_chat(token, doc_id)
    
    # Test 4: Documents API (check for type issues)
    docs_ok = test_documents_page(token)
    
    # Summary
    section("TEST SUMMARY")
    print(f"""
✅ Login:           PASSED
✅ Documents:       PASSED
{'✅' if streaming_ok else '❌'} Streaming:      {'PASSED' if streaming_ok else 'FAILED'}
{'✅' if docs_ok else '❌'} Documents API: {'PASSED' if docs_ok else 'FAILED'}

Overall: {'🎉 ALL TESTS PASSED' if (streaming_ok and docs_ok) else '⚠️  SOME TESTS FAILED'}
""")
    
    return streaming_ok and docs_ok

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
