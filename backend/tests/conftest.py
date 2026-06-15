from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

TEST_ROOT = Path(__file__).resolve().parent
UPLOAD_DIR = TEST_ROOT / "tmp_uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

os.environ.setdefault("DATABASE_URL", f"sqlite:///{(TEST_ROOT / 'test_agent1.db').as_posix()}")
os.environ.setdefault("UPLOAD_DIR", str(UPLOAD_DIR))
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/15")

from app.db.session import Base, SessionLocal, engine
from app.main import app


@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client
