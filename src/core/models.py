from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, index=True)
    hashed_password = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    assets = relationship("Asset", back_populates="user")
    quizzes = relationship("Quiz", back_populates="user")
    chats = relationship("Chat", back_populates="user")
    quiz_results = relationship("QuizResult", back_populates="user")
    study_suggestions = relationship("StudySuggestion", back_populates="user")
class Asset(Base):
    __tablename__ = "assets"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    file_path = Column(String)
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    user = relationship("User", back_populates="assets")
    quizzes = relationship("Quiz", back_populates="asset")
    sources = relationship("Source", back_populates="asset")

class Source(Base):
    __tablename__ = "sources"
    
    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"))
    chat_id = Column(Integer, ForeignKey("chats.id"))
    
    asset = relationship("Asset", back_populates="sources")
    chat = relationship("Chat", back_populates="sources")

class Quiz(Base):
    __tablename__ = "quizzes"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    quiz_type = Column(String)  # multiple_choice, true_false, fill_blank
    created_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"))
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=True)
    
    user = relationship("User", back_populates="quizzes")
    asset = relationship("Asset", back_populates="quizzes")
    questions = relationship("Question", back_populates="quiz")
    quiz_results = relationship("QuizResult", back_populates="quiz")

class Question(Base):
    __tablename__ = "questions"
    
    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"))
    question_text = Column(Text)
    question_type = Column(String) # e.g., "multiple_choice", "true_false", "fill_in_the_blank"
    options = Column(JSON, nullable=True) # For multiple choice
    correct_answer = Column(Text)
    explanation = Column(Text, nullable=True) # Add explanation field
    
    quiz = relationship("Quiz", back_populates="questions")
    answers = relationship("Answer", back_populates="question")

class Answer(Base):
    __tablename__ = "answers"
    
    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"))
    quiz_result_id = Column(Integer, ForeignKey("quiz_results.id"))
    user_answer = Column(Text)
    is_correct = Column(Boolean)
    
    question = relationship("Question", back_populates="answers")
    quiz_result = relationship("QuizResult", back_populates="answers")

class Chat(Base):
    __tablename__ = "chats"
    
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, index=True)  # Frontend chat ID
    title = Column(String, default="New Chat")
    mode = Column(String, default="explanation") # Mode from chat history (first message)
    tutor = Column(String, default="enola") # Tutor from chat history (first message)
    current_mode = Column(String, default="explanation") # Current mode in UI
    current_tutor = Column(String, default="enola") # Current tutor in UI
    messages = Column(JSON)  # Store full conversation
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    user = relationship("User", back_populates="chats")
    sources = relationship("Source", back_populates="chat")

class QuizResult(Base):
    __tablename__ = "quiz_results"
    
    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    score = Column(Integer)
    total_questions = Column(Integer)
    completed_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="quiz_results")
    quiz = relationship("Quiz", back_populates="quiz_results")
    answers = relationship("Answer", back_populates="quiz_result")
    study_suggestions = relationship("StudySuggestion", back_populates="quiz_result")

class StudySuggestion(Base):
    __tablename__ = "study_suggestions"
    
    id = Column(Integer, primary_key=True, index=True)
    quiz_result_id = Column(Integer, ForeignKey("quiz_results.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    suggestion_text = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="study_suggestions")
    quiz_result = relationship("QuizResult", back_populates="study_suggestions")
