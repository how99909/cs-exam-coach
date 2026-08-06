from fastapi import APIRouter, HTTPException

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
        
        result = rag_service.index_document_pages(
            user_name=request.user_name,
            subject=request.subject,
            material_id=request.material_id,
            pages=pages,
        )
    elif request.content:
        result =  rag_service.index_document(
            user_name=request.user_name,
            subject=request.subject,
            material_id=request.material_id,
            content=request.content,
        )
    else:
        raise HTTPException(
            status_code=400,
            detail="content 또는 pages 중 하나는 필요합니다.",
        )
        
    if not result.get("success"):
        raise HTTPException(
            status_code=400,
            detail=result.get("message", "RAG 인덱싱에 실패했습니다."),
        )
        
    return result
    
    
@router.post("/ask")
def ask_document(request: schemas.RagAskRequest):
    result =  rag_service.answer_with_context(
        user_name=request.user_name,
        subject=request.subject,
        question=request.question,
        top_k=request.top_k,
        material_id=request.material_id,
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=404,
            detail=result.get("message", "RAG 답변 생성에 실패했습니다."),
        )
        
    return result
    
    
@router.get("/documents")
def list_documents(
    user_name: str | None = None,
    subject: str | None = None,
):
    return rag_service.list_indexed_documents(
        user_name=user_name,
        subject=subject,
    )
    
    
@router.delete("/documents")
def delete_document(request: schemas.RagDeleteRequest):
    result = rag_service.delete_indexed_document(
        user_name=request.user_name,
        subject=request.subject,
        material_id=request.material_id,
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=404,
            detail=result.get("message", "삭제할 RAG 문서를 찾지 못했습니다."),
        )
        
    return result