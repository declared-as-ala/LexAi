"""
Hybrid Agent 4 LLM layer: templates first, then optional Groq enhancement.

- Per-clause groups: multiple template rows for the same clause_id are merged in one LLM call.
- clause_id null: each violation stays isolated (never merged across null keys).
- On any LLM/parse failure, original template (or fallback) rows are preserved.

Example — single violation LLM input (JSON sent in the user message)::

    {
      "original_clause": "Le responsable du traitement peut transférer...",
      "violation": "Titre — description — hint",
      "risk_level": "high",
      "legal_reference": "GDPR Art. 44",
      "template_rewrite": "... texte issu du gabarit ...",
      "issue_description": "... issue gabarit ..."
    }

Expected strict JSON output::

    {
      "improved_rewrite": "...",
      "clear_explanation": "...",
      "risk_summary": "..."
    }

Merge mode adds ``merge_mode: true`` and ``violations`` (list of the same per-item fields)
instead of a flat single violation object.
"""

from __future__ import annotations

import json
import re
from typing import Any

from app.core.config import LLM_ENABLED
from app.core.logging import get_logger
from app.schemas.llm_enhanced import LlmEnhancedOutput
from app.services.llm.groq_client import groq_chat_completion_content

logger = get_logger(__name__)

_SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}

_SYSTEM_SINGLE = (
    "Tu es un juriste senior rédigeant en français juridique formel (contrats, conformité RGPD/LNPDP/ISO). "
    "Tu reçois un JSON avec : clause d'origine, violation, niveau de risque, référence légale fournie, "
    "proposition de réécriture issue d'un gabarit (template_rewrite), et description du problème. "
    "Ta tâche : améliorer la formulation juridique, clarifier l'exposé, sans inventer d'articles ni de références "
    "qui ne figurent pas dans legal_reference, sans ajouter de faits, sans affaiblir les obligations. "
    "Réponds uniquement avec un objet JSON au format exact : "
    '{"improved_rewrite":"...","clear_explanation":"...","risk_summary":"..."} '
    "improved_rewrite = texte de clause réécrite cohérent ; clear_explanation = mesures et justification opérationnelle ; "
    "risk_summary = synthèse courte du risque (2–4 phrases max)."
)

_SYSTEM_MERGE = (
    "Tu es un juriste senior (français juridique formel). Plusieurs violations portent sur la MÊME clause contractuelle. "
    "Tu reçois le texte d'origine de la clause et une liste d'éléments (violation, risque, référence légale, réécriture gabarit, description). "
    "Produit UNE seule réécriture de clause qui traite l'ensemble des problèmes de manière cohérente, sans redondance, "
    "sans inventer de références hors de celles fournies, sans hallucination. "
    "Réponds uniquement avec : "
    '{"improved_rewrite":"...","clear_explanation":"...","risk_summary":"..."} '
    "risk_summary = synthèse globale des risques ; clear_explanation = recommandations claires couvrant tous les points."
)


def _parse_json_payload(text: str) -> dict[str, Any] | None:
    t = (text or "").strip()
    if not t:
        return None
    if t.startswith("```"):
        t = re.sub(r"^```(?:json)?\s*", "", t, flags=re.IGNORECASE)
        t = re.sub(r"\s*```\s*$", "", t)
    try:
        return json.loads(t)
    except json.JSONDecodeError:
        return None


def _violations_by_id(violations: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for v in violations:
        vid = v.get("violation_id")
        if vid is not None:
            out[str(vid)] = v
    return out


def _clauses_by_id(clauses: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(c.get("clause_id")): c for c in clauses if c.get("clause_id") is not None}


def _original_clause_text(clause: dict[str, Any] | None, violation: dict[str, Any] | None) -> str:
    if clause:
        t = (clause.get("text") or "").strip()
        if t:
            return t
    if violation:
        t = (violation.get("clause_text") or "").strip()
        if t:
            return t
    return "—"


def _violation_narrative(v: dict[str, Any] | None) -> str:
    if not v:
        return "—"
    parts = [
        str(v.get("title") or ""),
        str(v.get("description") or ""),
        str(v.get("remediation_hint") or ""),
    ]
    return " — ".join(p for p in parts if p).strip() or "—"


def _legal_reference(row: dict[str, Any]) -> str:
    fw = (row.get("framework") or "").strip()
    art = (row.get("article") or "").strip()
    if fw and art:
        return f"{fw} {art}"
    return (fw or art or "—").strip() or "—"


def _severity_rank(severity: str | None) -> int:
    if not severity:
        return 99
    return _SEVERITY_ORDER.get(str(severity).lower(), 50)


def _group_key(row: dict[str, Any]) -> str:
    """Same real clause_id → same group; missing clause_id → one group per violation."""
    cid = row.get("clause_id")
    if cid is None or str(cid).strip() == "":
        return f"__single__{row.get('violation_id') or id(row)}"
    return str(cid)


def _sort_group_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(rows, key=lambda r: (_severity_rank(r.get("severity")), r.get("priority") or 0))


def _pick_primary_row(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return min(rows, key=lambda r: (_severity_rank(r.get("severity")), r.get("priority") or 9999))


def _call_llm_enhanced(system: str, user_payload: dict[str, Any]) -> LlmEnhancedOutput | None:
    user_msg = json.dumps(user_payload, ensure_ascii=False)
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user_msg},
    ]
    raw = groq_chat_completion_content(messages, temperature=0.2)
    if not raw:
        return None
    payload = _parse_json_payload(raw)
    if not payload:
        return None
    try:
        return LlmEnhancedOutput.model_validate(payload)
    except Exception as exc:
        logger.warning("llm_enhanced_parse_failed", extra={"extra": {"error": str(exc)}})
        return None


