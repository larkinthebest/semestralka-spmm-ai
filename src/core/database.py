from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./ai_tutor.db?check_same_thread=False"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    from .models import User, Document, Quiz, Chat
    Base.metadata.create_all(bind=engine)
    
    # Create demo user if it doesn't exist
    db = SessionLocal()
    try:
        demo_user = db.query(User).filter(User.id == 1).first()
        if not demo_user:
            demo_user = User(
                id=1,
                email="guest@example.com",
                username="Guest User",
                hashed_password=""  # No password for guest
            )
            db.add(demo_user)
            db.commit()
            print("✅ Guest user created")
        
        # Create test user if it doesn't exist
        test_user = db.query(User).filter(User.email == "test@example.com").first()
        if not test_user:
            from .auth import get_password_hash
            test_user = User(
                email="test@example.com",
                username="test",
                hashed_password=get_password_hash("test")
            )
            db.add(test_user)
            db.commit()
            print("✅ Test user created")
        
        print(f"📊 Database initialized with {db.query(User).count()} users")
    except Exception as e:
        print(f"❌ Database initialization error: {e}")
        db.rollback()
    finally:
        db.close()