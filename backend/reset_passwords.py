#!/usr/bin/env python3
"""
Reset all user passwords to match frontend expectations
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.user import User, UserRole
from app.auth.utils import get_password_hash

def reset_passwords():
    """Reset passwords for all demo users"""
    
    db = SessionLocal()
    
    # Password mapping: username -> password
    password_map = {
        "superadmin": "admin123",
        "admin": "admin123",
        "user": "user123",
        "test": "test123"
    }
    
    print("🔄 Resetting passwords...")
    print("=" * 50)
    
    for username, password in password_map.items():
        user = db.query(User).filter(User.username == username).first()
        
        if user:
            # Update password
            user.hashed_password = get_password_hash(password)
            print(f"✅ Updated password for {username}: {password}")
            
            # Also fix email if needed
            if username == "superadmin" and user.email != "superadmin@example.com":
                user.email = "superadmin@example.com"
                print(f"   Fixed email: {user.email}")
            elif username == "admin" and user.email != "admin@example.com":
                user.email = "admin@example.com"
                print(f"   Fixed email: {user.email}")
        else:
            print(f"❌ User not found: {username}")
    
    try:
        db.commit()
        print("\n✅ All passwords updated successfully!")
        
        # Display final user list
        print("\n📋 Final User List:")
        print("-" * 60)
        users = db.query(User).all()
        for u in users:
            print(f"  👤 {u.username} ({u.email})")
            print(f"    Role: {u.role.value} | Active: {u.is_active}")
            print(f"    Login with password: {password_map.get(u.username, 'Unknown')}")
            print()
            
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    reset_passwords()