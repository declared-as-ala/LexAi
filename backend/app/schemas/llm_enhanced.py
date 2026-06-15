"""Strict JSON schema for Agent 4 LLM enhancement (hybrid layer)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class LlmEnhancedOutput(BaseModel):
    """LLM must return only these keys — mapped onto DB fields in llm_service."""

    improved_rewrite: str = Field(..., min_length=1, max_length=32000)
    clear_explanation: str = Field(..., min_length=1, max_length=16000)
    risk_summary: str = Field(..., min_length=1, max_length=8000)
