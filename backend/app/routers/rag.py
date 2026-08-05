from fastapi import APIRouter

from app import rag_service, schemas

router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/index")
def index_document(request: schemas.RagIndexRequest):
    if request.pages:
        pages = [
            {
                "page": page.page,
                "text": page.text,
            }
            for page in request.pages
        ]
        
        return rag_service.index_document_pages(
            user_name=request.user_name,
            subject=request.subject,
            material_id=request.material_id,
            pages=pages,
        )
        
    if request.content:
        return rag_service.index_document(
            user_name=request.user_name,
            subject=request.subject,
            material_id=request.material_id,
            content=request.content,
        )
        
    return {
        "success": False,
        "message": "content 또는 pages 중 하나는 필요합니다."
    }
    
    
@router.post("/ask")
def ask_document(request: schemas.RagAskRequest):
    return rag_service.answer_with_context(
        user_name=request.user_name,
        subject=request.subject,
        question=request.question,
        top_k=request.top_k,
    )