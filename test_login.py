import requests
import json

# Test login
url = "http://localhost:8000/api/v1/auth/login"
payload = {
    "username": "superadmin",
    "password": "superadmin123"
}

print("=" * 70)
print("🔐 TESTING SUPERADMIN CREDENTIALS")
print("=" * 70)
print(f"\n📍 Testing URL: {url}")
print(f"📝 Payload: {json.dumps(payload, indent=2)}")

try:
    response = requests.post(url, json=payload, timeout=10)
    print(f"\n✓ Response Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ LOGIN SUCCESSFUL!\n")
        print(f"   Access Token: {data.get('access_token', 'N/A')[:50]}...")
        print(f"   Token Type: {data.get('token_type', 'N/A')}")
        print(f"   User ID: {data.get('user_id', 'N/A')}")
        print(f"   Role: {data.get('role', 'N/A')}")
    else:
        print(f"\n❌ LOGIN FAILED!")
        print(f"   Error: {response.text}")
        
except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")
    print(f"\n⚠️  Make sure backend is running on http://localhost:8000")

print("\n" + "=" * 70)
