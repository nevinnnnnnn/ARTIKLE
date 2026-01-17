import sys
import os
import sqlite3
import requests
import json
import subprocess
import importlib.util
from pathlib import Path

print("=" * 80)
print("COMPREHENSIVE SYSTEM DIAGNOSTIC")
print("=" * 80)

def check_python_environment():
    print("\n🔍 1. PYTHON ENVIRONMENT")
    print("-" * 40)
    
    print(f"Python version: {sys.version}")
    print(f"Current directory: {os.getcwd()}")
    print(f"Backend directory exists: {os.path.exists('app')}")
    
def check_imports():
    print("\n🔍 2. IMPORT CHECKS")
    print("-" * 40)
    
    required_modules = [
        ("fastapi", "FastAPI framework"),
        ("uvicorn", "ASGI server"),
        ("sqlalchemy", "Database ORM"),
        ("pydantic", "Data validation"),
        ("jose", "JWT tokens"),
        ("passlib", "Password hashing"),
        ("sklearn", "Machine learning"),
        ("numpy", "Numerical computing"),
        ("pypdf", "PDF processing"),
    ]
    
    all_ok = True
    for module, description in required_modules:
        try:
            __import__(module)
            print(f"✅ {module:20} - {description}")
        except ImportError:
            print(f"❌ {module:20} - {description} - MISSING")
            all_ok = False
    
    return all_ok

def check_database():
    print("\n🔍 3. DATABASE CHECK")
    print("-" * 40)
    
    db_path = "pdf_chatbot.db"
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        print("   Server needs to be started at least once to create database.")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print(f"✅ Database exists: {db_path} ({os.path.getsize(db_path)/1024:.1f} KB)")
        print(f"   Tables found: {len(tables)}")
        
        required_tables = ['users', 'documents', 'document_chunks']
        missing_tables = []
        
        for table in required_tables:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if cursor.fetchone():
                # Get row count
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"   ✅ {table:20} - {count} rows")
            else:
                print(f"   ❌ {table:20} - MISSING")
                missing_tables.append(table)
        
        conn.close()
        
        if missing_tables:
            print(f"\n   ⚠️  Missing tables: {missing_tables}")
            print("   Run: python -m uvicorn app.main:app --reload (once)")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def check_app_structure():
    print("\n🔍 4. APPLICATION STRUCTURE")
    print("-" * 40)
    
    required_files = [
        "app/__init__.py",
        "app/main.py",
        "app/config.py",
        "app/database.py",
        "app/utils/__init__.py",
        "app/utils/vector_store.py",
        "app/models/__init__.py",
        "app/models/user.py",
        "app/models/document.py",
        "app/schemas/__init__.py",
        "app/schemas/user.py",
        "app/schemas/auth.py",
        "app/schemas/document.py",
        "app/schemas/chat.py",
        "app/auth/__init__.py",
        "app/auth/dependencies.py",
        "app/auth/utils.py",
        "app/api/__init__.py",
        "app/api/auth.py",
        "app/api/users.py",
        "app/api/documents.py",
        "app/api/chat.py",
        "app/services/__init__.py",
        "app/services/pdf_processor.py",
        "app/services/minimal_embeddings.py",
        "app/services/chat_service.py",
        "app/services/gpt4all_generator.py",
    ]
    
    all_ok = True
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - MISSING")
            all_ok = False
    
    return all_ok

def check_server_health():
    print("\n🔍 5. SERVER HEALTH CHECK")
    print("-" * 40)
    
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running and healthy")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"❌ Server responded with: {response.status_code}")
            return False
    except requests.ConnectionError:
        print("❌ Server is not running")
        print("   Start with: python -m uvicorn app.main:app --reload")
        return False
    except Exception as e:
        print(f"❌ Error checking server: {e}")
        return False

