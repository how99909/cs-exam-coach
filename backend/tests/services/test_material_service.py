from io import BytesIO

import pytest

from app import models
from app.services import material_service
from app.services.exceptions import InvalidRequestError


class _FakePage:
    def __init__(self, text):
        self.text = text

    def extract_text(self):
        return self.text


class _FakeReader:
    def __init__(self, file_obj):
        self.pages = [_FakePage(" First page "), _FakePage("Second page")]


def _pdf_file(content=b"%PDF-fake"):
    return BytesIO(content)


def test_extract_pdf_saves_selected_pages_and_preserves_response_contract(
    db,
    user_a,
    monkeypatch,
):
    monkeypatch.setattr(material_service, "PdfReader", _FakeReader)

    result = material_service.extract_pdf(
        db=db,
        user_id=user_a.id,
        subject=" algorithms ",
        file_obj=_pdf_file(),
        filename="notes.PDF",
        start_page=2,
        end_page=2,
    )

    material = db.get(models.StudyMaterial, result["material_id"])
    assert material is not None
    assert material.subject == "algorithms"
    assert material.content == "[Page 2]\nSecond page"
    assert result == {
        "material_id": material.id,
        "subject": "algorithms",
        "filename": "notes.PDF",
        "page_count": 2,
        "selected_start_page": 2,
        "selected_end_page": 2,
        "selected_page_count": 1,
        "text_length": len(material.content),
        "preview": material.content,
        "content": material.content,
        "pages": [{"page": 2, "text": "Second page"}],
    }


@pytest.mark.parametrize(
    ("filename", "subject", "content"),
    [
        (None, "algorithms", b"%PDF-fake"),
        ("notes.txt", "algorithms", b"%PDF-fake"),
        ("notes.pdf", "   ", b"%PDF-fake"),
        ("notes.pdf", "algorithms", b"not-a-pdf"),
    ],
)
def test_extract_pdf_rejects_invalid_metadata_or_signature(
    db,
    user_a,
    filename,
    subject,
    content,
):
    with pytest.raises(InvalidRequestError):
        material_service.extract_pdf(
            db=db,
            user_id=user_a.id,
            subject=subject,
            file_obj=_pdf_file(content),
            filename=filename,
            start_page=None,
            end_page=None,
        )

    assert db.query(models.StudyMaterial).count() == 0


def test_extract_pdf_rejects_invalid_page_range(db, user_a, monkeypatch):
    monkeypatch.setattr(material_service, "PdfReader", _FakeReader)

    with pytest.raises(InvalidRequestError):
        material_service.extract_pdf(
            db=db,
            user_id=user_a.id,
            subject="algorithms",
            file_obj=_pdf_file(),
            filename="notes.pdf",
            start_page=2,
            end_page=1,
        )


def test_extract_pdf_rolls_back_when_commit_fails(db, user_a, monkeypatch):
    monkeypatch.setattr(material_service, "PdfReader", _FakeReader)
    original_rollback = db.rollback
    rollback_called = False

    def fail_commit():
        raise RuntimeError("commit failed")

    def track_rollback():
        nonlocal rollback_called
        rollback_called = True
        original_rollback()

    monkeypatch.setattr(db, "commit", fail_commit)
    monkeypatch.setattr(db, "rollback", track_rollback)

    with pytest.raises(RuntimeError, match="commit failed"):
        material_service.extract_pdf(
            db=db,
            user_id=user_a.id,
            subject="algorithms",
            file_obj=_pdf_file(),
            filename="notes.pdf",
            start_page=None,
            end_page=None,
        )

    assert rollback_called is True
