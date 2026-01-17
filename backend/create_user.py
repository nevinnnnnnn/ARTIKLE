#!/usr/bin/env python3
"""
Script to create demo users for the PDF Chatbot system.
Run this from the backend directory.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models.user import User, UserRole
from app.auth.utils import get_password_hash
from sqlalchemy.exc import IntegrityError

def create_demo_users():
    """Create demo users: superadmin, admin, and regular user"""
    
    db = SessionLocal()
    
    demo_users = [
        {
            "email": "superadmin@example.com",
            "username": "superadmin",
            "password": "admin123",
            "full_name": "Super Admin",
            "role": UserRole.SUPERADMIN,
            "is_active": True
        },
        {
            "email": "admin@example.com",
            "username": "admin",
            "password": "admin123",
            "full_name": "Admin User",
            "role": UserRole.ADMIN,
            "is_active": True
        },
        {
            "email": "user@example.com",
            "username": "user",
            "password": "user123",
            "full_name": "Regular User",
            "role": UserRole.USER,
            "is_active": True
        },
        {
            "email": "test@example.com",
            "username": "test",
            "password": "test123",
            "full_name": "Test User",
            "role": UserRole.USER,
            "is_active": True
        }
    ]
    
    created_count = 0
    existing_count = 0
    
    for user_data in demo_users:
        try:
            # Check if user exists
            existing = db.query(User).filter(
                (User.username == user_data["username"]) | 
                (User.email == user_data["email"])
            ).first()
            
            if not existing:
                user = User(
                    email=user_data["email"],
                    username=user_data["username"],
                    hashed_password=get_password_hash(user_data["password"]),
                    full_name=user_data["full_name"],
                    role=user_data["role"],
                    is_active=user_data["is_active"]
                )
                db.add(user)
                created_count += 1
                print(f"✅ Created user: {user_data['username']} ({user_data['role'].value})")
            else:
                existing_count += 1
                print(f"ℹ️ User already exists: {user_data['username']}")
        
        except IntegrityError as e:
            db.rollback()
            print(f"❌ Error creating user {user_data['username']}: {str(e)}")
    
    try:
        db.commit()
        print(f"\n🎯 Summary: Created {created_count} new users, {existing_count} already existed")
        print("\n📋 Demo Credentials:")
        print("=" * 40)
        print("👑 SUPERADMIN:")
        print("  Username: superadmin")
        print("  Password: admin123")
        print("\n🛠️ ADMIN:")
        print("  Username: admin")
        print("  Password: admin123")
        print("\n👤 USER:")
        print("  Username: user")
        print("  Password: user123")
        print("\n👤 TEST USER:")
        print("  Username: test")
        print("  Password: test123")
        print("=" * 40)
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error committing changes: {str(e)}")
    finally:
        db.close()

def list_existing_users():
    """List all existing users in the database"""
    
    db = SessionLocal()
    users = db.query(User).all()
    
    print("\n📊 Existing Users in Database:")
    print("=" * 60)
    print(f"{'ID':<5} {'Username':<15} {'Email':<25} {'Role':<12} {'Active':<8}")
    print("-" * 60)
    
    for user in users:
        status = "✅" if user.is_active else "❌"
        print(f"{user.id:<5} {user.username:<15} {user.email:<25} {user.role.value:<12} {status:<8}")
    
    print("=" * 60)
    db.close()

def check_database():
    """Check if database exists and has tables"""
    
    from sqlalchemy import inspect
    
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    print("\n🔍 Database Check:")
    print(f"Database URL: {engine.url}")
    print(f"Tables found: {tables}")
    
    if 'users' in tables:
        print("✅ Users table exists")
        list_existing_users()
    else:
        print("❌ Users table doesn't exist. Creating tables...")
        from app.database import Base
        Base.metadata.create_all(bind=engine)
        print("✅ Tables created")

if __name__ == "__main__":
    print("🤖 PDF Chatbot User Setup Utility")
    print("=" * 50)
    
    # Check database first
    check_database()
    
    # Ask if user wants to create demo users
    print("\nDo you want to create demo users? (y/n)")
    response = input().lower().strip()
    
    if response == 'y' or response == 'yes':
        print("\nCreating demo users...")
        create_demo_users()
    else:
        print("\nSkipping user creation.")
    
    print("\n🎉 Setup complete!")
    print("\n💡 Next steps:")
    print("1. Start backend server: python -m app.main")
    print("2. Start frontend: streamlit run app.py")
    print("3. Login with superadmin/admin123")