from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./ai_tutor.db"

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
                email="demo@example.com",
                username="Demo User",
                hashed_password="demo_hash"  # Simple hash for demo
            )
            db.add(demo_user)
            db.commit()
            print("✅ Demo user created")
    finally:
        db.close()