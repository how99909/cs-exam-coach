from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Date, Index

from app.database import Base
from app.time_utils import utc_now

class StudyMaterial(Base):
    __tablename__ = "study_materials"
    __table_args__ = (
        Index("ix_study_materials_user_subject_created", "user_id", "subject", "created_at"),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    subject = Column(String(100), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utc_now)

    
class Question(Base):
    __tablename__ = "questions"
    
    id = Column(Integer, primary_key=True, index=True)
    material_id = Column(Integer, ForeignKey("study_materials.id"), nullable=False)
    question_text = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    explanation = Column(Text, nullable=True)
    concept = Column(String(100), nullable=True)
    question_type = Column(String(50), nullable=False)
    difficulty = Column(String(50), nullable=False, default="medium")
    created_at = Column(DateTime, default=utc_now)
    
    
class WrongAnswer(Base):
    __tablename__ = "wrong_answers"
    __table_args__ = (
        Index("ix_wrong_answers_user_created", "user_id", "created_at"),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    question_id = Column(Integer, nullable=False)
    user_answer = Column(Text, nullable=False)
    correct_answer = Column(Text, nullable=False)
    concept = Column(String(100), nullable=True)
    feedback = Column(Text, nullable=True)
    is_correct = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utc_now)
    
    
class QuestionFeedback(Base):
    __tablename__ = "question_feedback"
    __table_args__ = (
        Index("ix_question_feedback_user_question", "user_id", "question_id"),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    question_id = Column(Integer, nullable=False)
    quality_score = Column(Integer, nullable=False)
    explanation_score = Column(Integer, nullable=False)
    exam_relevance_score = Column(Integer, nullable=False)
    difficulty_match_score = Column(Integer, nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    
    
class RagAnswerFeedback(Base):
    __tablename__ = "rag_answer_feedback"
    __table_args__ = (
        Index("ix_rag_feedback_user_subject_created", "user_id", "subject", "created_at"),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    subject = Column(String(100), nullable=False)
    material_id = Column(Integer, nullable=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    accuracy_score = Column(Integer, nullable=False)
    grounding_score = Column(Integer, nullable=False)
    source_relevance_score = Column(Integer, nullable=False)
    helpfulness_score = Column(Integer, nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)


class ExamAttempt(Base):
    __tablename__ = "exam_attempts"
    __table_args__ = (
        Index("ix_exam_attempts_user_subject_created", "user_id", "subject", "created_at"),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    subject = Column(String(100), nullable=False)
    title = Column(String(255), nullable=False)
    total_questions = Column(Integer, nullable=False)
    correct_count = Column(Integer, nullable=False, default=0)
    score = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=utc_now)
    
    
class ExamAttemptAnswer(Base):
    __tablename__ = "exam_attempt_answers"
    
    id = Column(Integer, primary_key=True, index=True)
    attempt_id = Column(Integer, ForeignKey("exam_attempts.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    user_answer = Column(Text, nullable=False)
    is_correct = Column(Boolean, nullable=False, default=False)
    feedback = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    
    
class StudyGoal(Base):
    __tablename__ = "study_goals"
    __table_args__ = (
        Index("ix_study_goals_user_exam_date", "user_id", "exam_date"),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    subject = Column(String(100), nullable=False)
    title = Column(String(255), nullable=False)
    target_score = Column(Integer, nullable=False)
    exam_date = Column(Date, nullable=False)
    created_at = Column(DateTime, default=utc_now)


class StudyChecklistItem(Base):
    __tablename__ = "study_checklist_items"
    __table_args__ = (
        Index("ix_checklist_user_goal_done", "user_id", "goal_id", "is_done"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    goal_id = Column(Integer, ForeignKey("study_goals.id"), nullable=False)
    subject = Column(String(100), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(Integer, nullable=False, default=1)
    is_done = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=utc_now)
    completed_at = Column(DateTime, nullable=True)
    
    
class StudySession(Base):
    __tablename__ = "study_sessions"
    __table_args__ = (
        Index("ix_study_sessions_user_subject_created", "user_id", "subject", "created_at"),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    subject = Column(String(100), nullable=False)
    goal_id = Column(Integer, ForeignKey("study_goals.id"), nullable=True)
    checklist_item_id = Column(Integer, ForeignKey("study_checklist_items.id"), nullable=True)
    duration_minutes = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    reflection = Column(Text, nullable=True)
    focus_score = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=utc_now)


class SmartReviewQueueItem(Base):
    __tablename__ = "smart_review_queue_items"
    __table_args__ = (
        Index("ix_review_queue_user_done_priority", "user_id", "is_done", "priority"),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    subject = Column(String(100), nullable=True)
    title = Column(String(255), nullable=False)
    reason = Column(Text, nullable=True)
    action = Column(Text, nullable=True)
    estimated_minutes = Column(Integer, nullable=True)
    priority = Column(Integer, nullable=False, default=1)
    source_type = Column(String(100), nullable=True)
    is_done = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=utc_now)
    completed_at = Column(DateTime, nullable=True)


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    user_name = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=True, index=True)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=utc_now)
