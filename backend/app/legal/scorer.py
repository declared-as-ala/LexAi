"""Agent 3 — Scorer: computes per-framework and global compliance scores from violations."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from app.legal.rule_engine import Violation

_WEIGHTS_FILE = Path(__file__).parent / "weights.json"


@dataclass
class ScoreResult:
    global_score: float                        # 0–100
    litigation_risk: str                       # low | medium | high | critical
    framework_scores: dict[str, float] = field(default_factory=dict)
    framework_violation_counts: dict[str, int] = field(default_factory=dict)


def _load_weights() -> dict:
    if _WEIGHTS_FILE.exists():
        return json.loads(_WEIGHTS_FILE.read_text(encoding="utf-8"))
    return {}


def compute_scores(violations: list[Violation], active_frameworks: list[str]) -> ScoreResult:
    """
    Compute per-framework compliance scores and a weighted global score.

    Formula:
        framework_score(F) = max(0, 100 - Σ severity_weight(v) for v in violations[F])
        global_score = Σ(score(F) × weight(F)) / Σ(weight(F) for active F)
    """
    cfg = _load_weights()
    severity_weights: dict[str, int] = cfg.get("severity_weights", {
        "critical": 30, "high": 20, "medium": 10, "low": 5
    })
    fw_cfg: dict[str, dict] = cfg.get("frameworks", {})
    risk_thresholds = cfg.get("litigation_risk_thresholds", {})

    # Group violations by framework
    by_framework: dict[str, list[Violation]] = {fw: [] for fw in active_frameworks}
    for v in violations:
        if v.framework in by_framework:
            by_framework[v.framework].append(v)

    # Per-framework scores
    framework_scores: dict[str, float] = {}
    framework_violation_counts: dict[str, int] = {}
    for fw in active_frameworks:
        fw_violations = by_framework.get(fw, [])
        deduction = sum(severity_weights.get(v.severity, 10) for v in fw_violations)
        score = round(max(0.0, 100.0 - deduction), 1)
        framework_scores[fw] = score
        framework_violation_counts[fw] = len(fw_violations)

    # Global weighted score
    total_weight = 0.0
    weighted_sum = 0.0
    for fw in active_frameworks:
        w = fw_cfg.get(fw, {}).get("weight", 0.1)
        weighted_sum += framework_scores[fw] * w
        total_weight += w

    global_score = round(weighted_sum / total_weight, 1) if total_weight > 0 else 100.0

    # Litigation risk from thresholds
    litigation_risk = _compute_risk(global_score, risk_thresholds)

    return ScoreResult(
        global_score=global_score,
        litigation_risk=litigation_risk,
        framework_scores=framework_scores,
        framework_violation_counts=framework_violation_counts,
    )


def _compute_risk(score: float, thresholds: dict) -> str:
    if score < thresholds.get("critical", {}).get("max_score", 40):
        return "critical"
    if score < thresholds.get("high", {}).get("max_score", 60):
        return "high"
    if score < thresholds.get("medium", {}).get("max_score", 80):
        return "medium"
    return "low"
