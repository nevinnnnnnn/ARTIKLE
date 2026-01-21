"""
AI Response Test - Verify Mistral model is answering questions properly
Tests the complete RAG pipeline
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8000/api/v1"

def test_ai_response():
    """Test if AI is answering questions"""
    
    print("\n" + "="*70)
    print("AI RESPONSE VERIFICATION TEST")
    print("="*70)
    
    # 1. Login
    print("\n[1/4] Logging in...")
    login_response = requests.post(
        f"{BASE_URL}/login",
        json={"username": "superadmin", "password": "superadmin"}
    )
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.text}")
        return False
    
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Login successful")
    
    # 2. Get documents
    print("\n[2/4] Getting documents...")
    docs_response = requests.get(
        f"{BASE_URL}/documents",
        headers=headers
    )
    
    if docs_response.status_code != 200:
        print(f"❌ Failed to get documents: {docs_response.text}")
        return False
    
    documents = docs_response.json()
    if not documents:
        print("❌ No documents available")
        return False
    
    doc_id = documents[0]["id"]
    doc_title = documents[0].get("title", "Untitled")
    print(f"✅ Found {len(documents)} documents. Using: {doc_title} (ID: {doc_id})")
    
    # 3. Test streaming chat with various questions
    print("\n[3/4] Testing AI responses with streaming...")
    
    test_questions = [
        "What is the main topic?",
        "Summarize the content",
        "What information is provided?"
    ]
    
    responses_received = 0
    
    for question in test_questions:
        print(f"\n  Question: {question}")
        
        try:
            chat_response = requests.post(
                f"{BASE_URL}/chat/stream",
                headers=headers,
                json={"document_id": doc_id, "query": question},
                stream=True,
                timeout=180
            )
            
            if chat_response.status_code != 200:
                print(f"  ❌ Chat failed: HTTP {chat_response.status_code}")
                continue
            
            response_text = ""
            chunk_count = 0
            
            for line in chat_response.iter_lines():
                if line:
                    try:
                        if line.startswith(b"data:"):
                            line = line[5:].strip()
                        
                        data = json.loads(line)
                        
                        if "response" in data:
                            response_text += data["response"]
                            chunk_count += 1
                    except:
                        pass
            
            if response_text.strip():
                preview = response_text[:80].replace("\n", " ")
                print(f"  ✅ Response received ({len(response_text)} chars, {chunk_count} chunks)")
                print(f"     Preview: {preview}...")
                responses_received += 1
            else:
                print(f"  ⚠️  No response text received")
        
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    # 4. Summary
    print("\n[4/4] Test Summary")
    print("="*70)
    
    if responses_received >= 2:
        print(f"✅ AI IS ANSWERING QUESTIONS ({responses_received}/{len(test_questions)} responses)")
        print("   The system is working correctly!")
        return True
    else:
        print(f"❌ Limited responses ({responses_received}/{len(test_questions)})")
        return False


if __name__ == "__main__":
    try:
        success = test_ai_response()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted")
        sys.exit(1)
