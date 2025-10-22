from fastapi import FastAPI, File, UploadFile, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
from typing import Optional
import uvicorn
import os
from pathlib import Path

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.core.database import get_db, init_db
from src.core.models import User, Document, Quiz, Chat, QuizResult
from src.core.schemas import UserCreate, UserResponse, QuizCreate, ChatMessage
from datetime import datetime
from src.core.auth import get_current_user, create_access_token, verify_password, get_password_hash, verify_google_token, create_or_get_google_user, get_current_user_optional
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
@app.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    # Use current user ID or default to 1 for guest
    user_id = current_user.id if current_user else 1
    # Accept various file types
    allowed_extensions = ['.pdf', '.docx', '.txt', '.md', '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.mp3', '.wav', '.m4a', '.ogg', '.mp4', '.avi', '.mov', '.mkv', '.webm']
    file_extension = Path(file.filename).suffix.lower()
    
    if file_extension not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"File type {file_extension} not supported")
    
    # Check if file already exists to avoid duplicates
    existing_doc = db.query(Document).filter(Document.filename == file.filename, Document.user_id == user_id).first()
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
    
    # Save to database
    document = Document(
        filename=file.filename,
        file_path=str(file_path),
        content=file_info.get('content', ''),
        user_id=user_id
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
async def get_documents(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    user_id = current_user.id if current_user else 1
    documents = db.query(Document).filter(Document.user_id == user_id).all()
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

# Simple chat endpoint (supports both authenticated and guest users)
@app.post("/simple-chat")
async def simple_chat(
    request: dict, 
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    # Use current user ID or default to 1 for guest
    user_id = current_user.id if current_user else 1
    message = request.get("message", "")
    mode = request.get("mode", "explanation")
    tutor = request.get("tutor", "enola")
    chat_id = request.get("chat_id", 1)
    attached_files = request.get("attached_files", [])
    language = request.get("language", "en")
    
    if not message:
        raise HTTPException(status_code=400, detail="Message is required")
    
    # ENFORCE STRICT TUTOR-MODE PAIRING
    if tutor == "enola":
        mode = "explanation"  # Enola ONLY does explanations
    elif tutor == "franklin":
        mode = "testing"  # Franklin ONLY does testing
    
    # Optimize database queries - get documents in single query with caching
    try:
        if attached_files:
            # Get only attached files if specified
            user_documents = db.query(Document).filter(
                Document.filename.in_(attached_files),
                Document.user_id == user_id
            ).all()
        else:
            # Get all user documents
            user_documents = db.query(Document).filter(Document.user_id == user_id).all()
    except Exception as e:
        print(f"Database query error: {e}")
        user_documents = []
    
    # Check if user has files or if message sent without files
    if not user_documents and not attached_files:
        if tutor == "enola":
            no_files_response = """Hi! I'm **Enola** 📚 - I will explain the world to you!

I need study materials to provide detailed explanations. Please upload files first!

**Upload files using:**
• The **+** button in Assets panel
• Drag files directly into chat

**I work with:** PDFs, documents, images, audio, video

**I'll explain concepts and enhance them with real-world examples!** 😊"""
        else:  # Franklin
            no_files_response = """Greetings! I'm **Franklin** 📝 - I will test your *ss!

I need study materials to create comprehensive assessments. Please upload files first!

**Upload files using:**
• The **+** button in Assets panel  
• Drag files directly into chat

**I work with:** Course content, textbooks, notes, slides

**I'll create challenging quizzes to test your knowledge thoroughly!** 🎯"""
        
        return {"response": no_files_response, "sources": [], "requires_files": True}
    
    # Require files for explanation mode
    if tutor == "enola" and not attached_files and not user_documents:
        return {
            "response": "Please upload or attach files before asking for explanations! I need study materials to work with. 📚",
            "sources": [],
            "requires_files": True
        }
    
    # Use optimized document list
    relevant_docs = user_documents
    file_context = "\n\n=== STUDY MATERIALS ===\n"
    sources = []
    
    # Calculate token budget for 16K context window
    max_context_tokens = 60000  # 16K tokens = ~60K characters
    current_tokens = 0
    
    # Add relevant files for context with token management
    for doc in relevant_docs:
        try:
            # Validate document exists
            if not doc or not doc.file_path:
                continue
                
            # Process file only once and cache result
            if hasattr(doc, '_processed_info'):
                file_info = doc._processed_info
            else:
                file_info = multimedia_processor.process_file(doc.file_path)
                if not file_info:
                    continue
                doc._processed_info = file_info
            
            # Estimate tokens (rough: 1 token ≈ 4 characters)
            content_tokens = len(doc.content) // 4
            
            # Truncate content if too large
            if current_tokens + content_tokens > max_context_tokens:
                remaining_tokens = max_context_tokens - current_tokens
                if remaining_tokens > 100:  # Only add if meaningful content fits
                    truncated_content = doc.content[:remaining_tokens * 4]
                    file_context += f"\n📄 **{doc.filename}** (truncated)\n"
                    file_context += f"Content: {truncated_content}...\n"
                    current_tokens = max_context_tokens
                break
            else:
                file_context += f"\n📄 **{doc.filename}**\n"
                file_context += f"Content: {doc.content}\n"
                current_tokens += content_tokens
            
            file_context += "---\n"
            
            # Create source info
            source_info = _create_source_info(doc, file_info)
            if source_info:
                sources.append(source_info)
                
        except (FileNotFoundError, PermissionError, OSError) as e:
            print(f"File access error for {doc.filename}: {e}")
            continue
        except Exception as e:
            print(f"Unexpected error processing {doc.filename}: {e}")
            continue
    
    # Language instruction
    language_instruction = ""
    if language == "de":
        language_instruction = "\n\n**IMPORTANT: Respond in German (Deutsch). Use German language for all explanations and examples.**"
    elif language == "sk":
        language_instruction = "\n\n**IMPORTANT: Respond in Slovak (Slovenčina). Use Slovak language for all explanations and examples.**"
    elif language == "en":
        language_instruction = "\n\n**IMPORTANT: Respond in English.**"
    
    # Create specialized prompts
    if tutor == "enola":
        system_prompt = f"""You are Enola, a friendly and enthusiastic AI tutor who specializes in explanations.{language_instruction}

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
    else:  # Franklin
        system_prompt = f"""You are Franklin, a methodical AI testing tutor who creates structured quizzes and assessments.{language_instruction}

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
    
    # Generate response with token-aware context
    context_instruction = f"\n\n**TASK:** Answer '{message}' using the provided materials. Be comprehensive but concise."
    
    # Build prompt with token awareness
    base_prompt = f"{system_prompt}\n{file_context}{context_instruction}\n\nQ: {message}\nA:"
    
    # Ensure prompt fits in 16K context window
    if len(base_prompt) > 60000:  # 16K token limit
        # Truncate file context if needed
        truncated_context = file_context[:50000] + "\n[Content truncated for processing]\n"
        base_prompt = f"{system_prompt}\n{truncated_context}{context_instruction}\n\nQ: {message}\nA:"
    
    response = await llm_service.generate_response(base_prompt)
    
    # Format response for better readability
    response = format_ai_response(response, tutor)
    
    # Add conversation memory
    response = add_conversation_memory(response, message, user_id, chat_id)
    
    # Generate chat title suggestion based on content
    chat_title = None
    if len(message.split()) > 2 or attached_files:
        if attached_files:
            # Content-based naming for file chats
            file_name = attached_files[0]
            file_ext = file_name.split('.')[-1].lower() if '.' in file_name else ''
            base_name = file_name.split('.')[0][:15]
            
            # Extract key action from message
            if any(word in message.lower() for word in ['text', 'outline', 'read', 'extract', 'transcribe']):
                chat_title = f"{base_name} - Text Analysis"
            elif any(word in message.lower() for word in ['quiz', 'test', 'question', 'assess']):
                chat_title = f"{base_name} - Quiz"
            elif any(word in message.lower() for word in ['explain', 'understand', 'concept', 'learn']):
                chat_title = f"{base_name} - Explanation"
            elif any(word in message.lower() for word in ['analyze', 'describe', 'what', 'examine']):
                chat_title = f"{base_name} - Analysis"
            elif any(word in message.lower() for word in ['summary', 'summarize', 'overview']):
                chat_title = f"{base_name} - Summary"
            else:
                # Use first meaningful words from message
                words = [w for w in message.split()[:3] if len(w) > 2]
                if words:
                    chat_title = f"{base_name} - {' '.join(words).title()}"
                else:
                    chat_title = f"{base_name} - Discussion"
        else:
            # Message-based naming without files
            words = [w for w in message.split()[:4] if len(w) > 2]
            if words:
                chat_title = ' '.join(words).title()
                if len(chat_title) > 25:
                    chat_title = chat_title[:25] + "..."
            else:
                chat_title = "General Discussion"
    
    return {
        "response": response,
        "sources": sources,
        "suggested_title": chat_title,
        "mode": mode,
        "tutor": tutor,
        "requires_files": False
    }

def _create_source_info(doc, file_info) -> dict:
    """Create source information for a document"""
    try:
        word_count = len(doc.content.split()) if doc.content else 0
        file_type = file_info.get('file_type', 'document')
        
        # Extract key concepts efficiently
        key_concepts = _extract_key_concepts(doc.content)
        key_info = " • ".join(key_concepts) if key_concepts else doc.content[:100].replace('\n', ' ') if doc.content else "No content"
        
        return {
            "title": doc.filename,
            "excerpt": f"{file_type.title()} • {word_count} words\nKey topics: {key_info}...",
            "type": file_type,
            "word_count": word_count,
            "key_concepts": key_concepts
        }
    except Exception as e:
        print(f"Error creating source info: {e}")
        return None

def _extract_key_concepts(content: str, max_concepts: int = 3) -> list:
    """Extract key concepts from content efficiently"""
    try:
        if not content:
            return []
            
        lines = content.split('\n')[:15]
        key_concepts = []
        
        for line in lines:
            line = line.strip()
            if not line or len(key_concepts) >= max_concepts:
                continue
                
            if _is_heading_or_bullet(line):
                concept = _clean_concept(line)
                if concept and len(concept) > 3:
                    key_concepts.append(concept)
        
        return key_concepts
    except Exception as e:
        print(f"Error extracting key concepts: {e}")
        return []

def _is_heading_or_bullet(line: str) -> bool:
    """Check if line is a heading or bullet point"""
    try:
        return (line.startswith(('#', '-', '*', '•')) or 
                (line and line[0].isdigit() and '.' in line[:5]))
    except Exception:
        return False

def _clean_concept(line: str) -> str:
    """Clean and format concept text"""
    try:
        return line.lstrip('#-*•0123456789. ').strip()[:50]
    except Exception:
        return ""

def format_ai_response(response: str, tutor: str) -> str:
    """Format AI response with Amazon Q-style formatting"""
    try:
        lines = response.split('\n')
        formatted_lines = []
        in_code_block = False
        prev_was_heading = False
        prev_was_list = False
        
        for i, line in enumerate(lines):
            original_line = line
            line = line.strip()
            
            # Preserve empty lines for spacing
            if not line:
                formatted_lines.append('')
                prev_was_list = False
                continue
            
            # Handle code blocks
            if line.startswith('```'):
                in_code_block = not in_code_block
                if not in_code_block:
                    formatted_lines.append(original_line)
                    formatted_lines.append('')  # Add spacing after code block
                else:
                    formatted_lines.append(original_line)
                continue
            
            if in_code_block:
                formatted_lines.append(original_line)
                continue
            
            # Format headings with spacing
            if line.startswith('###'):
                if formatted_lines and formatted_lines[-1] != '':
                    formatted_lines.append('')  # Add space before subheading
                formatted_lines.append(f"### {line.lstrip('# ')}")
                formatted_lines.append('')  # Add space after heading
                prev_was_heading = True
                prev_was_list = False
            elif line.startswith('##'):
                if formatted_lines and formatted_lines[-1] != '':
                    formatted_lines.append('')  # Add space before heading
                formatted_lines.append(f"## {line.lstrip('# ')}")
                formatted_lines.append('')  # Add space after heading
                prev_was_heading = True
                prev_was_list = False
            elif line.startswith('#'):
                if formatted_lines and formatted_lines[-1] != '':
                    formatted_lines.append('')
                formatted_lines.append(f"## {line.lstrip('# ')}")
                formatted_lines.append('')
                prev_was_heading = True
                prev_was_list = False
            # Format bullet points with proper spacing
            elif line.startswith(('-', '*', '•')):
                if not prev_was_list and formatted_lines and formatted_lines[-1] != '':
                    formatted_lines.append('')  # Add space before list starts
                formatted_lines.append(f"• {line.lstrip('-*• ')}")
                prev_was_list = True
                prev_was_heading = False
            # Format numbered lists
            elif line[0].isdigit() and '. ' in line[:5]:
                if not prev_was_list and formatted_lines and formatted_lines[-1] != '':
                    formatted_lines.append('')
                formatted_lines.append(line)
                prev_was_list = True
                prev_was_heading = False
            # Format blockquotes with spacing
            elif line.startswith('>'):
                if formatted_lines and formatted_lines[-1] != '':
                    formatted_lines.append('')
                formatted_lines.append(line)
                formatted_lines.append('')
                prev_was_list = False
                prev_was_heading = False
            # Format tables
            elif '|' in line and line.count('|') >= 2:
                formatted_lines.append(line)
                prev_was_list = False
                prev_was_heading = False
            else:
                # Regular paragraph
                if prev_was_list and formatted_lines and formatted_lines[-1] != '':
                    formatted_lines.append('')  # Add space after list
                
                # Break long paragraphs
                if len(line) > 200:
                    sentences = line.split('. ')
                    current_para = ''
                    for sentence in sentences:
                        if len(current_para + sentence) > 150:
                            if current_para:
                                formatted_lines.append(current_para.strip() + '.')
                                formatted_lines.append('')  # Add spacing between paragraphs
                            current_para = sentence
                        else:
                            current_para += sentence + '. '
                    if current_para:
                        formatted_lines.append(current_para.strip())
                else:
                    formatted_lines.append(line)
                
                prev_was_list = False
                prev_was_heading = False
        
        return '\n'.join(formatted_lines)
        
    except Exception as e:
        print(f"Response formatting error: {e}")
        return response

def add_conversation_memory(response: str, message: str, user_id: int, chat_id: int) -> str:
    """Add conversation memory context"""
    try:
        # Simple memory implementation - store last few exchanges
        memory_key = f"memory_{user_id}_{chat_id}"
        
        # This would be stored in database in production
        # For now, just add context about the current conversation
        if "previous" in message.lower() or "earlier" in message.lower() or "before" in message.lower():
            memory_note = "\n\n*Note: I can reference our previous discussion in this chat session.*"
            response += memory_note
        
        return response
    except Exception as e:
        print(f"Memory error: {e}")
        return response

# Chat persistence endpoints
@app.post("/chats/save")
async def save_chat(
    request: dict,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    user_id = current_user.id if current_user else 1
    chat_id = request.get("chat_id")
    title = request.get("title", "New Chat")
    mode = request.get("mode", "explanation")
    tutor = request.get("tutor", "enola")
    messages = request.get("messages", [])
    files_used = request.get("files_used", [])
    
    try:
        # Check if chat exists
        existing_chat = db.query(Chat).filter(
            Chat.chat_id == chat_id,
            Chat.user_id == user_id
        ).first()
        
        if existing_chat:
            # Update existing chat
            existing_chat.title = title
            existing_chat.mode = mode
            existing_chat.tutor = tutor
            existing_chat.messages = messages
            existing_chat.files_used = files_used
            existing_chat.updated_at = datetime.utcnow()
        else:
            # Create new chat
            new_chat = Chat(
                chat_id=chat_id,
                title=title,
                mode=mode,
                tutor=tutor,
                messages=messages,
                files_used=files_used,
                user_id=user_id
            )
            db.add(new_chat)
        
        db.commit()
        return {"success": True, "message": "Chat saved successfully"}
        
    except Exception as e:
        db.rollback()
        print(f"Error saving chat: {e}")
        return {"success": False, "message": f"Error saving chat: {str(e)}"}

@app.get("/chats/list")
async def list_chats(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    user_id = current_user.id if current_user else 1
    
    try:
        chats = db.query(Chat).filter(Chat.user_id == user_id).order_by(Chat.updated_at.desc()).all()
        return {
            "chats": [{
                "chat_id": chat.chat_id,
                "title": chat.title,
                "mode": chat.mode,
                "tutor": chat.tutor,
                "messages": chat.messages,
                "files_used": chat.files_used,
                "updated_at": chat.updated_at.isoformat()
            } for chat in chats]
        }
    except Exception as e:
        print(f"Error loading chats: {e}")
        return {"chats": []}

@app.delete("/chats/{chat_id}")
async def delete_chat(
    chat_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    user_id = current_user.id if current_user else 1
    
    try:
        chat = db.query(Chat).filter(
            Chat.chat_id == chat_id,
            Chat.user_id == user_id
        ).first()
        
        if chat:
            db.delete(chat)
            db.commit()
            return {"success": True, "message": "Chat deleted successfully"}
        else:
            return {"success": False, "message": "Chat not found"}
            
    except Exception as e:
        db.rollback()
        print(f"Error deleting chat: {e}")
        return {"success": False, "message": f"Error deleting chat: {str(e)}"}

# Quiz result endpoints
@app.post("/quiz-results/save")
async def save_quiz_result(
    request: dict,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    user_id = current_user.id if current_user else 1
    quiz_data = request.get("quiz_data", {})
    score = request.get("score", 0)
    total_questions = request.get("total_questions", 0)
    answers = request.get("answers", {})
    
    try:
        result = QuizResult(
            quiz_id=None,
            user_id=user_id,
            score=score,
            total_questions=total_questions,
            answers=answers
        )
        db.add(result)
        db.commit()
        db.refresh(result)
        return {"success": True, "result_id": result.id}
    except Exception as e:
        db.rollback()
        print(f"Error saving quiz result: {e}")
        return {"success": False, "message": str(e)}

@app.get("/quiz-results/history")
async def get_quiz_history(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    user_id = current_user.id if current_user else 1
    
    try:
        results = db.query(QuizResult).filter(
            QuizResult.user_id == user_id
        ).order_by(QuizResult.completed_at.desc()).all()
        
        return {
            "results": [{
                "id": r.id,
                "score": r.score,
                "total_questions": r.total_questions,
                "percentage": round((r.score / r.total_questions * 100) if r.total_questions > 0 else 0),
                "completed_at": r.completed_at.isoformat(),
                "answers": r.answers
            } for r in results]
        }
    except Exception as e:
        print(f"Error loading quiz history: {e}")
        return {"results": []}

@app.get("/quiz-results/stats")
async def get_quiz_stats(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    user_id = current_user.id if current_user else 1
    
    try:
        results = db.query(QuizResult).filter(QuizResult.user_id == user_id).all()
        
        if not results:
            return {
                "total_quizzes": 0,
                "average_score": 0,
                "total_questions": 0,
                "improvement_trend": "N/A"
            }
        
        total_quizzes = len(results)
        total_score = sum(r.score for r in results)
        total_questions = sum(r.total_questions for r in results)
        average_score = round((total_score / total_questions * 100) if total_questions > 0 else 0)
        
        # Calculate improvement trend (last 5 vs first 5)
        if len(results) >= 5:
            recent_avg = sum(r.score / r.total_questions for r in results[:5]) / 5 * 100
            old_avg = sum(r.score / r.total_questions for r in results[-5:]) / 5 * 100
            improvement = round(recent_avg - old_avg, 1)
            trend = "improving" if improvement > 5 else "stable" if improvement > -5 else "declining"
        else:
            improvement = 0
            trend = "N/A"
        
        return {
            "total_quizzes": total_quizzes,
            "average_score": average_score,
            "total_questions": total_questions,
            "improvement_trend": trend,
            "improvement_percentage": improvement
        }
    except Exception as e:
        print(f"Error calculating quiz stats: {e}")
        return {"total_quizzes": 0, "average_score": 0, "total_questions": 0, "improvement_trend": "N/A"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)