#!/usr/bin/env python3
"""
Test script to setup a document for chatting
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models.user import User
from app.models.document import Document, DocumentChunk
from app.auth.utils import get_password_hash

def check_system():
    """Check if system is ready for chat"""
    
    db = SessionLocal()
    
    print("🔍 Checking system readiness...")
    
    # Check users
    users = db.query(User).all()
    print(f"✅ Found {len(users)} users")
    
    # Check documents
    documents = db.query(Document).all()
    print(f"📄 Found {len(documents)} documents")
    
    for doc in documents:
        chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).count()
        print(f"   - {doc.filename}: Processed={doc.is_processed}, Chunks={chunks}")
    
    db.close()
    
    if documents:
        print("\n📋 Available documents for chat:")
        for doc in documents:
            if doc.is_processed:
                print(f"   ✅ {doc.id}: {doc.title} (Ready for chat)")
            else:
                print(f"   ⏳ {doc.id}: {doc.title} (Needs processing)")
    
    return len(documents) > 0

if __name__ == "__main__":
    if check_system():
        print("\n🎉 System is ready for Phase 8 (Chat UI)!")
        print("\n💡 Next steps:")
        print("1. Start frontend: streamlit run app.py")
        print("2. Login with superadmin/admin123")
        print("3. Go to Chat page")
        print("4. Select a processed document and start chatting")
    else:
        print("\n⚠️ No documents found. Please upload a PDF first:")
        print("1. Login as admin/superadmin")
        print("2. Go to Upload page")
        print("3. Upload a PDF document")
        print("4. Process it (extract text & create embeddings)")