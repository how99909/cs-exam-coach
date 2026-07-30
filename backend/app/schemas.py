from pydantic import BaseModel


class MaterialCreate(BaseModel):
    subject: str
    content: str
    
    
class QuestionGenerateRequest(BaseModel):
    subject: str
    content: str
    question_type: str = "short_answer"
    count: int = 5
    
    
class QuestionResponse(BaseModel):
    question_id: int
    question_text: str
    answer: str
    explanation: str
    concept_tag: str
    question_type: str


class GradeRequest(BaseModel):
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
