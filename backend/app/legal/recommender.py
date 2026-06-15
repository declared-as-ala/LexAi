"""Agent 4 — template-based recommendations from evaluation violations."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

_TEMPLATES_PATH = Path(__file__).resolve().parent / "templates" / "recommendations_fr.json"

_SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}
_SLOT_PATTERN = re.compile(r"\{([A-Z0-9_]+)\}")


def _severity_rank(severity: str | None) -> int:
    if not severity:
        return 99
    return _SEVERITY_ORDER.get(str(severity).lower(), 50)


def load_templates_by_rule_id() -> dict[str, dict[str, Any]]:
    raw = json.loads(_TEMPLATES_PATH.read_text(encoding="utf-8"))
    templates = raw.get("templates") or []
    return {str(t["rule_id"]): t for t in templates if t.get("rule_id")}


def _clause_by_id(clauses: list[dict[str, Any]], clause_id: str | None) -> dict[str, Any] | None:
    if not clause_id:
        return None
    for c in clauses:
        if c.get("clause_id") == clause_id:
            return c
    return None


def _first_entity_by_label(clause: dict[str, Any] | None, label: str | None) -> str | None:
    if not clause or not label:
        return None
    best: tuple[float, str] | None = None
    for ent in clause.get("entities") or []:
        if (ent.get("label") or "") != label:
            continue
        text = (ent.get("text") or "").strip()
        if not text:
            continue
        conf = float(ent.get("confidence") or 0.0)
        if best is None or conf > best[0]:
            best = (conf, text)
    return best[1] if best else None


def _fill_template_string(template: str, slots: dict[str, Any] | None, clause: dict[str, Any] | None) -> str:
    slots = slots or {}

    def replace_slot(match: re.Match[str]) -> str:
        key = match.group(1)
        spec = slots.get(key)
        if isinstance(spec, dict):
            ent_label = spec.get("entity_label")
            default = spec.get("default")
            if isinstance(default, str):
                default_val = default
            elif default is not None:
                default_val = str(default)
            else:
                default_val = f"[{key}]"
            if ent_label:
                picked = _first_entity_by_label(clause, str(ent_label))
                if picked:
                    return picked
            return default_val
        return f"[{key}]"

    return _SLOT_PATTERN.sub(replace_slot, template)


def _fallback_recommendation(violation: dict[str, Any]) -> dict[str, Any]:
    fw = violation.get("framework") or ""
    art = violation.get("article") or ""
    desc = violation.get("description") or "Non-conformité détectée."
    hint = violation.get("remediation_hint") or ""
    clause_text = violation.get("clause_text") or ""
    return {
        "issue_description": desc,
        "recommendation_text": (
            f"Mettre à jour la clause pour corriger l'écart de conformité ({fw} {art}). "
            f"Indication : {hint}".strip()
        ),
        "rewritten_clause": (
            f"[Proposition indicative — à valider juridiquement]\n\n{clause_text}\n\n"
            f"— Ajouts suggérés : {hint}" if clause_text else f"[Clause à rédiger — {hint}]"
        ),
        "legal_rationale": f"Référence : {fw} {art}".strip(),
        "generated_by": "fallback_v1",
    }


def build_recommendation_rows(
    violations: list[dict[str, Any]],
    clauses: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Produce ordered recommendation dicts ready for Recommendation ORM rows.
    Sorted by severity (critical first), then stable by violation_id.
    """
    templates = load_templates_by_rule_id()
    sorted_v = sorted(
        violations,
        key=lambda v: (_severity_rank(v.get("severity")), v.get("violation_id") or ""),
    )
    rows: list[dict[str, Any]] = []
    for priority, violation in enumerate(sorted_v, start=1):
        rule_id = str(violation.get("rule_id") or "")
        clause = _clause_by_id(clauses, violation.get("clause_id"))
        tpl = templates.get(rule_id)

        if tpl:
            slots = tpl.get("slots") or {}
            issue = _fill_template_string(str(tpl.get("issue_description") or ""), slots, clause)
            rec = _fill_template_string(str(tpl.get("recommendation_text") or ""), slots, clause)
            rewritten = _fill_template_string(str(tpl.get("rewritten_clause") or ""), slots, clause)
            rationale = _fill_template_string(str(tpl.get("legal_rationale") or ""), slots, clause)
            generated_by = "template_v1"
        else:
            fb = _fallback_recommendation(violation)
            issue = fb["issue_description"]
            rec = fb["recommendation_text"]
            rewritten = fb["rewritten_clause"]
            rationale = fb["legal_rationale"]
            generated_by = fb["generated_by"]

        rows.append(
            {
                "violation_id": violation.get("violation_id"),
                "clause_id": violation.get("clause_id"),
                "violation_rule_id": rule_id or None,
                "framework": tpl.get("framework") if tpl else violation.get("framework"),
                "article": tpl.get("article") if tpl else violation.get("article"),
                "severity": violation.get("severity"),
                "priority": priority,
                "issue_description": issue,
                "recommendation_text": rec,
                "rewritten_clause": rewritten,
                "legal_rationale": rationale,
                "generated_by": generated_by,
            }
        )
    return rows
