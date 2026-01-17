import requests

def test_login():
    print("🔍 Testing login directly...")
    
    # Test credentials
    credentials = [
        ("superadmin", "admin123"),
        ("admin", "admin123"),
        ("user", "user123"),
        ("test", "test123")
    ]
    
    for username, password in credentials:
        print(f"\nTrying: {username}/{password}")
        try:
            response = requests.post(
                "http://localhost:8000/api/v1/auth/login",
                data={"username": username, "password": password},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ SUCCESS!")
                print(f"   Token: {data['access_token'][:30]}...")
                print(f"   Role: {data.get('role', 'unknown')}")
                return True
            else:
                print(f"❌ Failed: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    return False

if __name__ == "__main__":
    if test_login():
        print("\n🎉 Backend login is working!")
    else:
        print("\n❌ Backend login is not working.")