from pydantic import BaseModel


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
    concept_tag: str
    question_type: str


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