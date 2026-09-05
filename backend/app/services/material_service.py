from sqlalchemy.orm import Session
from pypdf import PdfReader
from pypdf.errors import PdfReadError

from app import models
from app.services.exceptions import InvalidRequestError


MAX_PDF_SIZE_BYTES = 20 * 1024 * 1024


def extract_pdf(
    db: Session,
    *,
    user_id: int,
    subject: str,
    file_obj,
    filename: str | None,
    start_page: int | None,
    end_page: int | None,
):
    filename = (filename or "").strip()
    subject = subject.strip()

    if not subject:
        raise InvalidRequestError("과목을 입력해야 합니다.")

    if not filename.lower().endswith(".pdf"):
        raise InvalidRequestError(
            "PDF 파일만 업로드 가능합니다.",
        )

    _validate_pdf_file(file_obj)

    try:
        reader = PdfReader(file_obj)
    except (PdfReadError, OSError, ValueError) as exc:
        raise InvalidRequestError(
            "올바른 PDF 파일을 읽을 수 없습니다."
        ) from exc

    total_pages = len(reader.pages)
    
    start_page = start_page or 1
    end_page = end_page or total_pages
        
    if start_page < 1:
        raise InvalidRequestError (
            "시작 페이지는 1 이상이어야 합니다."
        )
        
    if end_page > total_pages:
        raise InvalidRequestError (
            f"끝 페이지는 PDF의 총 페이지 수({total_pages})를 초과할 수 없습니다.",
        )

    if start_page > end_page:
        raise InvalidRequestError (
            "시작 페이지는 끝 페이지보다 클 수 없습니다."
        )
        
    extracted_pages = []
    
    for page_number in range(start_page, end_page + 1):
        try:
            text = (
                reader.pages[page_number - 1]
                .extract_text()
                or ""
            ).strip()
        except (PdfReadError, OSError, ValueError) as exc:
            raise InvalidRequestError(
                f"PDF의 {page_number}페이지를 읽을 수 없습니다."
            ) from exc
        
        if text:
            extracted_pages.append(
                {
                    "page": page_number,
                    "text": text,
                }
            )
            
    full_text = "\n\n".join(
        f"[Page {item['page']}]\n{item['text']}"
        for item in extracted_pages
    )
    
    if not full_text.strip():
        raise InvalidRequestError (
            "PDF에서 텍스트를 추출할 수 없습니다. 스캔본 PDF일 가능성이 있습니다.",
        )
        
    material = models.StudyMaterial(
        user_id=user_id,
        subject=subject,
        content=full_text,
    )
    
    try:
        db.add(material)
        db.commit()
        db.refresh(material)
    except Exception:
        db.rollback()
        raise
    
    return {
        "material_id": material.id,
        "subject": subject,
        "filename": filename,
        "page_count": total_pages,
        "selected_start_page": start_page,
        "selected_end_page": end_page,
        "selected_page_count": end_page - start_page + 1,
        "text_length": len(full_text),
        "preview": full_text[:2000] + ("..." if len(full_text) > 2000 else ""),
        "content": full_text,
        "pages": extracted_pages,
    }


def _validate_pdf_file(file_obj) -> None:
    try:
        file_obj.seek(0, 2)
        file_size = file_obj.tell()
        file_obj.seek(0)
        signature = file_obj.read(5)
        file_obj.seek(0)
    except (OSError, ValueError) as exc:
        raise InvalidRequestError("업로드한 파일을 읽을 수 없습니다.") from exc

    if file_size > MAX_PDF_SIZE_BYTES:
        raise InvalidRequestError("PDF 파일 크기는 20MB 이하여야 합니다.")

    if signature != b"%PDF-":
        raise InvalidRequestError("올바른 PDF 파일이 아닙니다.")
