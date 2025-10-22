#!/usr/bin/env python3
"""
Database migration script to update Chat model structure
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from src.core.database import engine, SessionLocal
from src.core.models import Base, User, Document, Quiz, Chat
from sqlalchemy import text

def migrate_database():
    """Migrate database to new Chat model structure"""
    print("🔄 Starting database migration...")
    
    try:
        # Drop existing tables to recreate with new structure
        print("📊 Recreating database tables...")
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        
        # Create users
        db = SessionLocal()
        try:
            # Create guest user
            guest_user = User(
                id=1,
                email="guest@example.com",
                username="Guest User",
                hashed_password=""
            )
            db.add(guest_user)
            
            # Create test user
            from src.core.auth import get_password_hash
            test_user = User(
                email="test@example.com",
                username="test",
                hashed_password=get_password_hash("test")
            )
            db.add(test_user)
            
            db.commit()
            print("✅ Users created successfully")
            
        except Exception as e:
            print(f"❌ Error creating users: {e}")
            db.rollback()
        finally:
            db.close()
            
        print("✅ Database migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = migrate_database()
    if success:
        print("\n🎉 Migration completed! You can now run the application.")
    else:
        print("\n💥 Migration failed! Please check the errors above.")
        sys.exit(1)