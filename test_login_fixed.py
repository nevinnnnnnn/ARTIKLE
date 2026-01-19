#!/usr/bin/env python
"""Test login endpoint with fixed JSON format"""
import requests
import json
import sys

# Backend URL
BACKEND_URL = "http://localhost:8000"

# Test credentials (from init_db.py)
test_credentials = [
    ("superadmin", "superadmin123"),
    ("admin", "admin123"),
    ("user", "user123"),
]

def test_login(username: str, password: str):
    """Test login with JSON body"""
    url = f"{BACKEND_URL}/api/v1/auth/login"
    
    payload = {
        "username": username,
        "password": password
    }
    
    print(f"\n{'='*60}")
    print(f"Testing login for: {username}")
    print(f"{'='*60}")
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print(f"Content-Type: application/json")
    
    try:
        response = requests.post(
            url,
            json=payload,  # ✅ CORRECT: JSON body
            timeout=10
        )
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ LOGIN SUCCESSFUL!")
            print(f"Token Type: {data.get('token_type')}")
            print(f"User ID: {data.get('user_id')}")
            print(f"Role: {data.get('role')}")
            print(f"Access Token (first 50 chars): {data.get('access_token', '')[:50]}...")
            return True
        else:
            print(f"\n❌ LOGIN FAILED")
            try:
                error = response.json()
                print(f"Error Details: {json.dumps(error, indent=2)}")
            except:
                print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"\n❌ Cannot connect to backend at {BACKEND_URL}")
        print("Make sure the backend is running: python -m uvicorn app.main:app --reload")
        return False
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("\n" + "="*60)
    print("TESTING LOGIN ENDPOINT WITH FIXED JSON FORMAT")
    print("="*60)
    
    results = []
    for username, password in test_credentials:
        success = test_login(username, password)
        results.append((username, success))
    
    print(f"\n\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    
    for username, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{username}: {status}")
    
    if all(success for _, success in results):
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed")
        sys.exit(1)
