from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session
from pypdf import PdfReader

from app import models
from app.database import get_db
from app.dependencies import get_current_user

router = APIRouter(prefix="/materials", tags=["materials"])

@router.post("/extract-pdf")
async def extract_pdf_text(
    subject: str = Form(...),
    start_page: int | None = Form(None, ge=1),
    end_page: int | None = Form(None, ge=1),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    filename = file.filename or ""

    if not filename.lower().endswith(".pdf"):
        return {
            "success": False,
            "message": "PDF 파일만 업로드 가능합니다.",
        }
    
    try:
        reader = PdfReader(file.file)
        total_pages = len(reader.pages)
        
        if start_page is None:
            start_page = 1
            
        if end_page is None:
            end_page = total_pages
            
        if start_page < 1:
            return {
                "success": False,
                "message": "시작 페이지는 1 이상이어야 합니다.",
            }
            
        if end_page > total_pages:
            return {
                "success": False,
                "message": f"끝 페이지는 PDF의 총 페이지 수({total_pages})를 초과할 수 없습니다.",
            }

        if start_page > end_page:
            return {
                "success": False,
                "message": "시작 페이지는 끝 페이지보다 클 수 없습니다.",
            }
            
        extracted_pages = []
        
        for page_number in range(start_page, end_page + 1):
            page = reader.pages[page_number - 1]
            text = page.extract_text() or ""
            text = text.strip()
            
            if text:
                extracted_pages.append(
                    {
                        "page": page_number,
                        "text": text,
                    }
                )
                
        full_text = "\n\n".join(
            [f"[Page {item['page']}]\n{item['text']}" for item in extracted_pages]
        )
        
        if not full_text.strip():
            return {
                "success": False,
                "message": "PDF에서 텍스트를 추출할 수 없습니다. 스캔본 PDF일 가능성이 있습니다.",
            }
            
        material = models.StudyMaterial(
            user_name=current_user.user_name,
            subject=subject,
            content=full_text,
        )
        
        db.add(material)
        db.commit()
        db.refresh(material)
        
        return {
            "success": True,
            "user_name": current_user.user_name,
            "material_id": material.id,
            "subject": subject,
            "filename": filename,
            "page_count": len(reader.pages),
            "selected_start_page": start_page,
            "selected_end_page": end_page,
            "selected_page_count": end_page - start_page + 1,
            "text_length": len(full_text),
            "preview": full_text[:2000] + ("..." if len(full_text) > 2000 else ""),
            "content": full_text,
            "pages": extracted_pages,
        }
        
    except Exception as error:
        return {
            "success": False,
            "message": f"PDF 처리 중 오류가 발생했습니다: {str(error)}",
        }
