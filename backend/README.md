# Legal-Tech Compliance API (Backend)

## Agent 1 upgrade

This backend now provides:
- queued document upload via `POST /documents/upload`
- polling document status via `GET /documents/{id}`
- extraction payload via `GET /documents/{id}/extraction`
- Celery + Redis background extraction
- Alembic migrations for schema management
- tests for providers, normalizer, service, and API flow

## Run with Docker

From the project root:

```bash
docker compose up -d --build
```

Services:
- API: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`
- Frontend: `http://localhost:4173`

## Run locally

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Apply migrations:
   ```bash
   alembic upgrade head
   ```
3. Run the API:
   ```bash
   uvicorn app.main:app --reload
   ```
4. Run the worker:
   ```bash
   celery -A app.tasks.celery_app.celery_app worker --loglevel=info
   ```

## Test

```bash
pytest
```
