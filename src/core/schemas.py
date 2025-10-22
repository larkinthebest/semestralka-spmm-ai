from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime

class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    
    class Config:
        from_attributes = True

class DocumentResponse(BaseModel):
    id: int
    filename: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class QuizCreate(BaseModel):
    document_id: int
    quiz_type: str = "multiple_choice"
    num_questions: int = 5

class QuizQuestion(BaseModel):
    question: str
    options: Optional[List[str]] = None
    correct_answer: str
    explanation: Optional[str] = None

class QuizResponse(BaseModel):
    id: int
    title: str
    questions: List[Dict[str, Any]]
    quiz_type: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class ChatMessage(BaseModel):
    content: str
    document_id: Optional[int] = None

class ChatResponse(BaseModel):
    response: str

class QuizSubmission(BaseModel):
    quiz_id: int
    answers: Dict[int, str]  # question_index: answer