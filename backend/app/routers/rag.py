from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app import rag_service, schemas, models
from app.database import get_db
from app.dependencies import get_current_user

router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/index")
def index_document(
    request: schemas.RagIndexRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    material = (
        db.query(models.StudyMaterial)
        .filter(models.StudyMaterial.id == request.material_id)
        .filter(models.StudyMaterial.user_id == current_user.id)
        .filter(models.StudyMaterial.subject == request.subject)
        .first()
    )
    if material is None:
        raise HTTPException(status_code=404, detail="학습 자료를 찾을 수 없습니다.")

    if request.pages:
        pages = [
            {
                "page": page.page,
                "text": page.text,
            }
            for page in request.pages
        ]
        
        result = rag_service.index_document_pages(
            user_name=current_user.user_name,
            subject=request.subject,
            material_id=request.material_id,
            pages=pages,
        )
    elif request.content:
        result =  rag_service.index_document(
            user_name=current_user.user_name,
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
def ask_document(
    request: schemas.RagAskRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if request.material_id is not None:
        material = (
            db.query(models.StudyMaterial)
            .filter(models.StudyMaterial.id == request.material_id)
            .filter(
                models.StudyMaterial.user_id == current_user.id
            )
            .filter(models.StudyMaterial.subject == request.subject)
            .first()
        )
        
        if material is None:
            raise HTTPException(
                status_code=404,
                detail="학습 자료를 찾지 못했습니다.",
            )
        
    result =  rag_service.answer_with_context(
        user_name=current_user.user_name,
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
    subject: str | None = None,
    current_user: models.User = Depends(get_current_user),
):
    return rag_service.list_indexed_documents(
        user_name=current_user.user_name,
        subject=subject,
    )
    
    
@router.delete("/documents")
def delete_document(
    request: schemas.RagDeleteRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    material = (
        db.query(models.StudyMaterial)
        .filter(models.StudyMaterial.id == request.material_id)
        .filter(
            models.StudyMaterial.user_id == current_user.id
        )
        .filter(models.StudyMaterial.subject == request.subject)
        .first()
    )
    
    if material is None:
        raise HTTPException(
            status_code=404,
            detail="학습 자료를 찾지 못했습니다.",
        )
    
    result = rag_service.delete_indexed_document(
        user_name=current_user.user_name,
        subject=request.subject,
        material_id=request.material_id,
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=404,
            detail=result.get("message", "삭제할 RAG 문서를 찾지 못했습니다."),
        )
        
    return result