def enhance_recommendation(
    template_row: dict[str, Any],
    violation: dict[str, Any] | None,
    clause: dict[str, Any] | None,
) -> dict[str, Any] | None:
    """
    Call LLM for one template row. Returns a new row dict with llm_v2 on success, else None.
    legal_rationale is always preserved from the template row (references stay grounded).
    """
    if not LLM_ENABLED:
        return None
    sev = template_row.get("severity") or (violation.get("severity") if violation else None)
    user_obj = {
        "original_clause": _original_clause_text(clause, violation),
        "violation": _violation_narrative(violation),
        "risk_level": str(sev or "—"),
        "legal_reference": _legal_reference(template_row),
        "template_rewrite": (template_row.get("rewritten_clause") or "").strip() or "—",
        "issue_description": (template_row.get("issue_description") or "").strip() or "—",
    }
    out = _call_llm_enhanced(_SYSTEM_SINGLE, user_obj)
    if not out:
        return None
    return {
        **template_row,
        "issue_description": out.risk_summary.strip(),
        "recommendation_text": out.clear_explanation.strip(),
        "rewritten_clause": out.improved_rewrite.strip(),
        "legal_rationale": (template_row.get("legal_rationale") or "").strip(),
        "generated_by": "llm_v2",
    }


def _enhance_merged_group(
    rows: list[dict[str, Any]],
    violations_by_id: dict[str, dict[str, Any]],
    clause: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if not LLM_ENABLED or len(rows) < 2:
        return None
    primary = _pick_primary_row(rows)
    vid0 = primary.get("violation_id")
    v0 = violations_by_id.get(str(vid0)) if vid0 is not None else None
    original = _original_clause_text(clause, v0)
    items = []
    for r in _sort_group_rows(rows):
        vid = r.get("violation_id")
        v = violations_by_id.get(str(vid)) if vid is not None else None
        items.append(
            {
                "violation": _violation_narrative(v),
                "risk_level": str(r.get("severity") or ""),
                "legal_reference": _legal_reference(r),
                "template_rewrite": (r.get("rewritten_clause") or "").strip() or "—",
                "issue_description": (r.get("issue_description") or "").strip() or "—",
            }
        )
    user_obj = {
        "merge_mode": True,
        "original_clause": original,
        "violations": items,
    }
    out = _call_llm_enhanced(_SYSTEM_MERGE, user_obj)
    if not out:
        return None
    rationales = [str(r.get("legal_rationale") or "").strip() for r in rows if r.get("legal_rationale")]
    merged_rationale = " | ".join(dict.fromkeys(r for r in rationales if r))
    vids = [str(r.get("violation_id") or "") for r in rows if r.get("violation_id")]
    if len(vids) > 1:
        note = "Violations agrégées (même clause) : " + ", ".join(vids)
        merged_rationale = f"{merged_rationale}\n\n{note}".strip() if merged_rationale else note

    rule_ids = [str(r.get("violation_rule_id") or "") for r in rows if r.get("violation_rule_id")]
    merged_rule = " | ".join(dict.fromkeys(r for r in rule_ids if r))[:128]

    return {
        "violation_id": primary.get("violation_id"),
        "clause_id": primary.get("clause_id"),
        "violation_rule_id": merged_rule or primary.get("violation_rule_id"),
        "framework": primary.get("framework"),
        "article": primary.get("article"),
        "severity": primary.get("severity"),
        "priority": min(int(r.get("priority") or 9999) for r in rows),
        "issue_description": out.risk_summary.strip(),
        "recommendation_text": out.clear_explanation.strip(),
        "rewritten_clause": out.improved_rewrite.strip(),
        "legal_rationale": merged_rationale,
        "generated_by": "llm_v2",
    }


def enhance_recommendation_rows(
    rows: list[dict[str, Any]],
    violations: list[dict[str, Any]],
    clauses: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    template_result → LLM → final_result.

    Groups rows by clause_id (null clause_id never merged with each other).
    """
    if not LLM_ENABLED or not rows:
        return rows

    v_by_id = _violations_by_id(violations)
    c_by_id = _clauses_by_id(clauses)

    # Preserve global order: sort group keys by first appearance index
    key_order: list[str] = []
    seen: set[str] = set()
    for row in rows:
        k = _group_key(row)
        if k not in seen:
            seen.add(k)
            key_order.append(k)

    groups: dict[str, list[dict[str, Any]]] = {k: [] for k in key_order}
    for row in rows:
        groups[_group_key(row)].append(row)

    final: list[dict[str, Any]] = []
    for key in key_order:
        chunk = groups[key]
        chunk = _sort_group_rows(chunk)
        clause = c_by_id.get(str(chunk[0].get("clause_id") or "")) if chunk[0].get("clause_id") else None

        if len(chunk) == 1:
            r0 = chunk[0]
            vid = r0.get("violation_id")
            v = v_by_id.get(str(vid)) if vid is not None else None
            cid = r0.get("clause_id")
            cl = c_by_id.get(str(cid)) if cid else None
            enhanced = enhance_recommendation(r0, v, cl)
            final.append(enhanced if enhanced else r0)
            continue

        merged = _enhance_merged_group(chunk, v_by_id, clause)
        if merged:
            final.append(merged)
        else:
            final.extend(chunk)

    return final