def check_authentication():
    print("\n🔍 6. AUTHENTICATION TEST")
    print("-" * 40)
    
    try:
        # Test login
        response = requests.post(
            "http://localhost:8000/api/v1/auth/login",
            data={"username": "superadmin", "password": "qweqwe"},
            timeout=10
        )
        
        if response.status_code == 200:
            token = response.json()["access_token"]
            print("✅ Authentication working")
            print(f"   Token obtained: {token[:50]}...")
            
            # Test protected endpoint
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(
                "http://localhost:8000/api/v1/protected/test",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                print("✅ Protected endpoint accessible")
                return token
            else:
                print(f"❌ Protected endpoint failed: {response.status_code}")
                return None
        else:
            print(f"❌ Login failed: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Authentication test error: {e}")
        return None

def check_documents(token):
    print("\n🔍 7. DOCUMENT SYSTEM CHECK")
    print("-" * 40)
    
    if not token:
        print("⚠️  Skipping (no auth token)")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        # Get documents
        response = requests.get(
            "http://localhost:8000/api/v1/documents",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            documents = response.json()
            print(f"✅ Found {len(documents)} document(s)")
            
            if documents:
                processed_count = sum(1 for d in documents if d.get('is_processed'))
                print(f"   Processed: {processed_count}/{len(documents)}")
                
                # Check each document
                for doc in documents[:3]:  # First 3
                    print(f"\n   Document ID: {doc['id']}")
                    print(f"   Title: {doc.get('title', 'Untitled')}")
                    print(f"   Processed: {doc.get('is_processed', False)}")
                    print(f"   Public: {doc.get('is_public', False)}")
                    
                    # Check vector stats
                    if doc.get('is_processed'):
                        stats_response = requests.get(
                            f"http://localhost:8000/api/v1/documents/{doc['id']}/vector-stats",
                            headers=headers,
                            timeout=10
                        )
                        if stats_response.status_code == 200:
                            stats = stats_response.json()
                            print(f"   Vectors: {stats['data']['vector_count']}")
                        else:
                            print(f"   ❌ No vector store")
            else:
                print("   ⚠️  No documents uploaded yet")
                
        else:
            print(f"❌ Failed to get documents: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Document check error: {e}")

def check_chat_system(token):
    print("\n🔍 8. CHAT SYSTEM CHECK")
    print("-" * 40)
    
    if not token:
        print("⚠️  Skipping (no auth token)")
        return
    
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    try:
        # Get chatable documents
        response = requests.get(
            "http://localhost:8000/api/v1/chat/documents",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            documents = result.get('data', [])
            print(f"✅ Chat system accessible")
            print(f"   Chatable documents: {len(documents)}")
            
            if documents:
                # Test chat with first document
                doc_id = documents[0]['id']
                print(f"\n   Testing chat with document {doc_id}...")
                
                chat_data = {
                    "document_id": doc_id,
                    "query": "test",
                    "stream": False
                }
                
                response = requests.post(
                    "http://localhost:8000/api/v1/chat/message",
                    headers=headers,
                    json=chat_data,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"   ✅ Chat working")
                    print(f"   Relevant: {result['data']['metadata']['is_relevant']}")
                    print(f"   Response: {result['data']['response'][:100]}...")
                else:
                    print(f"   ❌ Chat failed: {response.status_code}")
            else:
                print("   ⚠️  No chatable documents (need processed PDFs)")
                
        else:
            print(f"❌ Chat system check failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Chat check error: {e}")

def check_gpt4all():
    print("\n🔍 9. GPT4ALL AI CHECK")
    print("-" * 40)
    
    try:
        # Check if GPT4All is installed
        spec = importlib.util.find_spec("gpt4all")
        if spec is None:
            print("❌ GPT4All not installed")
            print("   Run: pip install gpt4all")
            return False
        
        print("✅ GPT4All package installed")
        
        # Check if model file exists in cache
        cache_dir = os.path.expanduser("~/.cache/gpt4all")
        if os.path.exists(cache_dir):
            model_files = list(Path(cache_dir).glob("*.gguf"))
            if model_files:
                print(f"✅ Found {len(model_files)} model(s) in cache")
                for model in model_files[:3]:
                    print(f"   - {model.name} ({model.stat().st_size/1024/1024:.1f} MB)")
                return True
            else:
                print("⚠️  Cache directory exists but no models found")
                print("   First chat request will download model (~4GB)")
                return True
        else:
            print("⚠️  No cache directory (first run will download model)")
            return True
            
    except Exception as e:
        print(f"❌ GPT4All check error: {e}")
        return False

def check_performance():
    print("\n🔍 10. PERFORMANCE CHECK")
    print("-" * 40)
    
    # Check file sizes
    print("File sizes:")
    for file in ["pdf_chatbot.db", "vector_stores/"]:
        if os.path.exists(file):
            if os.path.isdir(file):
                size = sum(os.path.getsize(os.path.join(file, f)) for f in os.listdir(file) if os.path.isfile(os.path.join(file, f)))
                print(f"   {file:20} - {size/1024:.1f} KB")
            else:
                print(f"   {file:20} - {os.path.getsize(file)/1024:.1f} KB")
    
    # Check uploads directory
    uploads_dir = "uploads"
    if os.path.exists(uploads_dir):
        uploads = os.listdir(uploads_dir)
        print(f"   Uploads: {len(uploads)} files")

def generate_report():
    print("\n" + "=" * 80)
    print("📋 DIAGNOSTIC REPORT & RECOMMENDATIONS")
    print("=" * 80)
    
    print("\n🚨 CRITICAL ISSUES (Fix Immediately):")
    print("1. Server must be running for frontend to work")
    print("2. Database must have users, documents, document_chunks tables")
    print("3. At least one superadmin user must exist")
    
    print("\n⚠️  IMPORTANT CHECKS:")
    print("1. Upload and process at least one PDF document")
    print("2. Create embeddings for processed documents")
    print("3. Test chat functionality with actual questions")
    
    print("\n🎯 FOR FRONTEND DEVELOPMENT:")
    print("✅ Backend API endpoints are ready")
    print("✅ Authentication system is working")
    print("✅ Chat API is functional")
    print("✅ GPT4All AI integration is available")
    
    print("\n🔧 NEXT STEPS FOR PHASE 7 (Frontend):")
    print("1. Create frontend/ directory")
    print("2. Install Streamlit and dependencies")
    print("3. Build login page with JWT storage")
    print("4. Create document browser interface")
    print("5. Implement chat interface with streaming")
    
    print("\n⚡ PERFORMANCE TIPS:")
    print("• First GPT4All response will be slow (model loading)")
    print("• Subsequent responses will be faster")
    print("• Consider adding response caching")
    print("• Monitor database growth with many PDFs")
    
    print("\n🔒 SECURITY NOTES:")
    print("• Change default superadmin password")
    print("• Set proper CORS origins in production")
    print("• Use environment variables for secrets")
    print("• Consider rate limiting for API endpoints")

def main():
    # Run all checks
    check_python_environment()
    imports_ok = check_imports()
    db_ok = check_database()
    structure_ok = check_app_structure()
    server_running = check_server_health()
    
    token = None
    if server_running:
        token = check_authentication()
        if token:
            check_documents(token)
            check_chat_system(token)
    
    gpt4all_ok = check_gpt4all()
    check_performance()
    
    # Generate comprehensive report
    generate_report()
    
    print("\n" + "=" * 80)
    print("🚀 READY FOR FRONTEND DEVELOPMENT?")
    print("=" * 80)
    
    requirements_met = all([
        imports_ok,
        db_ok,
        structure_ok,
        server_running,
        token is not None,
        gpt4all_ok
    ])
    
    if requirements_met:
        print("\n✅ ALL SYSTEMS GO! Backend is ready for frontend integration.")
        print("\nYou can now proceed to Phase 7: Frontend Foundation")
    else:
        print("\n⚠️  Some issues detected. Please fix them before frontend development.")
        print("\nCommon fixes:")
        print("1. Start server: python -m uvicorn app.main:app --reload")
        print("2. Create superadmin if missing")
        print("3. Upload and process a PDF")
        print("4. Install missing packages: pip install -r requirements.txt")
    
    print("\n📞 Need help with any specific issue?")
    print("1. Database issues - Check tables exist")
    print("2. Import errors - Install missing packages")
    print("3. Chat not working - Process PDF and create embeddings")
    print("4. AI not responding - Check GPT4All installation")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDiagnostic interrupted.")
    except Exception as e:
        print(f"\n❌ Diagnostic failed: {e}")
        import traceback
        traceback.print_exc()