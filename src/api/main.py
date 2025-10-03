from fastapi import FastAPI, File, UploadFile, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
import uvicorn
import os
from pathlib import Path

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.core.database import get_db, init_db
from src.core.models import User, Document, Quiz, Chat
from src.core.schemas import UserCreate, UserResponse, QuizCreate, ChatMessage
from src.core.auth import get_current_user, create_access_token, verify_password, get_password_hash
from src.services.llm_service import LLMService
from src.processors.multimedia_processor import MultimediaProcessor
from src.services.quiz_generator import QuizGenerator

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    await llm_service.initialize()
    yield
    # Shutdown (if needed)

app = FastAPI(title="AI Tutor Platform", version="1.0.0", lifespan=lifespan)

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
multimedia_processor = MultimediaProcessor()
quiz_gen = QuizGenerator(llm_service)

# Get the project root directory (two levels up from main.py)
BASE_DIR = Path(__file__).parent.parent.parent

# Create directories with absolute paths
os.makedirs(BASE_DIR / "uploads", exist_ok=True)
os.makedirs(BASE_DIR / "static", exist_ok=True)

# Mount static files with absolute path
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

@app.get("/", response_class=HTMLResponse)
async def root():
    # Serve the main app interface
    app_html_path = BASE_DIR / "static" / "app.html"
    with open(app_html_path, "r") as f:
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
async def login(email: str, password: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer", "user": {"id": user.id, "email": user.email, "username": user.username}}

# Document endpoints
@app.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # Accept various file types
    allowed_extensions = ['.pdf', '.docx', '.txt', '.md', '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.mp3', '.wav', '.m4a', '.ogg', '.mp4', '.avi', '.mov', '.mkv', '.webm']
    file_extension = Path(file.filename).suffix.lower()
    
    if file_extension not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"File type {file_extension} not supported")
    
    # Check if file already exists to avoid duplicates
    existing_doc = db.query(Document).filter(Document.filename == file.filename, Document.user_id == 1).first()
    if existing_doc:
        return {
            "id": existing_doc.id, 
            "filename": existing_doc.filename, 
            "file_type": "existing",
            "description": "File already exists",
            "message": "File already uploaded"
        }
    
    # Save file with absolute path
    file_path = BASE_DIR / "uploads" / file.filename
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    # Process multimedia file
    file_info = multimedia_processor.process_file(str(file_path))
    
    # Save to database (using user_id=1 for demo)
    document = Document(
        filename=file.filename,
        file_path=str(file_path),
        content=file_info.get('content', ''),
        user_id=1  # Demo user ID
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    
    return {
        "id": document.id, 
        "filename": document.filename, 
        "file_type": file_info.get('file_type', 'unknown'),
        "description": file_info.get('description', ''),
        "message": "File uploaded successfully"
    }

@app.get("/documents")
async def get_documents(db: Session = Depends(get_db)):
    documents = db.query(Document).filter(Document.user_id == 1).all()  # Demo user
    return [{"id": doc.id, "filename": doc.filename, "created_at": doc.created_at} for doc in documents]

# Quiz endpoints
@app.post("/quizzes/generate")
async def generate_quiz(
    document_id: int,
    quiz_type: str = "multiple_choice",
    num_questions: int = 5,
    db: Session = Depends(get_db)
):
    document = db.query(Document).filter(Document.id == document_id, Document.user_id == 1).first()  # Demo user
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    questions = await quiz_gen.generate_quiz(document.content, quiz_type, num_questions)
    
    quiz = Quiz(
        title=f"Quiz for {document.filename}",
        questions=questions,
        quiz_type=quiz_type,
        document_id=document_id,
        user_id=1  # Demo user
    )
    db.add(quiz)
    db.commit()
    db.refresh(quiz)
    
    return {"id": quiz.id, "title": quiz.title, "questions": questions}

@app.get("/quizzes")
async def get_quizzes(db: Session = Depends(get_db)):
    quizzes = db.query(Quiz).filter(Quiz.user_id == 1).all()  # Demo user
    return [{"id": quiz.id, "title": quiz.title, "quiz_type": quiz.quiz_type, "created_at": quiz.created_at} for quiz in quizzes]

# Simple chat endpoint (no auth required)
@app.post("/simple-chat")
async def simple_chat(request: dict, db: Session = Depends(get_db)):
    message = request.get("message", "")
    mode = request.get("mode", "explanation")
    tutor = request.get("tutor", "enola")
    chat_id = request.get("chat_id", 1)
    attached_files = request.get("attached_files", [])
    
    if not message:
        raise HTTPException(status_code=400, detail="Message is required")
    
    # Get only files mentioned in this conversation or attached
    relevant_files = []
    sources = []
    
    if attached_files:
        for filename in attached_files:
            doc = db.query(Document).filter(Document.filename == filename, Document.user_id == 1).first()
            if doc:
                relevant_files.append(doc)
    
    # Build context only from relevant files
    file_context = ""
    if relevant_files:
        file_context = "\n\nRelevant files for this conversation:\n"
        for doc in relevant_files:
            try:
                file_info = multimedia_processor.process_file(doc.file_path)
                summary = multimedia_processor.get_content_summary(file_info)
                file_context += f"\n{summary}\n"
                
                # Add to sources for response
                sources.append({
                    "title": doc.filename,
                    "excerpt": file_info.get('description', 'No description available')
                })
            except Exception as e:
                print(f"Error processing file {doc.filename}: {e}")
    
    # Specialized tutor prompts based on mode
    if tutor == "enola" and mode == "explanation":
        tutor_context = "You are Enola, a friendly and enthusiastic tutor who specializes in explaining concepts. Format your responses with clear structure using markdown-like formatting. Use bullet points, numbered lists, and emphasis to make content easy to understand. Be encouraging and conversational. "
    elif tutor == "franklin" and mode == "testing":
        tutor_context = "You are Franklin, a wise and methodical tutor who specializes in testing knowledge. Create quizzes, ask probing questions, and provide structured assessments. Format your responses clearly with numbered questions and organized content. Be thorough and systematic. "
    elif tutor == "enola" and mode == "testing":
        tutor_context = "You are Enola, but the student wants testing. Suggest they switch to Franklin for better testing experience, but still help with basic questions if needed. "
    else:  # franklin + explanation
        tutor_context = "You are Franklin, but the student wants explanations. Suggest they switch to Enola for better explanatory experience, but still provide structured explanations if needed. "
    
    # Generate response using LLM service
    full_message = tutor_context + file_context + "\n\nStudent question: " + message
    response = await llm_service.generate_response(full_message)
    
    # Generate chat title suggestion if this looks like a new topic
    chat_title = None
    if len(message.split()) > 2 and any(word in message.lower() for word in ['about', 'explain', 'what', 'how', 'tell']):
        if attached_files:
            chat_title = f"Discussion: {attached_files[0]}"
        else:
            # Extract key topic from message
            words = message.split()[:4]
            chat_title = f"Chat: {' '.join(words)}..."
    
    return {
        "response": response,
        "sources": sources if sources else None,
        "suggested_title": chat_title
    }

# Chat endpoints
@app.post("/chat")
async def chat(
    message: ChatMessage,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Get context from user's documents if needed
    context = ""
    if message.document_id:
        document = db.query(Document).filter(Document.id == message.document_id, Document.user_id == current_user.id).first()
        if document:
            context = document.content[:2000]  # Limit context size
    
    # Generate response
    response = await llm_service.generate_response(message.content, context)
    
    # Save chat history
    chat_entry = Chat(
        message=message.content,
        response=response,
        user_id=current_user.id,
        document_id=message.document_id
    )
    db.add(chat_entry)
    db.commit()
    
    return {"response": response}

@app.get("/chat/history")
async def get_chat_history(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    chats = db.query(Chat).filter(Chat.user_id == current_user.id).order_by(Chat.created_at.desc()).limit(50).all()
    return [{"message": chat.message, "response": chat.response, "created_at": chat.created_at} for chat in chats]

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)