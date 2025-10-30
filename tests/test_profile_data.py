import sys
from pathlib import Path
import os
from datetime import datetime

# Add project root to path for imports
sys.path.append(str(Path(__file__).parent.parent))

import pytest
import pytest_asyncio
from unittest.mock import MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from src.core.database import Base, get_db as original_get_db
from src.core.models import User, Asset, Quiz, Chat, Source, Question, QuizResult, Answer
from src.core.auth import get_password_hash, create_access_token
from src.api.main import app, llm_service as global_llm_service # Import app and global llm_service
from fastapi.testclient import TestClient

# --- Database Fixtures for Integration Tests ---
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_profile.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="module")
def setup_database():
    if SQLALCHEMY_DATABASE_URL != "sqlite:///:memory:":
        if Path(SQLALCHEMY_DATABASE_URL.replace("sqlite:///./", "")).exists():
            os.remove(SQLALCHEMY_DATABASE_URL.replace("sqlite:///./", ""))
    
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        # Create a test user
        test_user = User(id=2, email="test@example.com", username="testuser", hashed_password=get_password_hash("test")) # Changed ID to 2
        db.add(test_user)
        db.commit()
        db.refresh(test_user)

        # Create assets for test user
        sample_asset_1_path = Path(__file__).parent.parent.parent / "samples" / "ai_concepts.md"
        sample_asset_2_path = Path(__file__).parent.parent.parent / "samples" / "sample_text.txt"

        asset1 = Asset(
            filename="ai_concepts.md",
            file_path=str(sample_asset_1_path),
            content="Content of AI Concepts Markdown file.",
            user_id=test_user.id
        )
        asset2 = Asset(
            filename="sample_text.txt",
            file_path=str(sample_asset_2_path),
            content="Content of Sample Text file.",
            user_id=test_user.id
        )
        db.add_all([asset1, asset2])
        db.flush() # Flush to get asset IDs

        # Create chats for test user
        chat1 = Chat(
            chat_id=1,
            user_id=test_user.id,
            title="Test Chat 1 (AI Concepts)",
            mode="explanation",
            tutor="enola",
            current_tutor="enola",
            current_mode="explanation",
            messages=[
                {"role": "user", "content": "Explain AI concepts.", "timestamp": datetime.utcnow().isoformat()},
                {"role": "assistant", "content": "Based on 'ai_concepts.md', AI is...", "timestamp": datetime.utcnow().isoformat()}
            ],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        chat2 = Chat(
            chat_id=2,
            user_id=test_user.id,
            title="Test Chat 2 (Sample Text)",
            mode="explanation",
            tutor="enola",
            current_tutor="enola",
            current_mode="explanation",
            messages=[
                {"role": "user", "content": "Summarize the sample text.", "timestamp": datetime.utcnow().isoformat()},
                {"role": "assistant", "content": "The sample text discusses...", "timestamp": datetime.utcnow().isoformat()}
            ],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add_all([chat1, chat2])
        db.flush() # Flush to get chat IDs

        # Link assets to chats
        source1 = Source(asset_id=asset1.id, chat_id=chat1.id)
        source2 = Source(asset_id=asset2.id, chat_id=chat2.id)
        db.add_all([source1, source2])

        # Create quizzes for test user
        quiz1 = Quiz(
            title="AI Concepts Quiz",
            quiz_type="multiple_choice",
            user_id=test_user.id,
            asset_id=asset1.id
        )
        quiz2 = Quiz(
            title="Sample Text Quiz",
            quiz_type="short_answer",
            user_id=test_user.id,
            asset_id=asset2.id
        )
        db.add_all([quiz1, quiz2])
        db.flush()

        question1_q1 = Question(
            quiz_id=quiz1.id,
            question_text="What is a neural network?",
            question_type="multiple_choice",
            options=["A) A type of database", "B) A model inspired by the human brain", "C) A programming language", "D) A data structure"],
            correct_answer="B) A model inspired by the human brain"
        )
        question2_q1 = Question(
            quiz_id=quiz1.id,
            question_text="Which of these is a subfield of AI?",
            question_type="multiple_choice",
            options=["A) Thermodynamics", "B) Machine Learning", "C) Quantum Physics", "D) Organic Chemistry"],
            correct_answer="B) Machine Learning"
        )
        db.add_all([question1_q1, question2_q1])
        db.flush()

        quiz_result1 = QuizResult(
            quiz_id=quiz1.id,
            user_id=test_user.id,
            score=1,
            total_questions=2,
            completed_at=datetime.utcnow()
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
        db.flush()

        question1_q2 = Question(
            quiz_id=quiz2.id,
            question_text="What is the main topic of the sample text?",
            question_type="short_answer",
            correct_answer="Placeholder for main topic"
        )
        db.add(question1_q2)
        db.flush()

        quiz_result2 = QuizResult(
            quiz_id=quiz2.id,
            user_id=test_user.id,
            score=1,
            total_questions=1,
            completed_at=datetime.utcnow()
        )
        db.add(quiz_result2)
        db.flush()

        answer1_q2 = Answer(
            question_id=question1_q2.id,
            quiz_result_id=quiz_result2.id,
            user_answer="User's answer to sample text topic",
            is_correct=True
        )
        db.add(answer1_q2)
        db.commit()
        
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        if SQLALCHEMY_DATABASE_URL != "sqlite:///:memory:":
            if Path(SQLALCHEMY_DATABASE_URL.replace("sqlite:///./", "")).exists():
                os.remove(SQLALCHEMY_DATABASE_URL.replace("sqlite:///./", ""))

@pytest.fixture(scope="function")
def db_session(setup_database):
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    def override_get_db():
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[original_get_db] = override_get_db
    yield session
    session.close()
    transaction.rollback()
    connection.close()
    app.dependency_overrides = {}

@pytest_asyncio.fixture(scope="module")
async def initialized_llm_service():
    llm_service = global_llm_service # Use the global instance
    await llm_service.initialize()
    yield llm_service

@pytest.fixture(scope="module")
def test_client(initialized_llm_service):
    with TestClient(app) as client:
        yield client

@pytest.fixture
def auth_token(db_session):
    user = db_session.query(User).filter(User.email == "test@example.com").first()
    if not user:
        user = User(email="test@example.com", username="testuser", hashed_password=get_password_hash("test"))
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    return create_access_token(data={"sub": user.email})

@pytest.fixture
def mock_current_user():
    mock = MagicMock()
    mock.id = 2 # Mock user ID to match the test user created in setup_database
    return mock

# --- Tests for User Profile Data Visibility ---
@pytest.mark.asyncio
async def test_get_chats_list(test_client, db_session, auth_token, mock_current_user):
    from src.core.auth import get_current_user_optional
    app.dependency_overrides[get_current_user_optional] = lambda: mock_current_user

    response = test_client.get("/chats/list", headers={"Authorization": f"Bearer {auth_token}"})
    app.dependency_overrides = {}

    assert response.status_code == 200
    chats = response.json()
    assert len(chats) == 2
    assert chats[0]["title"] == "Test Chat 2 (Sample Text)" # Ordered by updated_at desc
    assert chats[1]["title"] == "Test Chat 1 (AI Concepts)"
    assert "attached_asset_filenames" in chats[0]
    assert "attached_asset_filenames" in chats[1]
    assert "sample_text.txt" in chats[0]["attached_asset_filenames"]
    assert "ai_concepts.md" in chats[1]["attached_asset_filenames"]

@pytest.mark.asyncio
async def test_get_documents(test_client, db_session, auth_token, mock_current_user):
    from src.core.auth import get_current_user_optional
    app.dependency_overrides[get_current_user_optional] = lambda: mock_current_user

    response = test_client.get("/documents", headers={"Authorization": f"Bearer {auth_token}"})
    app.dependency_overrides = {}

    assert response.status_code == 200
    assets = response.json()
    assert len(assets) == 2
    assert any(asset["filename"] == "ai_concepts.md" for asset in assets)
    assert any(asset["filename"] == "sample_text.txt" for asset in assets)

@pytest.mark.asyncio
async def test_get_quizzes(test_client, db_session, auth_token, mock_current_user):
    from src.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: mock_current_user

    response = test_client.get("/quizzes", headers={"Authorization": f"Bearer {auth_token}"})
    app.dependency_overrides = {}

    assert response.status_code == 200
    quizzes = response.json()
    assert len(quizzes) == 2
    assert any(quiz["title"] == "AI Concepts Quiz" for quiz in quizzes)
    assert any(quiz["title"] == "Sample Text Quiz" for quiz in quizzes)
    assert any(quiz["asset_filename"] == "ai_concepts.md" for quiz in quizzes)
    assert any(quiz["asset_filename"] == "sample_text.txt" for quiz in quizzes)

@pytest.mark.asyncio
async def test_get_quiz_history_enhanced(test_client, db_session, auth_token, mock_current_user):
    from src.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: mock_current_user

    response = test_client.get("/quiz-results/history", headers={"Authorization": f"Bearer {auth_token}"})
    app.dependency_overrides = {}

    assert response.status_code == 200
    history = response.json()["results"]
    assert len(history) == 2

    # Verify the structure and content of the enhanced history
    quiz_result_1 = next((r for r in history if r["quiz_title"] == "AI Concepts Quiz"), None)
    assert quiz_result_1 is not None
    assert quiz_result_1["asset_filename"] == "ai_concepts.md"
    assert quiz_result_1["score"] == 1
    assert quiz_result_1["total_questions"] == 2
    assert quiz_result_1["percentage"] == 50

    quiz_result_2 = next((r for r in history if r["quiz_title"] == "Sample Text Quiz"), None)
    assert quiz_result_2 is not None
    assert quiz_result_2["asset_filename"] == "sample_text.txt"
    assert quiz_result_2["score"] == 1
    assert quiz_result_2["total_questions"] == 1
    assert quiz_result_2["percentage"] == 100

# --- Tests for Franklin's Quiz Generation Capability ---
@pytest.mark.asyncio
async def test_franklin_quiz_generation_from_file(test_client, db_session, auth_token, mock_current_user):
    # Ensure the asset exists for the test user
    sample_content_path = Path(__file__).parent.parent.parent / "samples" / "ai_concepts.md"
    asset = db_session.query(Asset).filter(Asset.filename == "ai_concepts.md", Asset.user_id == mock_current_user.id).first()
    if not asset:
        asset = Asset(
            filename="ai_concepts.md",
            file_path=str(sample_content_path),
            content="Artificial Intelligence is a field of computer science. Machine Learning is a subset of AI.",
            user_id=mock_current_user.id
        )
        db_session.add(asset)
        db_session.commit()
        db_session.refresh(asset)
    
    # Store asset_id for later comparison as the asset object might become detached
    asset_id_for_comparison = asset.id

    quiz_request_data = {
        "attached_files": ["ai_concepts.md"],
        "quiz_type": "multiple_choice",
        "num_questions": 1,
        "topic": "Artificial Intelligence",
        "difficulty": "easy",
        "language": "en"
    }

    from src.core.auth import get_current_user_optional
    app.dependency_overrides[get_current_user_optional] = lambda: mock_current_user

    response = test_client.post("/quizzes/generate", json=quiz_request_data, headers={"Authorization": f"Bearer {auth_token}"})
    app.dependency_overrides = {}

    assert response.status_code == 200
    response_data = response.json()

    assert "id" in response_data
    assert response_data["title"] == "Quiz on Artificial Intelligence"
    assert response_data["quiz_type"] == "multiple_choice"
    assert len(response_data["questions"]) == 1
    
    question = response_data["questions"][0]
    assert "question_text" in question
    assert question["question_type"] in ["multiple_choice", "true_false", "fill_in_the_blank"]
    assert "correct_answer" in question

    # Verify quiz and question are in the database
    db_quiz = db_session.query(Quiz).filter(Quiz.id == response_data["id"]).first()
    assert db_quiz is not None
    assert db_quiz.title == "Quiz on Artificial Intelligence"
    assert db_quiz.quiz_type == "multiple_choice"
    assert db_quiz.user_id == mock_current_user.id
    assert db_quiz.asset_id == asset_id_for_comparison

    db_question = db_session.query(Question).filter(Question.quiz_id == db_quiz.id).first()
    assert db_question is not None
    assert db_question.question_text == question["question_text"]
    assert db_question.question_type == question["question_type"]
    assert db_question.correct_answer == question["correct_answer"]

@pytest.mark.asyncio
async def test_chat_attached_assets_persistence(test_client, db_session, auth_token, mock_current_user):
    from src.core.auth import get_current_user_optional
    app.dependency_overrides[get_current_user_optional] = lambda: mock_current_user

    # Create a new chat
    new_chat_response = test_client.post("/chats/new", headers={"Authorization": f"Bearer {auth_token}"})
    assert new_chat_response.status_code == 200
    new_chat_data = new_chat_response.json()
    chat_id = new_chat_data["chat_id"]

    # Get existing assets for the user
    assets_response = test_client.get("/assets", headers={"Authorization": f"Bearer {auth_token}"})
    assert assets_response.status_code == 200
    user_assets = assets_response.json()
    
    # Select some assets to attach
    attached_filenames = [asset["filename"] for asset in user_assets[:1]] # Attach the first asset

    # Save the chat with attached assets
    save_chat_response = test_client.post("/chats/save", 
        headers={"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"},
        json={
            "chat_id": chat_id,
            "title": "Chat with Attached Assets",
            "mode": "explanation",
            "tutor": "enola",
            "messages": [{"role": "user", "content": "Hello", "timestamp": datetime.utcnow().isoformat()}],
            "attached_asset_filenames": attached_filenames,
            "current_tutor": "enola",
            "current_mode": "explanation"
        }
    )
    assert save_chat_response.status_code == 200
    assert save_chat_response.json()["success"] is True

    # Load the chat details and verify attached assets
    load_chat_response = test_client.get(f"/chats/{chat_id}", headers={"Authorization": f"Bearer {auth_token}"})
    assert load_chat_response.status_code == 200
    loaded_chat_data = load_chat_response.json()

    assert "attached_asset_filenames" in loaded_chat_data
    assert loaded_chat_data["attached_asset_filenames"] == attached_filenames

    app.dependency_overrides = {}
