"""Celery application factory for background extraction tasks."""

from __future__ import annotations

from celery import Celery

from app.core.config import REDIS_URL

celery_app = Celery(
    "legaltech",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        "app.tasks.extraction",
        "app.tasks.nlp_analysis",
        "app.tasks.evaluation",
        "app.tasks.recommendation",
    ],
)
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)