from pydantic import BaseModel, EmailStr, ConfigDict
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
    
    model_config = ConfigDict(from_attributes=True)

class AssetResponse(BaseModel):
    id: int
    filename: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class QuizGenerateRequest(BaseModel):
    attached_files: List[str] # Expects filenames
    quiz_type: str
    num_questions: int
    topic: Optional[str] = None
    difficulty: Optional[str] = None
    language: Optional[str] = "en" # Add language parameter

class QuestionResponse(BaseModel):
    id: int
    question_text: str
    question_type: str
    options: Optional[List[str]] = None
    correct_answer: Optional[str] = None # Added for quiz generation and review

    model_config = ConfigDict(from_attributes=True)

class QuizCreate(BaseModel):
    id: int
    title: str
    quiz_type: str
    questions: List[QuestionResponse]

    model_config = ConfigDict(from_attributes=True)

class QuizAnswerSubmit(BaseModel):
    question_id: int
    user_answer: str

class QuizSubmit(BaseModel):
    quiz_id: int
    answers: List[QuizAnswerSubmit]

class QuizQuestionResultSchema(BaseModel):
    question_id: int
    question_text: str
    question_type: str
    options: Optional[List[str]] = None
    correct_answer: Optional[str] = None
    user_answer: Optional[str] = None
    is_correct: bool
    explanation: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class QuizResultResponse(BaseModel):
    id: int
    quiz_id: int
    quiz_title: str
    user_id: int
    score: int
    total_questions: int
    percentage: float
    completed_at: datetime
    asset_filename: Optional[str] = None
    questions: List[QuizQuestionResultSchema] = []
    study_suggestions: List[str] = []

    model_config = ConfigDict(from_attributes=True)

class StudySuggestionResponse(BaseModel):
    id: int
    quiz_result_id: int
    suggestion_text: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
