#!/usr/bin/env python
"""Initialize database with default users"""

import os
import sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.getcwd())

from app.database import engine, Base, SessionLocal
from app.models.user import User, UserRole
from app.auth.utils import get_password_hash

# Create tables
Base.metadata.create_all(bind=engine)

db = SessionLocal()

# Check if users already exist
existing_users = db.query(User).count()
if existing_users > 0:
    print(f"Database already has {existing_users} users")
    db.close()
    sys.exit(0)

# Create default users
users = [
    User(
        username="superadmin",
        email="superadmin@example.com",
        hashed_password=get_password_hash("superadmin"),
        full_name="Super Admin",
        role=UserRole.SUPERADMIN,
        is_active=True
    ),
    User(
        username="admin",
        email="admin@example.com",
        hashed_password=get_password_hash("admin"),
        full_name="Admin User",
        role=UserRole.ADMIN,
        is_active=True
    ),
    User(
        username="user",
        email="user@example.com",
        hashed_password=get_password_hash("user"),
        full_name="Regular User",
        role=UserRole.USER,
        is_active=True
    )
]

for user in users:
    db.add(user)

db.commit()
print(f"Created {len(users)} default users:")
print("  - superadmin / superadmin (SUPERADMIN)")
print("  - admin / admin (ADMIN)")
print("  - user / user (USER)")
db.close()
