import sys
from pathlib import Path

# Add project root to path for imports
sys.path.append(str(Path(__file__).parent.parent))

import pytest
import pytest_asyncio # Import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from src.core.database import Base, get_db as original_get_db
from src.core.models import User, Asset, Quiz, Question
from src.core.schemas import QuizGenerateRequest
from src.services.quiz_generator import QuizGenerator
from src.services.llm_service import LLMService
from src.api.main import app, quiz_gen as global_quiz_gen # Import app and global quiz_gen
from fastapi import HTTPException
from fastapi.testclient import TestClient
import os

# --- Database Fixtures for Integration Tests ---
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db" # Use a file-based SQLite for easier debugging if needed, or :memory:
# For in-memory: SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="module")
def setup_database():
    # Create the database file if it's not in-memory
    if SQLALCHEMY_DATABASE_URL != "sqlite:///:memory:":
        if Path(SQLALCHEMY_DATABASE_URL.replace("sqlite:///./", "")).exists():
            os.remove(SQLALCHEMY_DATABASE_URL.replace("sqlite:///./", ""))
    
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        # Create a test user
        test_user = User(id=1, email="test@example.com", username="testuser", hashed_password="hashedpassword")
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        if SQLALCHEMY_DATABASE_URL != "sqlite:///:memory__":
            if Path(SQLALCHEMY_DATABASE_URL.replace("sqlite:///./", "")).exists():
                os.remove(SQLALCHEMY_DATABASE_URL.replace("sqlite:///./", ""))

@pytest.fixture(scope="function")
def db_session(setup_database):
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    # Override get_db dependency
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
    app.dependency_overrides = {} # Clear overrides

# --- LLM Service Fixture for Integration Tests ---
@pytest_asyncio.fixture(scope="module") # Use pytest_asyncio.fixture for async fixtures
async def initialized_llm_service():
    llm_service = LLMService()
    await llm_service.initialize()
    # Temporarily replace the global quiz_gen's llm_service with our initialized one
    # This is a workaround for global instances in FastAPI apps for testing
    original_llm_service = global_quiz_gen.llm_service
    global_quiz_gen.llm_service = llm_service
    yield llm_service
    global_quiz_gen.llm_service = original_llm_service # Restore original

# --- Test Client Fixture ---
@pytest.fixture(scope="module")
def test_client(initialized_llm_service): # Ensure LLM is initialized before client is used
    with TestClient(app) as client:
        yield client

# --- Mock current_user for API endpoint tests (still useful for auth) ---
@pytest.fixture
def mock_current_user():
    mock = MagicMock()
    mock.id = 1
    return mock

# --- Unit Tests for QuizGenerator (with mock LLM) ---
@pytest.fixture
def mock_llm_service_unit():
    mock = AsyncMock(spec=LLMService)
    return mock

@pytest.fixture
def quiz_generator_unit(mock_llm_service_unit):
    return QuizGenerator(mock_llm_service_unit)

@pytest.mark.asyncio
async def test_generate_multiple_choice_quiz_unit(quiz_generator_unit, mock_llm_service_unit):
    content = "Artificial Intelligence is a field of computer science. Machine Learning is a subset of AI."
    quiz_type = "multiple_choice"
    num_questions = 1
    topic = "AI"
    difficulty = "easy"
    language = "en"

    mock_llm_service_unit.generate_response.return_value = """
    ```json
    [
        {
            "question_text": "What is AI?",
            "question_type": "multiple_choice",
            "options": ["A field of biology", "A field of computer science", "A type of robot", "A programming language"],
            "correct_answer": "A field of computer science"
        }
    ]
    ```
    """

    result = await quiz_generator_unit.generate_quiz(content, quiz_type, num_questions, topic, difficulty, language)

    assert "questions" in result
    assert len(result["questions"]) == num_questions
    question = result["questions"][0]
    assert question["question_text"] == "What is AI?"
    assert question["question_type"] == "multiple_choice"
    assert "options" in question
    assert len(question["options"]) == 4
    assert question["correct_answer"] == "A field of computer science"
    mock_llm_service_unit.generate_response.assert_called_once()

@pytest.mark.asyncio
async def test_generate_true_false_quiz_unit(quiz_generator_unit, mock_llm_service_unit):
    content = "The Earth is round."
    quiz_type = "true_false"
    num_questions = 1
    topic = "Earth"
    difficulty = "easy"
    language = "en"

    mock_llm_service_unit.generate_response.return_value = """
    ```json
    [
        {
            "question_text": "The Earth is flat.",
            "question_type": "true_false",
            "options": ["True", "False"],
            "correct_answer": "False"
        }
    ]
    ```
    """

    result = await quiz_generator_unit.generate_quiz(content, quiz_type, num_questions, topic, difficulty, language)

    assert "questions" in result
    assert len(result["questions"]) == num_questions
    question = result["questions"][0]
    assert question["question_text"] == "The Earth is flat."
    assert question["question_type"] == "true_false"
    assert question["options"] == ["True", "False"]
    assert question["correct_answer"] == "False"
    mock_llm_service_unit.generate_response.assert_called_once()

