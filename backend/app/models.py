from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean

from app.database import Base

class StudyMaterial(Base):
    __tablename__ = "study_materials"
    
    id = Column(Integer, primary_key=True, index=True)
    user_name = Column(String(100), nullable=False, default="default_user")
    subject = Column(String(100), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    
class Question(Base):
    __tablename__ = "questions"
    
    id = Column(Integer, primary_key=True, index=True)
    material_id = Column(Integer, nullable=False)
    question_text = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    explanation = Column(Text, nullable=True)
    concept_tag = Column(String(100), nullable=True)
    question_type = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    
class WrongAnswer(Base):
    __tablename__ = "wrong_answers"
    
    id = Column(Integer, primary_key=True, index=True)
    user_name = Column(String(100), nullable=False, default="default_user")
    question_id = Column(Integer, nullable=False)
    user_answer = Column(Text, nullable=False)
    correct_answer = Column(Text, nullable=False)
    concept_tag = Column(String(100), nullable=True)
    feedback = Column(Text, nullable=True)
    is_correct = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)