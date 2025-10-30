#!/usr/bin/env python3
"""
Database migration script to update Chat model structure
"""

import os
import sys
from pathlib import Path
import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from src.core.database import engine, SessionLocal
from src.core.models import Base, User, Asset, Quiz, Chat, Source, Question, Answer, QuizResult, StudySuggestion
from sqlalchemy import text
from datetime import datetime, timezone # Import timezone

def migrate_database():
    """Migrate database to new Chat model structure"""
    print("🔄 Starting database migration...")
    
    print("🔄 Starting database migration...")
    
    try:
        # Drop existing tables to recreate with new structure
        print("📊 Recreating database tables...")
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        
        # init_db() will now handle user and sample data creation
        # No need to duplicate logic here.
        
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
