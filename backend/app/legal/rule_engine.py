"""Agent 3 — Rule Engine: loads legal rules from JSON, evaluates clauses, returns violations."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

_RULES_DIR = Path(__file__).parent / "rules"
_MANDATORY_FILE = Path(__file__).parent / "mandatory_clauses.json"

_RULE_FILES = ["lnpdp.json", "gdpr.json", "iso27001.json", "iso9001.json"]

# Flags that indicate a specific detected problem — these take priority in matching
_SPECIFIC_FLAGS = frozenset({
    "missing_retention_period",
    "missing_consent_mechanism",
    "missing_data_subject_rights",
    "missing_security_measures",
    "missing_dpo_reference",
    "unlawful_cross_border_transfer",
    "excessive_data_collection",
})


@dataclass
class Violation:
    violation_id: str
    rule_id: str
    framework: str
    article: str
    title: str
    description: str
    severity: str           # critical | high | medium | low
    clause_id: str | None   # None = document-level missing clause
    clause_text: str | None
    remediation_hint: str


@dataclass
class EvaluationResult:
    violations: list[Violation] = field(default_factory=list)
    missing_clause_keys: list[str] = field(default_factory=list)
    active_frameworks: list[str] = field(default_factory=list)


def _load_all_rules() -> list[dict]:
    rules: list[dict] = []
    for fname in _RULE_FILES:
        path = _RULES_DIR / fname
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            rules.extend(data.get("rules", []))
    return rules


def _load_mandatory() -> dict:
    if _MANDATORY_FILE.exists():
        return json.loads(_MANDATORY_FILE.read_text(encoding="utf-8"))
    return {}


def _all_flags(clauses: list[dict]) -> set[str]:
    flags: set[str] = set()
    for c in clauses:
        flags.update(c.get("compliance_flags", []))
    return flags


def _all_labels(clauses: list[dict]) -> set[str]:
    labels: set[str] = set()
    for c in clauses:
        labels.update(c.get("labels", []))
    return labels


def _is_framework_active(framework: str, all_flags: set[str], all_labels: set[str], weights_cfg: dict) -> bool:
    fw = weights_cfg.get("frameworks", {}).get(framework, {})
    applies_when = fw.get("applies_when", "")
    if applies_when == "always":
        return True
    fw_flags = set(fw.get("applies_when_flags", []))
    fw_labels = set(fw.get("applies_when_labels", []))
    return bool(fw_flags & all_flags) or bool(fw_labels & all_labels)


def _load_weights() -> dict:
    weights_file = Path(__file__).parent / "weights.json"
    if weights_file.exists():
        return json.loads(weights_file.read_text(encoding="utf-8"))
    return {}


def evaluate(clauses: list[dict]) -> EvaluationResult:
    """
    Evaluate a list of clause dicts (from Agent 2) against all legal rules.
    Returns violations and missing mandatory clause keys.
    """
    rules = _load_all_rules()
    mandatory_data = _load_mandatory()
    weights_cfg = _load_weights()

    doc_flags = _all_flags(clauses)
    doc_labels = _all_labels(clauses)

    # Determine active frameworks
    active_frameworks = [
        fw for fw in ["LNPDP", "GDPR", "ISO27001", "ISO9001"]
        if _is_framework_active(fw, doc_flags, doc_labels, weights_cfg)
    ]

    violations: list[Violation] = []
    fired_rules: set[str] = set()  # each rule fires at most once per document

    for rule in rules:
        rule_id = rule.get("rule_id", "")
        framework = rule.get("framework", "")

        # Only evaluate rules for active frameworks
        if framework not in active_frameworks:
            continue

        # Skip duplicate firing
        if rule_id in fired_rules:
            continue

        trigger_flags: set[str] = set(rule.get("trigger_flags", []))
        trigger_labels: set[str] = set(rule.get("trigger_labels", []))

        # Split trigger_flags into specific (problem-indicating) vs context (informational)
        specific_triggers = trigger_flags & _SPECIFIC_FLAGS

        # Rules with no specific flags are structural/presence checks —
        # they are handled by mandatory clause detection, not clause-level violations
        if not specific_triggers:
            continue

        # Find first clause that has the specific flag AND the required label
        matched_clause: dict | None = None
        for clause in clauses:
            clause_flags = set(clause.get("compliance_flags", []))
            clause_labels = set(clause.get("labels", []))

            specific_ok = bool(specific_triggers & clause_flags)
            labels_ok = (not trigger_labels) or bool(trigger_labels & clause_labels)

            if specific_ok and labels_ok:
                matched_clause = clause
                break

        if matched_clause is None:
            continue

        fired_rules.add(rule_id)
        v_id = f"v-{len(violations) + 1:03d}"
        violations.append(Violation(
            violation_id=v_id,
            rule_id=rule_id,
            framework=framework,
            article=rule.get("article", ""),
            title=rule.get("title", rule_id),
            description=rule.get("description", ""),
            severity=rule.get("severity", "medium"),
            clause_id=matched_clause.get("clause_id"),
            clause_text=matched_clause.get("text", "")[:300],
            remediation_hint=rule.get("remediation_hint", ""),
        ))

    # Missing mandatory clause detection
    missing_keys: list[str] = []
    clause_defs = mandatory_data.get("clause_definitions", {})
    checklists = mandatory_data.get("checklists_by_contract_type", {})

    # Infer contract type from labels
    contract_type = "data_processing" if "data_processing" in doc_labels else (
        "service" if "obligation" in doc_labels else
        "nda" if "confidentiality" in doc_labels else
        "employment" if "termination" in doc_labels else
        "commercial"
    )

    checklist = checklists.get(contract_type, {})
    mandatory_clause_keys: list[str] = checklist.get("mandatory_clauses", [])

    # Add GDPR keys if GDPR is active
    if "GDPR" in active_frameworks:
        mandatory_clause_keys += checklist.get("if_gdpr_applies_add", [])
    if "unlawful_cross_border_transfer" in doc_flags:
        mandatory_clause_keys += checklist.get("if_cross_border_add", [])

    all_clause_text = " ".join(c.get("text", "").lower() for c in clauses)
    all_labels_flat = doc_labels

    for clause_key in mandatory_clause_keys:
        clause_def = clause_defs.get(clause_key)
        if not clause_def:
            continue

        # Check if this clause type is present in the document
        detected_labels = set(clause_def.get("detected_by_labels", []))
        detected_keywords = [kw.lower() for kw in clause_def.get("detected_by_keywords", [])]

        label_present = bool(detected_labels & all_labels_flat)
        keyword_present = any(kw in all_clause_text for kw in detected_keywords)

        if not label_present and not keyword_present:
            missing_keys.append(clause_key)

    return EvaluationResult(
        violations=violations,
        missing_clause_keys=list(dict.fromkeys(missing_keys)),  # dedup, preserve order
        active_frameworks=active_frameworks,
    )
