#!/usr/bin/env python3
"""
SQLite migration script to add embeddings_created_at column
"""

import sys
import os
sys.path.append('.')

from app.database import SessionLocal, engine
from sqlalchemy import inspect
import sqlite3

def add_embeddings_created_at_column():
    """Add embeddings_created_at column to documents table (SQLite compatible)"""
    
    print("🔧 Adding embeddings_created_at column to documents table...")
    
    # Method 1: Using SQLAlchemy metadata (recommended)
    try:
        from app.models.document import Document
        from app.database import Base
        
        # This will add the column if we recreate the table, but SQLite doesn't support ALTER ADD
        # Let's use direct SQLite connection instead
        print("Using direct SQLite connection...")
        
        # Get database path from engine URL
        db_url = str(engine.url)
        if db_url.startswith('sqlite:///'):
            db_path = db_url.replace('sqlite:///', '')
            
            # Connect directly to SQLite
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check if column already exists
            cursor.execute("PRAGMA table_info(documents)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'embeddings_created_at' in columns:
                print("✅ Column 'embeddings_created_at' already exists")
            else:
                # Add the column
                cursor.execute("ALTER TABLE documents ADD COLUMN embeddings_created_at DATETIME")
                conn.commit()
                print("✅ Column 'embeddings_created_at' added successfully")
            
            conn.close()
            
        else:
            print(f"❌ Not a SQLite database: {db_url}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        
        # Try alternative method
        try:
            print("\nTrying alternative method...")
            db = SessionLocal()
            
            # Check if column exists using PRAGMA
            result = db.execute("PRAGMA table_info(documents)")
            columns = [row[1] for row in result]
            
            if 'embeddings_created_at' in columns:
                print("✅ Column 'embeddings_created_at' already exists")
            else:
                # Add the column
                db.execute("ALTER TABLE documents ADD COLUMN embeddings_created_at DATETIME")
                db.commit()
                print("✅ Column 'embeddings_created_at' added successfully")
                
        except Exception as e2:
            print(f"❌ Alternative method also failed: {e2}")
            print("\n💡 Manual solution:")
            print("1. Backup your database: copy pdf_chatbot.db to pdf_chatbot_backup.db")
            print("2. Delete pdf_chatbot.db")
            print("3. Restart the backend - it will create a new database with the column")
        finally:
            db.close()

if __name__ == "__main__":
    add_embeddings_created_at_column()