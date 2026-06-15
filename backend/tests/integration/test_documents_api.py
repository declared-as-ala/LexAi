from app.api.routes import documents as document_routes
from app.tasks.extraction import run_extraction_sync


def test_upload_and_extract_flow(client, monkeypatch):
    monkeypatch.setattr(document_routes, "enqueue_extraction", lambda document_id: (run_extraction_sync(document_id), None)[1])

    response = client.post(
        "/documents/upload",
        files={"file": ("contract.txt", b"line one\n\nline two", "text/plain")},
    )
    assert response.status_code == 201
    upload_payload = response.json()
    document_id = upload_payload["id"]
    assert upload_payload["progress_stage"] in {"queued", "completed"}

    document_response = client.get(f"/documents/{document_id}")
    assert document_response.status_code == 200
    assert document_response.json()["status"] == "extracted"
    assert document_response.json()["progress_percent"] == 100

    extraction_response = client.get(f"/documents/{document_id}/extraction")
    assert extraction_response.status_code == 200
    payload = extraction_response.json()["extraction"]
    assert payload["normalized_text"] == "line one\n\nline two"

    list_response = client.get("/documents")
    assert list_response.status_code == 200
    assert list_response.json()["total_count"] == 1

    summary_response = client.get("/documents/summary")
    assert summary_response.status_code == 200
    assert summary_response.json()["extracted_count"] == 1


def test_upload_rejects_unsupported_file(client):
    response = client.post(
        "/documents/upload",
        files={"file": ("archive.zip", b"zip", "application/zip")},
    )
    assert response.status_code == 422


def test_retry_failed_document(client, monkeypatch):
    monkeypatch.setattr(document_routes, "enqueue_extraction", lambda document_id: None)

    upload_response = client.post(
        "/documents/upload",
        files={"file": ("contract.txt", b"retry me", "text/plain")},
    )
    document_id = upload_response.json()["id"]

    from app.db.session import SessionLocal
    from app.db.models.document import Document

    db = SessionLocal()
    try:
        document = db.get(Document, document_id)
        document.status = "failed"
        document.progress_stage = "failed"
        document.progress_percent = 42
        document.last_error = "boom"
        db.commit()
    finally:
        db.close()

    retried_ids: list[int] = []
    monkeypatch.setattr(document_routes, "enqueue_extraction", lambda retry_id: retried_ids.append(retry_id) or None)

    retry_response = client.post(f"/documents/{document_id}/retry")
    assert retry_response.status_code == 200
    assert retry_response.json()["status"] == "queued"
    assert retry_response.json()["progress_stage"] == "queued"
    assert retried_ids == [document_id]
