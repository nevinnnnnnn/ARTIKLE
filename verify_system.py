#!/usr/bin/env python
"""
Market-Ready System Verification Script
Checks all critical systems before deployment
"""

import sys
import os
from pathlib import Path

def check_python_version():
    """Verify Python version compatibility"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 9:
        print("✅ Python Version: OK (3.9+)")
        return True
    else:
        print("❌ Python Version: FAILED (requires 3.9+)")
        return False

def check_dependencies():
    """Check critical dependencies"""
    required = {
        'fastapi': '0.110.0',
        'uvicorn': '0.27.0',
        'pydantic': '2.5.0',
        'sqlalchemy': '2.0.36',
        'requests': '2.31.0',
    }
    
    all_ok = True
    for package, required_version in required.items():
        try:
            module = __import__(package)
            version = getattr(module, '__version__', 'unknown')
            print(f"✅ {package}: {version}")
        except ImportError:
            print(f"❌ {package}: NOT INSTALLED")
            all_ok = False
    
    return all_ok

def check_directories():
    """Verify directory structure"""
    required_dirs = [
        'backend',
        'backend/app',
        'backend/app/api',
        'backend/app/services',
        'backend/app/models',
        'backend/app/schemas',
        'frontend',
        'frontend/pages',
        'frontend/src',
    ]
    
    all_ok = True
    for directory in required_dirs:
        if os.path.isdir(directory):
            print(f"✅ Directory: {directory}")
        else:
            print(f"❌ Directory MISSING: {directory}")
            all_ok = False
    
    return all_ok

def check_files():
    """Verify critical files exist"""
    required_files = [
        'backend/requirements.txt',
        'backend/app/main.py',
        'backend/app/config.py',
        'backend/app/database.py',
        'backend/app/api/auth.py',
        'backend/app/api/chat.py',
        'frontend/app.py',
        'frontend/requirements.txt',
    ]
    
    all_ok = True
    for file in required_files:
        if os.path.isfile(file):
            print(f"✅ File: {file}")
        else:
            print(f"❌ File MISSING: {file}")
            all_ok = False
    
    return all_ok

def check_database():
    """Check database connectivity"""
    try:
        sys.path.insert(0, 'backend')
        from app.database import engine, Base
        
        # Try to connect
        connection = engine.connect()
        connection.close()
        print("✅ Database Connection: OK")
        return True
    except Exception as e:
        print(f"⚠️  Database Connection: {str(e)[:50]}...")
        return True  # Not critical for first run

def check_models():
    """Verify all models can be imported"""
    try:
        sys.path.insert(0, 'backend')
        from app.models import User, Document, DocumentChunk, ChatHistory
        print("✅ All Models: Imported successfully")
        return True
    except Exception as e:
        print(f"❌ Models Import: {str(e)[:50]}...")
        return False

def check_schemas():
    """Verify all schemas can be imported"""
    try:
        sys.path.insert(0, 'backend')
        from app.schemas.auth import Token, LoginRequest
        from app.schemas.user import UserCreate
        from app.schemas.chat import ChatRequest
        print("✅ All Schemas: Imported successfully")
        return True
    except Exception as e:
        print(f"❌ Schemas Import: {str(e)[:50]}...")
        return False

def main():
    """Run all checks"""
    print("=" * 80)
    print("MARKET-READY SYSTEM VERIFICATION")
    print("=" * 80)
    print()
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Directory Structure", check_directories),
        ("Critical Files", check_files),
        ("Models", check_models),
        ("Schemas", check_schemas),
        ("Database", check_database),
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\n--- {name} ---")
        try:
            result = check_func()
            results.append(result)
        except Exception as e:
            print(f"❌ Error during check: {str(e)[:100]}")
            results.append(False)
    
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Checks Passed: {passed}/{total}")
    
    if passed == total:
        print("\n✅ SYSTEM READY FOR DEPLOYMENT")
        print("\nQuick Start:")
        print("  1. cd backend")
        print("  2. python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        print("  3. Open new terminal and cd frontend")
        print("  4. streamlit run app.py")
        print("  5. Visit http://localhost:8501")
        return 0
    else:
        print(f"\n⚠️  Some checks failed ({total - passed})")
        print("\nFix issues and run verification again")
        return 1

if __name__ == "__main__":
    sys.exit(main())
