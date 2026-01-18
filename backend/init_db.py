#!/usr/bin/env python
"""
Database initialization script to set up the database and create default users.
This script should be run once to initialize the database.
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import engine, Base, SessionLocal
from app.models.user import User, UserRole
from app.auth.utils import get_password_hash
from app.config import settings

def init_db():
    """Initialize database with tables and default users"""
    
    print("🔄 Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully!")
    
    # Create a session
    db = SessionLocal()
    
    try:
        # Create default superadmin
        superadmin_username = "superadmin"
        superadmin_email = "superadmin@artikle.local"
        superadmin_password = "superadmin123"
        
        # Check if superadmin already exists
        existing_superadmin = db.query(User).filter(
            User.username == superadmin_username
        ).first()
        
        if existing_superadmin:
            print(f"⚠️  Superadmin user already exists: {superadmin_username}")
        else:
            superadmin = User(
                email=superadmin_email,
                username=superadmin_username,
                hashed_password=get_password_hash(superadmin_password),
                full_name="Super Administrator",
                role=UserRole.SUPERADMIN,
                is_active=True
            )
            db.add(superadmin)
            db.commit()
            db.refresh(superadmin)
            print(f"✅ Superadmin user created!")
            print(f"   Username: {superadmin_username}")
            print(f"   Email: {superadmin_email}")
            print(f"   Password: {superadmin_password}")
        
        # Create default admin
        admin_username = "admin"
        admin_email = "admin@artikle.local"
        admin_password = "admin123"
        
        existing_admin = db.query(User).filter(
            User.username == admin_username
        ).first()
        
        if existing_admin:
            print(f"⚠️  Admin user already exists: {admin_username}")
        else:
            admin = User(
                email=admin_email,
                username=admin_username,
                hashed_password=get_password_hash(admin_password),
                full_name="Administrator",
                role=UserRole.ADMIN,
                is_active=True
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)
            print(f"✅ Admin user created!")
            print(f"   Username: {admin_username}")
            print(f"   Email: {admin_email}")
            print(f"   Password: {admin_password}")
        
        # Create default user
        user_username = "user"
        user_email = "user@artikle.local"
        user_password = "user123"
        
        existing_user = db.query(User).filter(
            User.username == user_username
        ).first()
        
        if existing_user:
            print(f"⚠️  User already exists: {user_username}")
        else:
            user = User(
                email=user_email,
                username=user_username,
                hashed_password=get_password_hash(user_password),
                full_name="Regular User",
                role=UserRole.USER,
                is_active=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"✅ User created!")
            print(f"   Username: {user_username}")
            print(f"   Email: {user_email}")
            print(f"   Password: {user_password}")
        
        print("\n📋 Summary:")
        print("============================================")
        print("🔐 SUPERADMIN CREDENTIALS:")
        print(f"   Username: superadmin")
        print(f"   Password: superadmin123")
        print("\n🔐 ADMIN CREDENTIALS:")
        print(f"   Username: admin")
        print(f"   Password: admin123")
        print("\n🔐 USER CREDENTIALS:")
        print(f"   Username: user")
        print(f"   Password: user123")
        print("============================================")
        print("\n✨ Database initialization complete!")
        
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
