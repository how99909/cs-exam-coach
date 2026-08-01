from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session
from pypdf import PdfReader

from app import models
from app.database import get_db

router = APIRouter(prefix="/materials", tags=["materials"])

@router.post("/extract-pdf")
async def extract_pdf_text(
    user_name: str = Form("default_user"),
    subject: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not file.filename.lower().endswith(".pdf"):
        return {
            "success": False,
            "message": "PDF 파일만 업로드 가능합니다.",
        }
    
    try:
        reader = PdfReader(file.file)
        extracted_pages = []
        
        for page_number, page in enumerate(reader.pages, start=1):
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
            user_name=user_name,
            subject=subject,
            content=full_text,
        )
        
        db.add(material)
        db.commit()
        db.refresh(material)
        
        return {
            "success": True,
            "user_name": user_name,
            "material_id": material.id,
            "subject": subject,
            "filename": file.filename,
            "page_count": len(reader.pages),
            "text_length": len(full_text),
            "preview": full_text[:2000] + ("..." if len(full_text) > 2000 else ""),
            "content": full_text,
        }
        
    except Exception as error:
        return {
            "success": False,
            "message": f"PDF 처리 중 오류가 발생했습니다: {str(error)}",
        }