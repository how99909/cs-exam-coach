from fastapi import APIRouter

from app import rag_service, schemas

router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/index")
def index_document(request: schemas.RagIndexRequest):
    return rag_service.index_document(
        user_name=request.user_name,
        subject=request.subject,
        material_id=request.material_id,
        content=request.content,
    )
    
    
@router.post("/ask")
def ask_document(request: schemas.RagAskRequest):
    return rag_service.answer_with_context(
        user_name=request.user_name,
        subject=request.subject,
        question=request.question,
        top_k=request.top_k,
    )