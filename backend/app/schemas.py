from pydantic import BaseModel
from datetime import date


class MaterialCreate(BaseModel):
    subject: str
    content: str
    
    
class QuestionGenerateRequest(BaseModel):
    user_name: str = "default_user"
    subject: str
    content: str
    question_type: str = "short_answer"
    count: int = 5
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
    user_name: str = "default_user"
    question_id: int
    question_text: str
    correct_answer: str
    user_answer: str
    concept_tag: str | None = None
    
    
class GradeResponse(BaseModel):
    is_correct: bool
    feedback: str
    concept_tag: str | None = None
    
    
class ReviewItem(BaseModel):
    concept_tag: str
    wrong_count: int


class QuestionFeedbackCreate(BaseModel):
    user_name: str = "default_user"
    question_id: int
    quality_score: int
    explanation_score: int
    exam_relevance_score: int
    difficulty_match_score: int
    comment: str | None = None
    

class QuestionFeedbackResponse(BaseModel):
    id: int
    user_name: str
    question_id: int
    quality_score: int
    explanation_score: int
    exam_relevance_score: int
    difficulty_match_score: int
    comment: str | None = None
    
    
class RagPage(BaseModel):
    page: int
    text: str
    
    
class RagIndexRequest(BaseModel):
    user_name: str = "default_user"
    subject: str
    material_id: int
    content: str | None = None
    pages: list[RagPage] | None = None
    
    
class RagAskRequest(BaseModel):
    user_name: str = "default_user"
    subject: str
    question: str
    top_k: int = 5
    material_id: int | None = None
    
class RagDeleteRequest(BaseModel):
    user_name: str = "default_user"
    subject: str
    material_id: int
    
    
class RagAnswerFeedbackCreate(BaseModel):
    user_name: str = "default_user"
    subject: str
    material_id: int | None = None
    question: str
    answer: str
    accuracy_score: int
    grounding_score: int
    source_relevance_score: int
    helpfulness_score: int
    comment: str | None = None
    
    
class RagQuestionGenerateRequest(BaseModel):
    user_name: str = "default_user"
    subject: str
    material_id: int | None = None
    question_type: str = "short_answer"
    difficulty: str = "medium"
    count: int = 5
    top_k: int = 8
    
    
class WeaknessRagQuestionRequest(BaseModel):
    user_name: str = "default_user"
    subject: str
    material_id: int | None = None
    weakness_count: int = 3
    question_count: int = 5
    question_type: str = "short_answer"
    difficulty: str = "exam_like"
    top_k_per_concept: int = 3


class ExamPaperGenerateRequest(BaseModel):
    user_name: str = "default_user"
    subject: str
    question_ids: list[int]
    title: str = "CS Exam Coach Practice Test"
    include_answers: bool = False
    include_explanations: bool = False


class ExamAttemptAnswerRequest(BaseModel):
    question_id: int
    user_answer: str
    
    
class ExamAttemptSubmitRequest(BaseModel):
    user_name: str = "default_user"
    subject: str
    title: str = "Practice Exam"
    answers: list[ExamAttemptAnswerRequest]


class StudyReportRequest(BaseModel):
    user_name: str = "default_user"
    subject: str | None = None
    limit: int = 20
    

class StudyGoalCreateRequest(BaseModel):
    user_name: str = "default_user"
    subject: str
    title: str
    target_score: int
    exam_date: date
    
    
class StudyGoalStrategyRequest(BaseModel):
    user_name: str = "default_user"
    goal_id: int
    
    
class StudyChecklistGenerateRequest(BaseModel):
    user_name: str = "default_user"
    goal_id: int
    item_count: int = 5
    
    
class StudyChecklistUpdateRequest(BaseModel):
    user_name: str = "default_user"
    is_done: bool