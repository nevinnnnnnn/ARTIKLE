#!/usr/bin/env python
"""
Quick Startup Script - Run this to verify everything is working
"""

import os
import sys
import time
import subprocess
import requests
import json

def check_ollama():
    """Check if Ollama is running"""
    print("\n[1/4] Checking Ollama connection...")
    try:
        resp = requests.get("http://localhost:11434/api/tags", timeout=5)
        if resp.status_code == 200:
            models = resp.json().get("models", [])
            print(f"  ✓ Ollama running with {len(models)} models")
            model_names = [m.get("name") for m in models]
            if any("mistral" in m.lower() for m in model_names):
                print(f"  ✓ Mistral model available")
                return True
            else:
                print(f"  ✗ Mistral model NOT found. Available: {model_names}")
                return False
        else:
            print(f"  ✗ Ollama returned status {resp.status_code}")
            return False
    except Exception as e:
        print(f"  ✗ Cannot connect to Ollama: {e}")
        print(f"     Please start Ollama: ollama serve")
        return False

def check_backend():
    """Check if backend is running"""
    print("\n[2/4] Checking backend API...")
    try:
        resp = requests.get("http://localhost:8000/health", timeout=5)
        if resp.status_code == 200:
            print(f"  ✓ Backend running on http://localhost:8000")
            return True
        else:
            print(f"  ✗ Backend returned status {resp.status_code}")
            return False
    except Exception as e:
        print(f"  ✗ Cannot connect to backend: {e}")
        return False

def check_database():
    """Check if database exists"""
    print("\n[3/4] Checking database...")
    db_path = os.path.join("backend", "pdf_chatbot.db")
    if os.path.exists(db_path):
        size = os.path.getsize(db_path)
        print(f"  ✓ Database found ({size} bytes)")
        return True
    else:
        print(f"  ✗ Database not found at {db_path}")
        print(f"     Run: cd backend && python init_db.py")
        return False

def check_services():
    """Check if all services are loaded"""
    print("\n[4/4] Checking services...")
    try:
        os.chdir("backend")
        result = subprocess.run(
            [sys.executable, "-c", "from app.main import app; print('✓ All services loaded')"],
            capture_output=True,
            text=True,
            timeout=10
        )
        os.chdir("..")
        if result.returncode == 0:
            print(f"  ✓ {result.stdout.strip()}")
            return True
        else:
            print(f"  ✗ Service check failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"  ✗ Error checking services: {e}")
        return False

def main():
    print("=" * 70)
    print("PDF AI CHATBOT - SYSTEM STARTUP VERIFICATION")
    print("=" * 70)
    
    checks = [
        ("Ollama Connection", check_ollama),
        ("Backend API", check_backend),
        ("Database", check_database),
        ("Services", check_services),
    ]
    
    results = {}
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print(f"  ✗ Unexpected error: {e}")
            results[name] = False
    
    # Summary
    print("\n" + "=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{name:.<50} {status}")
    
    print(f"\nOverall: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n✓ All systems ready! You can now:")
        print("  1. Backend:  python backend/run_server.py")
        print("  2. Frontend: streamlit run frontend/app.py")
        print("  3. Access:   http://localhost:8501")
        print("  4. Login:    user/user (or admin/admin or superadmin/superadmin)")
        return 0
    else:
        print("\n✗ Some systems not ready. Fix the issues above and try again.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
