from dotenv import load_dotenv # Import load_dotenv
load_dotenv() # Load environment variables from .env file

from fastapi import FastAPI, File, UploadFile, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import func # Import func
from contextlib import asynccontextmanager
from typing import Optional, List
import uvicorn
import os
from pathlib import Path


import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.core.database import get_db, init_db
from src.core.models import User, Asset, Source, Quiz, Question, Answer, Chat, QuizResult, StudySuggestion
from src.core.schemas import UserCreate, UserResponse, QuizCreate, QuizSubmit, StudySuggestionResponse, QuizGenerateRequest
from datetime import datetime
from src.core.auth import get_current_user, create_access_token, verify_password, get_password_hash, verify_google_token, create_or_get_google_user, get_current_user_optional
from src.services.llm_service import LLMService
from src.processors.multimedia_processor import MultimediaProcessor
from src.services.quiz_generator import QuizGenerator
from sqlalchemy.orm import joinedload # Import joinedload for eager loading

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    await llm_service.initialize()
    yield
    # Shutdown (if needed)

app = FastAPI(title="AI Tutor Platform", version="1.0.0", lifespan=lifespan)

# Debug: Print all registered routes at startup
@app.on_event("startup")
async def startup_event():
    print("\n--- Registered FastAPI Routes ---")
    for route in app.routes:
        if hasattr(route, "path") and hasattr(route, "methods"):
            print(f"Path: {route.path}, Methods: {list(route.methods)}")
    print("---------------------------------\n")

@app.get("/debug/routes")
async def debug_routes():
    routes_info = []
    for route in app.routes:
        if hasattr(route, "path") and hasattr(route, "methods"):
            routes_info.append({"path": route.path, "methods": list(route.methods)})
    return {"routes": routes_info}

@app.get("/debug/assets/{user_id}")
async def debug_get_assets_for_user(user_id: int, db: Session = Depends(get_db)):
    assets = db.query(Asset).filter(Asset.user_id == user_id).all()
    return [{"id": asset.id, "filename": asset.filename, "file_path": asset.file_path, "created_at": asset.created_at} for asset in assets]

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
llm_service = LLMService()
print(f"DEBUG: Global LLMService instance created in main.py: {id(llm_service)}, model_name: {llm_service.full_model_name}")
multimedia_processor = MultimediaProcessor()
quiz_gen = QuizGenerator(llm_service)

# Get the project root directory (two levels up from main.py)
BASE_DIR = Path(__file__).parent.parent.parent

# Create directories with absolute paths
os.makedirs(BASE_DIR / "uploads", exist_ok=True)
os.makedirs(BASE_DIR / "static", exist_ok=True)

# Mount static files with absolute path
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
app.mount("/uploads", StaticFiles(directory=str(BASE_DIR / "uploads")), name="uploads")

@app.get("/", response_class=HTMLResponse)
async def root():
    # Serve the main app interface
    app_html_path = BASE_DIR / "static" / "app.html"
    with open(app_html_path, "r") as f:
        return f.read()

@app.get("/auth", response_class=HTMLResponse)
async def auth_page():
    # Serve the authentication page
    auth_html_path = BASE_DIR / "static" / "auth.html"
    with open(auth_html_path, "r") as f:
        return f.read()

