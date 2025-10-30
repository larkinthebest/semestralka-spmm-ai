from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

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
    from .models import User, Asset, Source, Quiz, Question, Answer, Chat, QuizResult, StudySuggestion
    from datetime import datetime, timezone
    from pathlib import Path
    import sys

    # Add project root to path for samples
    project_root = Path(__file__).parent.parent.parent
    sys.path.append(str(project_root))

    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Create guest user if it doesn't exist
        guest_user = db.query(User).filter(User.id == 1).first()
        if not guest_user:
            guest_user = User(
                id=1,
                email="guest@example.com",
                username="Guest User",
                hashed_password=""  # No password for guest
            )
            db.add(guest_user)
            db.commit()
            db.refresh(guest_user)
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
            db.refresh(test_user)
            print("✅ Test user created")

        # --- Add sample data for test user (ID 2) if not already present ---
        # Check if assets already exist for test_user
        existing_assets_count = db.query(Asset).filter(Asset.user_id == test_user.id).count()
        if existing_assets_count == 0:
            print("Adding sample assets for test user...")
            sample_asset_1_path = project_root / "samples" / "ai_concepts.md"
            sample_asset_2_path = project_root / "samples" / "sample_text.txt"

            asset1 = None
            if sample_asset_1_path.exists():
                asset1 = Asset(
                    filename="ai_concepts.md",
                    file_path=str(sample_asset_1_path),
                    content="Content of AI Concepts Markdown file.", # Placeholder content
                    user_id=test_user.id
                )
                db.add(asset1)
            else:
                print(f"⚠️ Sample file not found: {sample_asset_1_path}. Skipping asset creation.")

            asset2 = None
            if sample_asset_2_path.exists():
                asset2 = Asset(
                    filename="sample_text.txt",
                    file_path=str(sample_asset_2_path),
                    content="Content of Sample Text file.", # Placeholder content
                    user_id=test_user.id
                )
                db.add(asset2)
            else:
                print(f"⚠️ Sample file not found: {sample_asset_2_path}. Skipping asset creation.")
            
            db.flush() # Flush to get asset IDs

            # Create chats for test user if not existing
            existing_chats_count = db.query(Chat).filter(Chat.user_id == test_user.id).count()
            if existing_chats_count == 0:
                print("Adding sample chats for test user...")
                chat1 = Chat(
                    chat_id=1,
                    user_id=test_user.id,
                    title="Test Chat 1 (AI Concepts)",
                    mode="explanation",
                    tutor="enola",
                    current_tutor="enola",
                    current_mode="explanation",
                    messages=[
                        {"role": "user", "content": "Explain AI concepts.", "timestamp": datetime.now(timezone.utc).isoformat()},
                        {"role": "assistant", "content": "Based on 'ai_concepts.md', AI is...", "timestamp": datetime.now(timezone.utc).isoformat()}
                    ],
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                )
                db.add(chat1)

                chat2 = Chat(
                    chat_id=2,
                    user_id=test_user.id,
                    title="Test Chat 2 (Sample Text)",
                    mode="explanation",
                    tutor="enola",
                    current_tutor="enola",
                    current_mode="explanation",
                    messages=[
                        {"role": "user", "content": "Summarize the sample text.", "timestamp": datetime.now(timezone.utc).isoformat()},
                        {"role": "assistant", "content": "The sample text discusses...", "timestamp": datetime.now(timezone.utc).isoformat()}
                    ],
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                )
                db.add(chat2)
                db.flush() # Flush to get chat IDs

                # Link assets to chats
                if asset1:
                    source1 = Source(asset_id=asset1.id, chat_id=chat1.id)
                    db.add(source1)
                if asset2:
                    source2 = Source(asset_id=asset2.id, chat_id=chat2.id)
                    db.add(source2)
                print("✅ Sample chats created")

            # Create quizzes for test user if not existing
            existing_quizzes_count = db.query(Quiz).filter(Quiz.user_id == test_user.id).count()
            if existing_quizzes_count == 0:
                print("Adding sample quizzes for test user...")
                quiz1 = Quiz(
                    title="AI Concepts Quiz",
                    quiz_type="multiple_choice",
                    user_id=test_user.id,
                    asset_id=asset1.id if asset1 else None
                )
                db.add(quiz1)
                db.flush()

                question1_q1 = Question(
                    quiz_id=quiz1.id,
                    question_text="What is a neural network?",
                    question_type="multiple_choice",
                    options=["A) A type of database", "B) A model inspired by the human brain", "C) A programming language", "D) A data structure"],
                    correct_answer="B) A model inspired by the human brain",
                    explanation="Neural networks are a core component of deep learning, a subfield of machine learning, and are inspired by the structure and function of the human brain."
                )
                question2_q1 = Question(
                    quiz_id=quiz1.id,
                    question_text="Which of these is a subfield of AI?",
                    question_type="multiple_choice",
                    options=["A) Thermodynamics", "B) Machine Learning", "C) Quantum Physics", "D) Organic Chemistry"],
                    correct_answer="B) Machine Learning",
                    explanation="Machine Learning is a prominent subfield of Artificial Intelligence that focuses on enabling systems to learn from data."
                )
                db.add_all([question1_q1, question2_q1])
                db.flush()

                quiz_result1 = QuizResult(
                    quiz_id=quiz1.id,
                    user_id=test_user.id,
                    score=1,
                    total_questions=2,
                    completed_at=datetime.now(timezone.utc)
                )
                db.add(quiz_result1)
                db.flush()

                answer1_q1 = Answer(
                    question_id=question1_q1.id,
                    quiz_result_id=quiz_result1.id,
                    user_answer="A) A type of database",
                    is_correct=False
                )
                answer2_q1 = Answer(
                    question_id=question2_q1.id,
                    quiz_result_id=quiz_result1.id,
                    user_answer="B) Machine Learning",
                    is_correct=True
                )
                db.add_all([answer1_q1, answer2_q1])

                quiz2 = Quiz(
                    title="Sample Text Quiz",
                    quiz_type="short_answer",
                    user_id=test_user.id,
                    asset_id=asset2.id if asset2 else None
                )
                db.add(quiz2)
                db.flush()

                question1_q2 = Question(
                    quiz_id=quiz2.id,
                    question_text="What is the main topic of the sample text?",
                    question_type="short_answer",
                    correct_answer="Placeholder for main topic",
                    explanation="The sample text discusses various aspects of AI, including its definition, applications, and ethical considerations."
                )
                db.add(question1_q2)
                db.flush()

                quiz_result2 = QuizResult(
                    quiz_id=quiz2.id,
                    user_id=test_user.id,
                    score=1,
                    total_questions=1,
                    completed_at=datetime.now(timezone.utc)
                )
                db.add(quiz_result2)
                db.flush()

                answer1_q2 = Answer(
                    question_id=question1_q2.id,
                    quiz_result_id=quiz_result2.id,
                    user_answer="User's answer to sample text topic",
                    is_correct=True # Assuming correct for test data
                )
                db.add(answer1_q2)
                print("✅ Sample quizzes created")
            
            db.commit() # Commit all sample data if added
        
        print(f"📊 Database initialized with {db.query(User).count()} users and sample data.")
    except Exception as e:
        print(f"❌ Database initialization error: {e}")
        db.rollback()
    finally:
        db.close()
