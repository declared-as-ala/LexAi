from app.db.models.document import Document
from app.services.ingestion.progress import DocumentProgressService


def test_progress_service_updates_document(db_session):
    document = Document(
        name="sample.txt",
        filename="sample.txt",
        file_path="/tmp/sample.txt",
        mime_type="text/plain",
        size_bytes=10,
        status="queued",
    )
    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)

    service = DocumentProgressService(db_session)
    service.extracting(document.id, "starting", "Worker started extraction", 15)

    db_session.refresh(document)
    assert document.status == "extracting"
    assert document.progress_stage == "starting"
    assert document.progress_percent == 15