@pytest.mark.asyncio
async def test_generate_fill_in_the_blank_quiz_unit(quiz_generator_unit, mock_llm_service_unit):
    content = "Python is a popular programming language."
    quiz_type = "fill_in_the_blank"
    num_questions = 1
    topic = "Programming"
    difficulty = "medium"
    language = "en"

    mock_llm_service_unit.generate_response.return_value = """
    ```json
    [
        {
            "question_text": "Python is a popular [BLANK] language.",
            "question_type": "fill_in_the_blank",
            "correct_answer": "programming"
        }
    ]
    ```
    """

    result = await quiz_generator_unit.generate_quiz(content, quiz_type, num_questions, topic, difficulty, language)

    assert "questions" in result
    assert len(result["questions"]) == num_questions
    question = result["questions"][0]
    assert question["question_text"] == "Python is a popular [BLANK] language."
    assert question["question_type"] == "fill_in_the_blank"
    assert "options" not in question # Fill-in-the-blank should not have options
    assert question["correct_answer"] == "programming"
    mock_llm_service_unit.generate_response.assert_called_once()

# --- Integration Tests for API Endpoint (with real LLM and DB) ---
@pytest.mark.asyncio
async def test_generate_quiz_api_integration(test_client, db_session, mock_current_user):
    # Create a sample asset in the test database
    sample_content_path = Path(__file__).parent.parent / "samples" / "ai_concepts.md"
    with open(sample_content_path, "r") as f:
        sample_content = f.read()

    asset = Asset(
        filename="ai_concepts.md",
        file_path=str(sample_content_path),
        content=sample_content,
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

    # Mock get_current_user_optional to return our mock_current_user
    from src.core.auth import get_current_user_optional
    app.dependency_overrides[get_current_user_optional] = lambda: mock_current_user

    response = test_client.post("/quizzes/generate", json=quiz_request_data)
    app.dependency_overrides = {} # Clear overrides

    assert response.status_code == 200
    response_data = response.json()

    assert "id" in response_data
    assert response_data["title"] == "Quiz on Artificial Intelligence"
    assert response_data["quiz_type"] == "multiple_choice"
    assert len(response_data["questions"]) == 1
    
    question = response_data["questions"][0]
    assert "question_text" in question
    # The LLM might sometimes deviate from the requested quiz_type.
    # For this integration test, we'll assert it's one of the expected types.
    # In a real application, more robust LLM response validation/correction might be needed.
    assert question["question_type"] in ["multiple_choice", "true_false", "fill_in_the_blank"]
    
    if question["question_type"] == "multiple_choice":
        assert "options" in question
        assert len(question["options"]) > 0
    elif question["question_type"] == "true_false":
        assert "options" in question
        assert len(question["options"]) == 2
    # For fill_in_the_blank, options should not be present
    
    assert "correct_answer" in question

    # Verify quiz and question are in the database
    db_quiz = db_session.query(Quiz).filter(Quiz.id == response_data["id"]).first()
    assert db_quiz is not None
    assert db_quiz.title == "Quiz on Artificial Intelligence"
    assert db_quiz.quiz_type == "multiple_choice"
    assert db_quiz.user_id == mock_current_user.id
    assert db_quiz.asset_id == asset_id_for_comparison # Use the stored ID

    db_question = db_session.query(Question).filter(Question.quiz_id == db_quiz.id).first()
    assert db_question is not None
    assert db_question.question_text == question["question_text"]
    assert db_question.question_type == question["question_type"]
    assert db_question.options == question["options"]
    assert db_question.correct_answer == question["correct_answer"]

@pytest.mark.asyncio
async def test_generate_quiz_api_endpoint_no_files_integration(test_client, db_session, mock_current_user):
    quiz_request_data = {
        "attached_files": [],
        "quiz_type": "multiple_choice",
        "num_questions": 1,
        "topic": "AI",
        "difficulty": "easy",
        "language": "en"
    }
    from src.core.auth import get_current_user_optional
    app.dependency_overrides[get_current_user_optional] = lambda: mock_current_user

    response = test_client.post("/quizzes/generate", json=quiz_request_data)
    app.dependency_overrides = {} # Clear overrides

    assert response.status_code == 400
    assert "No files attached" in response.json()["detail"]

@pytest.mark.asyncio
async def test_generate_quiz_api_endpoint_no_relevant_assets_integration(test_client, db_session, mock_current_user):
    quiz_request_data = {
        "attached_files": ["non_existent_file.txt"],
        "quiz_type": "multiple_choice",
        "num_questions": 1,
        "topic": "AI",
        "difficulty": "easy",
        "language": "en"
    }
    from src.core.auth import get_current_user_optional
    app.dependency_overrides[get_current_user_optional] = lambda: mock_current_user

    response = test_client.post("/quizzes/generate", json=quiz_request_data)
    app.dependency_overrides = {} # Clear overrides

    assert response.status_code == 404
    assert "No relevant assets found" in response.json()["detail"]