# Auth endpoints
@app.post("/auth/register", response_model=UserResponse)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user.password)
    db_user = User(email=user.email, username=user.username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return UserResponse(id=db_user.id, email=db_user.email, username=db_user.username)

@app.post("/auth/login")
async def login(request: dict, db: Session = Depends(get_db)):
    email = request.get("email")
    password = request.get("password")
    
    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password are required")
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer", "user": {"id": user.id, "email": user.email, "username": user.username}}

@app.post("/auth/google")
async def google_auth(request: dict, db: Session = Depends(get_db)):
    google_token = request.get("google_token")
    
    if not google_token:
        raise HTTPException(status_code=400, detail="Google token is required")
    """Authenticate with Google OAuth token"""
    try:
        user_info = await verify_google_token(google_token)
        user = create_or_get_google_user(user_info, db)
        access_token = create_access_token(data={"sub": user.email})
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Google auth error: {e}")
        raise HTTPException(status_code=401, detail="Google authentication failed")

@app.get("/auth/me")
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user info"""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "username": current_user.username
    }

# Document endpoints
@app.post("/documents/upload") # Renamed from /assets/upload to /documents/upload
async def upload_asset(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user_id = current_user.id
    allowed_extensions = [
        '.pdf', '.docx', '.txt', '.md', '.jpg', '.jpeg', '.png', '.gif', '.bmp',
        '.mp3', '.wav', '.m4a', '.ogg', '.mp4', '.avi', '.mov', '.mkv', '.webm',
        '.pptx', '.ppt', '.js', '.css', '.html', '.py', '.c', '.cpp', '.java', '.go', '.rb', '.php', '.ts', '.tsx', '.jsx', '.json', '.xml', '.yaml', '.yml'
    ]
    file_extension = Path(file.filename).suffix.lower()

    print(f"DEBUG: Received file for upload: {file.filename}, content_type: {file.content_type}")
    print(f"DEBUG: File size: {file.size}") # Note: file.size might be 0 until read

    if file_extension not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"File type {file_extension} not supported")

    existing_asset = db.query(Asset).filter(Asset.filename == file.filename, Asset.user_id == user_id).first()
    if existing_asset:
        return {
            "id": existing_asset.id, 
            "filename": existing_asset.filename, 
            "file_type": "existing",
            "description": "File already exists",
            "message": "File already uploaded"
        }
    
    file_path = BASE_DIR / "uploads" / file.filename
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    file_info = multimedia_processor.process_file(str(file_path))
    
    asset = Asset(
        filename=file.filename,
        file_path=str(file_path),
        content=file_info.get('content', ''),
        user_id=user_id
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    
    return {
        "id": asset.id, 
        "filename": asset.filename, 
        "file_type": file_info.get('file_type', 'unknown'),
        "description": file_info.get('description', ''),
        "message": "File uploaded successfully"
    }

@app.get("/documents") # Renamed from /assets to /documents
async def get_assets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user_id = current_user.id
    assets = db.query(Asset).filter(Asset.user_id == user_id).all()
    return [{"id": asset.id, "filename": asset.filename, "created_at": asset.created_at} for asset in assets]

@app.get("/assets")
async def get_assets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user_id = current_user.id
    assets = db.query(Asset).filter(Asset.user_id == user_id).all()
    return [{"id": asset.id, "filename": asset.filename, "created_at": asset.created_at} for asset in assets]

@app.patch("/assets/{asset_id}/rename")
async def rename_asset(
    asset_id: int,
    request: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user_id = current_user.id
    new_filename = request.get("new_filename")
    
    if not new_filename:
        raise HTTPException(status_code=400, detail="New filename is required")
    
    asset = db.query(Asset).filter(Asset.id == asset_id, Asset.user_id == user_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    old_file_path = Path(asset.file_path)
    new_file_path = old_file_path.parent / new_filename
    
    if new_file_path.exists():
        raise HTTPException(status_code=400, detail="File with new name already exists")
    
    try:
        os.rename(old_file_path, new_file_path)
        asset.filename = new_filename
        asset.file_path = str(new_file_path)
        db.commit()
        db.refresh(asset)
        return {"success": True, "message": "Asset renamed successfully", "new_filename": asset.filename}
    except Exception as e:
        db.rollback()
        print(f"Error renaming asset: {e}")
        raise HTTPException(status_code=500, detail=f"Error renaming asset: {str(e)}")

@app.delete("/assets/{asset_id}")
async def delete_asset(
    asset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user_id = current_user.id
    
    try:
        asset = db.query(Asset).filter(
            Asset.id == asset_id,
            Asset.user_id == user_id
        ).first()
        
        if asset:
            # Delete file from filesystem
            if Path(asset.file_path).exists():
                os.remove(asset.file_path)
            
            # Delete associated sources first
            db.query(Source).filter(Source.asset_id == asset.id).delete()
            db.delete(asset)
            db.commit()
            return {"success": True, "message": "Asset deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Asset not found")
            
    except Exception as e:
        db.rollback()
        print(f"Error deleting asset: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting asset: {str(e)}")

# Quiz endpoints
@app.post("/quizzes/generate", response_model=QuizCreate)
async def generate_quiz(
    quiz_request: QuizGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user_id = current_user.id
    
    if not quiz_request.attached_files:
        raise HTTPException(status_code=400, detail="No files attached to generate quiz from.")

    # Fetch assets based on filenames
    assets = db.query(Asset).filter(
        Asset.filename.in_(quiz_request.attached_files),
        Asset.user_id == user_id
    ).all()

    if not assets:
        raise HTTPException(status_code=404, detail="No relevant assets found for quiz generation.")
    
    # Concatenate content from all attached assets
    combined_content = "\n\n".join([asset.content for asset in assets])
    
    quiz_questions_data = await quiz_gen.generate_quiz(
        combined_content, 
        quiz_request.quiz_type, 
        quiz_request.num_questions, 
        topic=quiz_request.topic, 
        difficulty=quiz_request.difficulty,
        language=quiz_request.language
    )
    
    quiz = Quiz(
        title=f"Quiz on {quiz_request.topic or 'selected files'}",
        quiz_type=quiz_request.quiz_type,
        user_id=user_id,
        asset_id=assets[0].id if assets else None # Link to the first asset for simplicity
    )
    db.add(quiz)
    db.commit()
    db.refresh(quiz)
    
    print(f"DEBUG: quiz_questions_data from quiz_gen: {quiz_questions_data}") # Added debug print
    
    for q_data in quiz_questions_data.get("questions", []): # Iterate over the 'questions' list
        print(f"DEBUG: Processing q_data: {q_data}") # Added debug print
        question = Question(
            quiz_id=quiz.id,
            question_text=q_data["question_text"], # Use 'question_text' from formatted data from quiz_generator
            question_type=q_data["question_type"],      # Use 'question_type' from formatted data from quiz_generator
            options=q_data.get("options"),
            correct_answer=q_data.get("correct_answer") # Use .get for correct_answer as it might be missing for short_answer
        )
        db.add(question)
    db.commit()
    
    # After committing questions, refresh the quiz object to load the newly associated questions
    db.refresh(quiz)
    
    # Now, explicitly load the questions for the response
    loaded_questions = db.query(Question).filter(Question.quiz_id == quiz.id).all()
    print(f"DEBUG: Loaded questions from DB: {loaded_questions}") # Added debug print
    
    return QuizCreate(
        id=quiz.id,
        title=quiz.title,
        quiz_type=quiz.quiz_type,
        questions=[
            {
                "id": q.id,
                "question_text": q.question_text,
                "question_type": q.question_type,
                "options": q.options,
                "correct_answer": q.correct_answer # Include correct_answer in the response
            } for q in loaded_questions # Use loaded_questions here
        ]
    )

@app.get("/quizzes")
async def get_quizzes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    quizzes = db.query(Quiz).filter(Quiz.user_id == current_user.id).all()
    return [{
        "id": quiz.id, 
        "title": quiz.title, 
        "quiz_type": quiz.quiz_type, 
        "created_at": quiz.created_at,
        "asset_filename": quiz.asset.filename if quiz.asset else None
    } for quiz in quizzes]

from src.core.schemas import UserCreate, UserResponse, QuizCreate, QuizSubmit, StudySuggestionResponse, QuizGenerateRequest, QuizResultResponse, QuizQuestionResultSchema # Import QuizResultResponse and QuizQuestionResultSchema

@app.post("/quizzes/submit", response_model=QuizResultResponse)
async def submit_quiz(
    quiz_submit: QuizSubmit,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    print(f"DEBUG: Received quiz submission for quiz_id: {quiz_submit.quiz_id}") # Debug log
    # Eager load quiz and its questions to reduce N+1 queries
    quiz = db.query(Quiz).options(joinedload(Quiz.questions)).filter(
        Quiz.id == quiz_submit.quiz_id, Quiz.user_id == current_user.id
    ).first()
    
    if not quiz:
        print(f"DEBUG: Quiz with ID {quiz_submit.quiz_id} not found for user {current_user.id}") # Debug log
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    score = 0
    total_questions = len(quiz.questions)
    user_answers_data = []
    
    # Create a dictionary for quick lookup of questions by ID
    questions_by_id = {q.id: q for q in quiz.questions}

    for user_ans in quiz_submit.answers:
        question = questions_by_id.get(user_ans.question_id)
        if not question:
            print(f"DEBUG: Question with ID {user_ans.question_id} not found in quiz {quiz.id}") # Debug log
            raise HTTPException(status_code=404, detail=f"Question with ID {user_ans.question_id} not found in this quiz")
        
        is_correct = (user_ans.user_answer.lower() == question.correct_answer.lower())
        if is_correct:
            score += 1
        
        answer_entry = Answer(
            question_id=question.id,
            user_answer=user_ans.user_answer,
            is_correct=is_correct
        )
        user_answers_data.append(answer_entry)
    
    quiz_result = QuizResult(
        quiz_id=quiz.id,
        user_id=current_user.id,
        score=score,
        total_questions=total_questions
    )
    db.add(quiz_result)
    db.commit()
    db.refresh(quiz_result)
    print(f"DEBUG: QuizResult created with ID: {quiz_result.id}") # Debug log
    
    for answer_entry in user_answers_data:
        answer_entry.quiz_result_id = quiz_result.id
        db.add(answer_entry)
    db.commit()
    print(f"DEBUG: Answers saved for QuizResult ID: {quiz_result.id}") # Debug log
    
    # Generate study suggestions
    study_suggestion_text = await quiz_gen.generate_study_suggestions(quiz, quiz_result, user_answers_data)
    study_suggestion = StudySuggestion(
        quiz_result_id=quiz_result.id,
        user_id=current_user.id,
        suggestion_text=study_suggestion_text
    )
    db.add(study_suggestion)
    db.commit()
    db.refresh(study_suggestion)
    print(f"DEBUG: StudySuggestion created for QuizResult ID: {quiz_result.id}") # Debug log
    
    # Eager load quiz result with study suggestions for the response
    full_quiz_result = db.query(QuizResult).options(joinedload(QuizResult.study_suggestions)).filter(QuizResult.id == quiz_result.id).first()
    if not full_quiz_result:
        raise HTTPException(status_code=500, detail="Failed to retrieve full quiz result after submission.")

    # Manually construct the QuizResultResponse
    questions_with_results = []
    for q in quiz.questions:
        user_ans = next((ua for ua in user_answers_data if ua.question_id == q.id), None)
        questions_with_results.append(QuizQuestionResultSchema(
            question_id=q.id,
            question_text=q.question_text,
            question_type=q.question_type,
            options=q.options,
            correct_answer=q.correct_answer,
            user_answer=user_ans.user_answer if user_ans else None,
            is_correct=user_ans.is_correct if user_ans else False,
            explanation=q.explanation # Assuming explanation is part of Question model
        ))

    return QuizResultResponse(
        id=full_quiz_result.id,
        quiz_id=full_quiz_result.quiz_id,
        quiz_title=quiz.title,
        user_id=full_quiz_result.user_id,
        score=full_quiz_result.score,
        total_questions=full_quiz_result.total_questions,
        percentage=round((full_quiz_result.score / full_quiz_result.total_questions) * 100) if full_quiz_result.total_questions > 0 else 0,
        completed_at=full_quiz_result.completed_at,
        asset_filename=quiz.asset.filename if quiz.asset else None,
        questions=questions_with_results,
        study_suggestions=[s.suggestion_text for s in full_quiz_result.study_suggestions] if full_quiz_result.study_suggestions else []
    )

@app.get("/quiz-results/stats")
async def get_quiz_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    total_quizzes = db.query(QuizResult).filter(QuizResult.user_id == current_user.id).count()
    avg_score_query = db.query(func.avg(QuizResult.score * 100 / QuizResult.total_questions)).filter(QuizResult.user_id == current_user.id, QuizResult.total_questions > 0).scalar()
    average_score = round(avg_score_query) if avg_score_query else 0

    # For improvement trend, we'd need more complex logic, e.g., comparing recent scores to older ones.
    # For simplicity, let's just return a placeholder for now.
    improvement_trend = "stable" 

    return {
        "total_quizzes": total_quizzes,
        "average_score": average_score,
        "improvement_trend": improvement_trend
    }

@app.get("/quiz-results/history", response_model=List[QuizResultResponse])
async def get_quiz_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Eager load related data to reduce N+1 queries
    results = db.query(QuizResult).options(
        joinedload(QuizResult.quiz).joinedload(Quiz.asset),
        joinedload(QuizResult.answers), # Corrected relationship name
        joinedload(QuizResult.study_suggestions)
    ).filter(QuizResult.user_id == current_user.id).order_by(QuizResult.completed_at.desc()).all()
    
    response_results = []
    for quiz_result in results:
        quiz = quiz_result.quiz
        asset = quiz.asset if quiz else None
        
        questions_with_answers = []
        if quiz:
            # Create a dictionary for quick lookup of questions by ID from the quiz object
            questions_in_quiz_by_id = {q.id: q for q in quiz.questions}
            
            for answer_obj in quiz_result.answers: # Iterate through answers linked to quiz_result
                q = questions_in_quiz_by_id.get(answer_obj.question_id)
                if q:
                    questions_with_answers.append(QuizQuestionResultSchema(
                        question_id=q.id,
                        question_text=q.question_text,
                        question_type=q.question_type,
                        options=q.options,
                        correct_answer=q.correct_answer,
                        user_answer=answer_obj.user_answer,
                        is_correct=answer_obj.is_correct,
                        explanation=q.explanation # Assuming explanation is part of Question model
                    ))
        
        response_results.append(QuizResultResponse(
            id=quiz_result.id,
            quiz_id=quiz_result.quiz_id,
            quiz_title=quiz.title if quiz else "Untitled Quiz",
            user_id=quiz_result.user_id,
            score=quiz_result.score,
            total_questions=quiz_result.total_questions,
            percentage=round((quiz_result.score / quiz_result.total_questions) * 100) if quiz_result.total_questions > 0 else 0,
            completed_at=quiz_result.completed_at,
            asset_filename=asset.filename if asset else None,
            questions=questions_with_answers,
            study_suggestions=[s.suggestion_text for s in quiz_result.study_suggestions]
        ))
    
    return response_results

@app.get("/quiz-results/{result_id}/suggestions", response_model=StudySuggestionResponse)
async def get_study_suggestions(
    result_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    study_suggestion = db.query(StudySuggestion).filter(
        StudySuggestion.quiz_result_id == result_id,
        StudySuggestion.user_id == current_user.id
    ).first()
    
    if not study_suggestion:
        raise HTTPException(status_code=404, detail="Study suggestions not found for this quiz result")
    
    return StudySuggestionResponse(
        id=study_suggestion.id,
        quiz_result_id=study_suggestion.quiz_result_id,
        suggestion_text=study_suggestion.suggestion_text,
        created_at=study_suggestion.created_at
    )

@app.post("/chats/new")
async def create_new_chat(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user_id = current_user.id
    
    # Determine the next chat_id for the user
    max_chat_id = db.query(func.max(Chat.chat_id)).filter(Chat.user_id == user_id).scalar()
    new_chat_id = (max_chat_id or 0) + 1
    
    new_chat = Chat(
        chat_id=new_chat_id,
        user_id=user_id,
        title="New Chat",
        mode="explanation", # Default mode
        tutor="enola",      # Default tutor
        current_tutor="enola",
        current_mode="explanation",
        messages=[],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(new_chat)
    db.commit()
    db.refresh(new_chat)
    
    return {
        "chat_id": new_chat.chat_id,
        "title": new_chat.title,
        "mode": new_chat.mode,
        "tutor": new_chat.tutor,
        "current_tutor": new_chat.current_tutor,
        "current_mode": new_chat.current_mode,
        "messages": new_chat.messages,
        "attached_asset_ids": [],
        "attached_asset_filenames": [],
        "updated_at": new_chat.updated_at.isoformat()
    }

@app.get("/chats/list")
async def list_chats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user_id = current_user.id
    print(f"DEBUG: Fetching chats for user_id: {user_id}") # Added debug log
    chats = db.query(Chat).filter(Chat.user_id == user_id).order_by(Chat.updated_at.desc()).all()
    print(f"DEBUG: Found {len(chats)} chats for user_id: {user_id}") # Added debug log
    
    return [
        {
            "chat_id": chat.chat_id,
            "title": chat.title,
            "mode": chat.mode,
            "tutor": chat.tutor,
            "current_tutor": chat.current_tutor,
            "current_mode": chat.current_mode,
            "messages": chat.messages,
            "attached_asset_ids": [source.asset_id for source in chat.sources],
            "attached_asset_filenames": [source.asset.filename for source in chat.sources if source.asset],
            "updated_at": chat.updated_at.isoformat()
        }
        for chat in chats
    ]

@app.patch("/chats/{chat_id}/rename")
async def rename_chat(
    chat_id: int,
    request: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user_id = current_user.id
    new_title = request.get("new_title")
    
    if not new_title:
        raise HTTPException(status_code=400, detail="New title is required")
    
    chat = db.query(Chat).filter(Chat.chat_id == chat_id, Chat.user_id == user_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    chat.title = new_title
    chat.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(chat)
    
    return {"success": True, "message": "Chat renamed successfully", "new_title": chat.title}

@app.delete("/chats/{chat_id}")
async def delete_chat(
    chat_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user_id = current_user.id
    
    chat = db.query(Chat).filter(Chat.chat_id == chat_id, Chat.user_id == user_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # Delete associated sources first
    db.query(Source).filter(Source.chat_id == chat.id).delete()
    db.delete(chat)
    db.commit()
    
    return {"success": True, "message": "Chat deleted successfully"}

@app.get("/chats/{chat_id}")
async def get_chat_details(
    chat_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user_id = current_user.id
    chat = db.query(Chat).filter(Chat.chat_id == chat_id, Chat.user_id == user_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    return {
        "chat_id": chat.chat_id,
        "title": chat.title,
        "mode": chat.mode,
        "tutor": chat.tutor,
        "current_tutor": chat.current_tutor,
        "current_mode": chat.current_mode,
        "messages": chat.messages,
        "attached_asset_ids": [source.asset_id for source in chat.sources],
        "attached_asset_filenames": [source.asset.filename for source in chat.sources if source.asset],
        "updated_at": chat.updated_at.isoformat()
    }

@app.post("/chats/save")
async def save_chat(
    request: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user_id = current_user.id
    chat_id = request.get("chat_id")
    title = request.get("title")
    messages = request.get("messages")
    mode = request.get("mode")
    tutor = request.get("tutor")
    attached_asset_filenames = request.get("attached_asset_filenames", []) # Changed to filenames

    if chat_id is None:
        raise HTTPException(status_code=400, detail="Chat ID is required for saving")

    chat = db.query(Chat).filter(Chat.chat_id == chat_id, Chat.user_id == user_id).first()

    if not chat:
        # If chat doesn't exist, create a new one (this might happen if a new chat is saved for the first time)
        chat = Chat(
            chat_id=chat_id,
            user_id=user_id,
            title=title or "New Chat",
            mode=mode or "explanation",
            tutor=tutor or "enola",
            current_tutor=tutor or "enola",
            current_mode=mode or "explanation",
            messages=messages,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(chat)
        db.commit()
        db.refresh(chat)
    else:
        # Update existing chat
        chat.title = title
        chat.messages = messages
        chat.mode = mode
        chat.tutor = tutor
        chat.current_tutor = tutor
        chat.current_mode = mode
        chat.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(chat)

    # Update attached assets
    db.query(Source).filter(Source.chat_id == chat.id).delete()
    db.flush()
    
    # Fetch asset IDs from filenames
    if attached_asset_filenames:
        assets = db.query(Asset).filter(
            Asset.filename.in_(attached_asset_filenames),
            Asset.user_id == user_id # Ensure assets belong to the current user
        ).all()
        
        for asset in assets:
            source_entry = Source(asset_id=asset.id, chat_id=chat.id)
            db.add(source_entry)
    db.commit()

    return {"success": True, "message": "Chat saved successfully", "chat_id": chat.chat_id}

# Helper functions for simple_chat endpoint
def _fetch_user_assets(db: Session, user_id: int, attached_files: list) -> list:
    """Fetches user assets from the database."""
    if attached_files:
        return db.query(Asset).filter(
            Asset.filename.in_(attached_files),
            Asset.user_id == user_id
        ).all()
    else:
        return db.query(Asset).filter(Asset.user_id == user_id).all()

def _get_no_files_response(tutor: str) -> str:
    """Returns a no-files-uploaded response based on the tutor."""
    if tutor == "enola":
        return """Hi! I'm **Enola** 📚 - I will explain the world to you!

I need study materials to provide detailed explanations. Please upload files first!

**Upload files using:**
• The **+** button in Assets panel
• Drag files directly into chat

**I work with:** PDFs, documents, images, audio, video

**I'll explain concepts and enhance them with real-world examples!** 😊"""
    else: # Franklin
        return """Greetings! I'm **Franklin** 📝 - I will test your *ss!

I need study materials to create comprehensive assessments. Please upload files first!

**Upload files using:**
• The **+** button in Assets panel  
• Drag files directly into chat

**I work with:** Course content, textbooks, notes, slides

**I'll create challenging quizzes to test your knowledge thoroughly!** 🎯"""

def _create_source_info(asset: Asset, file_info: dict) -> dict:
    """Creates source information dictionary for a given asset."""
    source_info = {
        "filename": asset.filename,
        "file_type": file_info.get('file_type', 'unknown'),
        "description": file_info.get('description', ''),
        "content_preview": asset.content[:200] + "..." if asset.content else ""
    }
    if file_info.get('timestamps'):
        source_info['timestamps'] = file_info['timestamps']
    return source_info

def _build_file_context(assets: list, multimedia_processor: MultimediaProcessor) -> tuple[str, list]:
    """Builds file context and extracts source information from assets."""
    file_context = "\n\n=== STUDY MATERIALS ===\n"
    sources = []
    max_context_tokens = 60000
    current_tokens = 0
    
    for asset in assets:
        try:
            if not asset or not asset.file_path:
                continue
                
            if hasattr(asset, '_processed_info'):
                file_info = asset._processed_info
            else:
                file_info = multimedia_processor.process_file(asset.file_path)
                if not file_info:
                    continue
                asset._processed_info = file_info
            
            content_tokens = len(asset.content) // 4
            
            if current_tokens + content_tokens > max_context_tokens:
                remaining_tokens = max_context_tokens - current_tokens
                if remaining_tokens > 100:
                    truncated_content = asset.content[:remaining_tokens * 4]
                    file_context += f"\n📄 **{asset.filename}** (truncated)\n"
                    file_context += f"Content: {truncated_content}...\n"
                    current_tokens = max_context_tokens
                break
            else:
                file_context += f"\n📄 **{asset.filename}**\n"
                file_context += f"Content: {asset.content}\n"
                current_tokens += content_tokens
            
            file_context += "---\n"
            
            source_info = _create_source_info(asset, file_info)
            if source_info:
                sources.append(source_info)
                
        except (FileNotFoundError, PermissionError, OSError) as e:
            print(f"File access error for {asset.filename}: {e}")
            continue
        except Exception as e:
            print(f"Unexpected error processing {asset.filename}: {e}")
            continue
    return file_context, sources

def _get_system_prompt(tutor: str, mode: str, language: str, find_what_i_need: bool = False) -> str:
    """Generates the system prompt based on tutor, mode, and language."""
    language_instruction = ""
    if language == "de":
        language_instruction = "\n\n**IMPORTANT: Respond in German (Deutsch). Use German language for all explanations and examples.**"
    elif language == "sk":
        language_instruction = "\n\n**IMPORTANT: Respond in Slovak (Slovenčina). Use Slovak language for all explanations and examples.**"
    elif language == "en":
        language_instruction = "\n\n**IMPORTANT: Respond in English.**"
    
    if tutor == "enola" and mode == "explanation":
        if find_what_i_need:
            return f"""You are Enola, a friendly and enthusiastic AI tutor who specializes in finding specific information within provided documents.{language_instruction}

**Your role:**
• Directly address the user's request to "find what I need"
• Search through the attached files for the specific information requested in the user's message.
• Clearly outline where the information was found (e.g., "In file 'document.pdf', on page 3, it states...")
• Provide the relevant information concisely.
• If the information is not found, state that clearly.
• Be helpful and precise.

**CRITICAL FORMATTING REQUIREMENTS (Format like Amazon Q):**
• Start with a clear ## heading for the main topic
• Use **bold** for important terms and key concepts
• Use bullet points (•) for lists with proper spacing
• Add emojis occasionally to make content engaging (📚 🎯 💡 ✨)
• Use short paragraphs (2-3 sentences) with blank lines between them
• Use ### subheadings to break content into sections
• Add line breaks generously - never create walls of text
• Use numbered lists for sequential steps
• Use > blockquotes for important notes or tips
• Structure: Heading → Brief intro → Sections with subheadings → Lists → Examples

**Example format:**
## Information Found on [Topic]

I found the following information regarding [topic] in your attached files:

### From [Filename 1]
• On page [X], it states: "[Relevant quote/summary]"
• [Another point]

### From [Filename 2]
• [Relevant information]

Would you like me to elaborate on any of these points or search for something else? 😊"""
        else:
            return f"""You are Enola, a friendly and enthusiastic AI tutor who specializes in explanations.{language_instruction}

**Your role:**
• START with concepts from the uploaded files as your foundation
• EXPAND and enhance these concepts with additional knowledge and context
• Provide deeper explanations, real-world examples, and practical applications
• Connect file concepts to broader knowledge and current developments
• Use analogies, examples, and clear explanations to aid understanding
• Be warm, encouraging, and make learning enjoyable 😊
• Always reference which parts come from the files vs. your additional insights

**SPECIAL HANDLING FOR TRANSCRIPTION REQUESTS:**
When user asks to "transcribe" or wants "full transcript" or "complete transcription":
• Provide ALL available content from the file, not just summaries
• For videos: Include ALL extracted text, frame descriptions, and OCR content
• For audio: Include ALL transcribed text
• Add timestamps if available in the content (format: [00:00] or 0:00)
• If timestamps aren't in the source, organize content chronologically
• Use clear section breaks for different parts
• DO NOT summarize - provide the COMPLETE content

**CRITICAL FORMATTING REQUIREMENTS (Format like Amazon Q):**
• Start with a clear ## heading for the main topic
• Use **bold** for important terms and key concepts
• Use bullet points (•) for lists with proper spacing
• Add emojis occasionally to make content engaging (📚 🎯 💡 ✨)
• Use short paragraphs (2-3 sentences) with blank lines between them
• Use ### subheadings to break content into sections
• Add line breaks generously - never create walls of text
• Use numbered lists for sequential steps
• Use > blockquotes for important notes or tips
• Structure: Heading → Brief intro → Sections with subheadings → Lists → Examples

**Example format:**
## Understanding [Concept]

Based on your file, [concept] is... Let me explain this clearly.

### Key Points
• **First point**: Explanation here
• **Second point**: More details

### Real-World Application
In practice, this means... 💡

> **Important**: Remember that...

Would you like me to explain any part in more detail? 😊"""
    elif tutor == "franklin" and mode == "testing":
        return f"""You are Franklin, a methodical AI testing tutor who creates structured quizzes and assessments.{language_instruction}

**ABSOLUTE RULE: NEVER create test questions immediately! ALWAYS ask clarifying questions FIRST!**

**FORBIDDEN BEHAVIOR:**
- DO NOT answer test questions yourself
- DO NOT create quizzes without asking for preferences first
- DO NOT provide direct answers to questions in files
- DO NOT list questions without user's format preference

**REQUIRED BEHAVIOR:**

### When user says "test me on [topic]" or "test me on [topic] from [file]":
You MUST respond with:

## Test Preparation 📝

I'll create a test on **[topic]** from your materials. First, let me clarify your preferences:

**1. Which test format would you prefer?**
• Multiple choice questions
• True/False statements  
• Short answer questions
• Mixed format (combination of all)

**2. How many questions?** (I recommend 5-10)

**3. Difficulty level?**
• Easy (basic concepts)
• Medium (application)
• Hard (analysis and synthesis)

Please let me know your preferences, and I'll create the perfect test for you! 🎯

### When user says just "test me":
You MUST respond with:

## Test Preparation 📝

I'm ready to create a test for you! First, I need some information:

**1. Which topic would you like to be tested on?**
• [List 3-4 main topics from uploaded files]
• Or specify your own topic

**2. What test format do you prefer?**
• Multiple choice
• True/False
• Short answer
• Mixed format

**3. How many questions?** (5-10 recommended)

**4. Difficulty level?**
• Easy • Medium • Hard

Please provide these details so I can create the perfect test for you! 📚

### ONLY create actual quiz AFTER user provides ALL preferences:

📝 **Quiz: [Topic]**

**Question 1:** [Question]
**A)** [Option]
**B)** [Option]
**C)** [Option]
**D)** [Option]

[Continue with remaining questions based on user's chosen format]

**REMEMBER:**
- NEVER answer questions directly
- ALWAYS ask for preferences first
- ONLY create quiz after user confirms format, count, and difficulty
- Use ## headings, **bold**, emojis (📝 🎯 ✨), and proper spacing"""
    else: # Fallback or unexpected combination
        return f"""You are an AI tutor. Respond to the user's message based on the provided study materials.
        Your current mode is '{mode}' and your current tutor is '{tutor}'.{language_instruction}
        
        **Your role:**
        • Provide helpful and informative responses.
        • If in 'explanation' mode, explain concepts clearly.
        • If in 'testing' mode, guide the user towards quiz generation.
        • Always reference which parts come from the files vs. your additional insights.
        
        **CRITICAL FORMATTING REQUIREMENTS (Format like Amazon Q):**
        • Start with a clear ## heading for the main topic
        • Use **bold** for important terms and key concepts
        • Use bullet points (•) for lists with proper spacing
        • Add emojis occasionally to make content engaging (📚 🎯 💡 ✨)
        • Use short paragraphs (2-3 sentences) with blank lines between them
        • Use ### subheadings to break content into sections
        • Add line breaks generously - never create walls of text
        • Use numbered lists for sequential steps
        • Use > blockquotes for important notes or tips
        • Structure: Heading → Brief intro → Sections with subheadings → Lists → Examples

**Example format:**
## Understanding [Concept]

Based on your file, [concept] is... Let me explain this clearly.

### Key Points
• **First point**: Explanation here
• **Second point**: More details

### Real-World Application
In practice, this means... 💡

> **Important**: Remember that...

Would you like me to explain any part in more detail? 😊"""

def _generate_chat_title(message: str, attached_files: list, user_assets: list) -> str:
    """Generates a chat title based on the message and attached files."""
    if attached_files:
        filenames = [Path(f).stem for f in attached_files]
        return f"Chat about {', '.join(filenames[:2])}"
    elif user_assets:
        filenames = [Path(asset.filename).stem for asset in user_assets]
        return f"Chat about {', '.join(filenames[:2])}"
    else:
        return message[:50] + "..." if len(message) > 50 else message

def format_ai_response(response: str, tutor: str) -> str:
    """Formats the AI response based on the tutor."""
    if tutor == "enola":
        # Enola's formatting is handled by the system prompt directly
        return response
    elif tutor == "franklin":
        # Franklin's formatting is also handled by the system prompt directly
        return response
    return response

# Simple chat endpoint (supports both authenticated and guest users)
@app.post("/simple-chat")
async def simple_chat(
    request: dict, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user_id = current_user.id
    message = request.get("message", "")
    mode = request.get("mode", "explanation")
    tutor = request.get("tutor", "enola")
    chat_id = request.get("chat_id", 1)
    attached_files = request.get("attached_files", []) # Now expects filenames
    language = request.get("language", "en")
    find_what_i_need = request.get("find_what_i_need", False) # New parameter
    
    if not message:
        raise HTTPException(status_code=400, detail="Message is required")
    
    user_assets = _fetch_user_assets(db, user_id, attached_files)
    
    if not user_assets:
        no_files_response = _get_no_files_response(tutor)
        return {"response": no_files_response, "sources": [], "requires_files": True}
    
    file_context, sources = _build_file_context(user_assets, multimedia_processor)
    
    system_prompt = _get_system_prompt(tutor, mode, language, find_what_i_need)
    context_instruction = f"\n\n**TASK:** Answer '{message}' using the provided materials. Be comprehensive but concise."
    
    base_prompt = f"{system_prompt}\n{file_context}{context_instruction}\n\nQ: {message}\nA:"
    
    if len(base_prompt) > 60000:
        truncated_context = file_context[:50000] + "\n[Content truncated for processing]\n"
        base_prompt = f"{system_prompt}\n{truncated_context}{context_instruction}\n\nQ: {message}\nA:"
    
    print(f"DEBUG: Calling llm_service.generate_response from simple_chat. LLMService instance: {id(llm_service)}, initialized: {llm_service.initialized}, model_name: {llm_service.full_model_name}")
    try:
        response = await llm_service.generate_response(base_prompt)
    except Exception as e:
        print(f"Error generating LLM response: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating AI response: {str(e)}")
    
    response = format_ai_response(response, tutor)
    
    # Save chat message and sources to database
    chat = db.query(Chat).filter(Chat.chat_id == chat_id, Chat.user_id == user_id).first()
    if not chat:
        chat = Chat(chat_id=chat_id, user_id=user_id, title="New Chat", mode=mode, tutor=tutor, messages=[], current_tutor=tutor, current_mode=mode)
        db.add(chat)
        db.commit()
        db.refresh(chat)
    else:
        # Update chat's current_tutor and current_mode
        chat.current_tutor = tutor
        chat.current_mode = mode

    # Append new messages to the existing list
    chat.messages.append({"role": "user", "content": message, "timestamp": datetime.utcnow().isoformat()})
    chat.messages.append({"role": "assistant", "content": response, "timestamp": datetime.utcnow().isoformat()})
    chat.updated_at = datetime.utcnow()
    
    # Link sources to chat
    # First, clear existing sources for this chat to avoid duplicates
    db.query(Source).filter(Source.chat_id == chat.id).delete()
    db.flush() # Ensure delete is processed before adding new ones
    
    for asset in user_assets:
        source_entry = Source(asset_id=asset.id, chat_id=chat.id)
        db.add(source_entry)
    db.commit()

    chat_title = _generate_chat_title(message, attached_files, user_assets)
    
    return {
        "response": response,
        "sources": sources,
        "suggested_title": chat_title,
        "mode": mode,
        "tutor": tutor,
        "requires_files": False
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
