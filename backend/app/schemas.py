from pydantic import BaseModel, Field
from datetime import date


class MaterialCreate(BaseModel):
    subject: str
    content: str
    
    
class QuestionGenerateRequest(BaseModel):
    subject: str
    content: str
    question_type: str = "short_answer"
    count: int = Field(default=5, ge=1, le=20)
    difficulty: str = "medium"
    
    
class QuestionResponse(BaseModel):
    question_id: int
    question_text: str
    answer: str
    explanation: str
    concept: str
    question_type: str
    difficulty: str


class GradeRequest(BaseModel):
    question_id: int
    user_answer: str
    
    
class GradeResponse(BaseModel):
    is_correct: bool
    feedback: str
    concept: str | None = None
    
    
class ReviewItem(BaseModel):
    concept: str
    wrong_count: int


class QuestionFeedbackCreate(BaseModel):
    question_id: int
    quality_score: int = Field(ge=1, le=5)
    explanation_score: int = Field(ge=1, le=5)
    exam_relevance_score: int = Field(ge=1, le=5)
    difficulty_match_score: int = Field(ge=1, le=5)
    comment: str | None = None
    

class QuestionFeedbackResponse(BaseModel):
    id: int
    question_id: int
    quality_score: int
    explanation_score: int
    exam_relevance_score: int
    difficulty_match_score: int
    comment: str | None = None
    
    
class RagPage(BaseModel):
    page: int = Field(ge=1)
    text: str
    
    
class RagIndexRequest(BaseModel):
    subject: str
    material_id: int
    content: str | None = None
    pages: list[RagPage] | None = None
    
    
class RagAskRequest(BaseModel):
    subject: str
    question: str
    top_k: int = Field(default=5, ge=1, le=50)
    material_id: int | None = None
    
class RagDeleteRequest(BaseModel):
    subject: str
    material_id: int
    
    
class RagAnswerFeedbackCreate(BaseModel):
    subject: str
    material_id: int | None = None
    question: str
    answer: str
    accuracy_score: int = Field(ge=1, le=5)
    grounding_score: int = Field(ge=1, le=5)
    source_relevance_score: int = Field(ge=1, le=5)
    helpfulness_score: int = Field(ge=1, le=5)
    comment: str | None = None
    
    
class RagQuestionGenerateRequest(BaseModel):
    subject: str
    material_id: int | None = None
    question_type: str = "short_answer"
    difficulty: str = "medium"
    count: int = Field(default=5, ge=1, le=20)
    top_k: int = Field(default=8, ge=1, le=50)
    
    
class WeaknessRagQuestionRequest(BaseModel):
    subject: str
    material_id: int | None = None
    weakness_count: int = Field(default=3, ge=1, le=20)
    question_count: int = Field(default=5, ge=1, le=20)
    question_type: str = "short_answer"
    difficulty: str = "exam_like"
    top_k_per_concept: int = Field(default=3, ge=1, le=20)


class ExamPaperGenerateRequest(BaseModel):
    subject: str
    question_ids: list[int] = Field(min_length=1, max_length=100)
    title: str = "CS Exam Coach Practice Test"
    include_answers: bool = False
    include_explanations: bool = False


class ExamAttemptAnswerRequest(BaseModel):
    question_id: int
    user_answer: str
    
    
class ExamAttemptSubmitRequest(BaseModel):
    subject: str
    title: str = "Practice Exam"
    answers: list[ExamAttemptAnswerRequest] = Field(min_length=1, max_length=100)


class StudyReportRequest(BaseModel):
    subject: str | None = None
    limit: int = Field(default=20, ge=1, le=100)
    

class StudyGoalCreateRequest(BaseModel):
    subject: str
    title: str
    target_score: int = Field(ge=0, le=100)
    exam_date: date
    
    
class StudyGoalStrategyRequest(BaseModel):
    goal_id: int
    
    
class StudyChecklistGenerateRequest(BaseModel):
    goal_id: int
    item_count: int = Field(default=5, ge=1, le=20)
    
    
class StudyChecklistUpdateRequest(BaseModel):
    is_done: bool
    
    
class StudySessionCreateRequest(BaseModel):
    subject: str
    goal_id: int | None = None
    checklist_item_id: int | None = None
    duration_minutes: int = Field(ge=1, le=1440)
    content: str
    reflection: str | None = None
    focus_score: int | None = Field(default=None, ge=1, le=5)
    
    
class WeeklyStudyReportRequest(BaseModel):
    subject: str | None = None
    days: int = Field(default=7, ge=1, le=31)


class GoalDashboardRequest(BaseModel):
    goal_id: int


class SmartReviewQueueRequest(BaseModel):
    subject: str | None = None
    limit: int = Field(default=5, ge=1, le=50)


class SmartReviewQueueUpdateRequest(BaseModel):
    is_done: bool


class HomeDashboardRequest(BaseModel):
    subject: str | None = None


class UserCreateRequest(BaseModel):
    user_name: str = Field(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9_.-]+$")
    email: str | None = Field(default=None, max_length=255)
    password: str = Field(min_length=8, max_length=72)
    
    
class UserLoginRequest(BaseModel):
    user_name: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=72)
    
    
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_name: str
