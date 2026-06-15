from pathlib import Path

from app.db.models.document import Document
from app.services.ingestion.extractor_service import ExtractorService


def test_extractor_service_persists_success(db_session, tmp_path: Path):
    file_path = tmp_path / "sample.txt"
    file_path.write_text("hello contract", encoding="utf-8")

    document = Document(
        name="sample.txt",
        filename="sample.txt",
        file_path=str(file_path),
        mime_type="text/plain",
        size_bytes=14,
        status="queued",
    )
    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)

    artifact = ExtractorService().run(
        document_id=document.id,
        file_path=file_path,
        mime_type="text/plain",
        filename="sample.txt",
        size_bytes=14,
        session=db_session,
    )

    db_session.refresh(document)
    assert artifact.normalized_text == "hello contract"
    assert document.status == "extracted"
