"""Deterministic contract rewrite from Agent 2 spans + Agent 4 recommendations."""

from app.services.rewrite.engine import (
    build_revision_metadata,
    build_revised_text,
    clamp_clauses_for_document,
)

__all__ = ["build_revised_text", "build_revision_metadata", "clamp_clauses_for_document"]
