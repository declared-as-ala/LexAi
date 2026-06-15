# Agent 3 — Evaluator: Complete Technical Report

> **Date completed**: 2026-04-20
> **Status**: ✅ DONE — fully integrated, syntax-clean, TypeScript-clean

---

## 1. What Is Agent 3?

Agent 3 is the **Legal Evaluation Engine** of the LegalTech AI platform. It sits immediately after Agent 2 (NLP Analyzer) in the pipeline and answers one question:

> *"Is this contract legally compliant — and if not, exactly which articles does it violate?"*

Agent 3 is **entirely rule-based**. It requires no machine learning model, no GPU, and no training data. It works by matching the flags and labels already computed by Agent 2 against a library of legal rules stored in JSON files.

---

## 2. Where Does the "Dataset" Come From?

Agent 3 does not use a machine learning dataset in the traditional sense. Its "dataset" is a **curated library of legal rules** drawn from four official legal sources:

---

### 2.1 LNPDP — Loi Organique n°2004-63 (Tunisia)

**Source**: *Loi organique n° 2004-63 du 27 juillet 2004 portant sur la protection des données à caractère personnel*, published in the Journal Officiel de la République Tunisienne (JORT).

This is the **primary legal framework** — Tunisian national law. It is the most important framework (weight = 45% of the global score) because every contract processed on Tunisian territory is subject to it.

**Articles extracted and encoded as rules:**

| Rule ID | Article | What it checks | Severity | Mandatory |
|---------|---------|---------------|----------|-----------|
| `lnpdp_art3_definitions` | Art. 3 | Contract defines "responsable du traitement" and "sous-traitant" | medium | ✅ |
| `lnpdp_art5_legitimacy` | Art. 5 | Processing has a legal basis (consent, contract, legal obligation) | high | ✅ |
| `lnpdp_art7_purpose` | Art. 7 | Processing purpose is explicitly stated and limited | high | ✅ |
| `lnpdp_art8_proportionality` | Art. 8 | Data collection is not excessive relative to the stated purpose | high | ❌ |
| `lnpdp_art14_consent` | Art. 14 | Consent mechanism is clearly described | high | ✅ |
| `lnpdp_art22_data_subject_rights` | Art. 22 | Data subjects' rights (access, opposition) are described | high | ✅ |
| `lnpdp_art23_retention` | Art. 23 | Retention period is explicitly stated | high | ✅ |
| `lnpdp_art24_rectification` | Art. 24-25 | Right to rectification and opposition is mentioned | medium | ❌ |
| `lnpdp_art28_special_categories` | Art. 28 | Special category data (health, biometric) has heightened protection | critical | ❌ |
| `lnpdp_art29_security` | Art. 29 | Technical and organisational security measures are described | high | ✅ |
| `lnpdp_art30_subprocessor` | Art. 30 | Sub-processor clause is present if data is shared with third parties | high | ✅ |
| `lnpdp_art36_declaration` | Art. 36 | INPDP declaration obligation is mentioned | high | ✅ |
| `lnpdp_art39_transfer` | Art. 39 | Cross-border data transfers have appropriate safeguards | critical | ❌ |
| `lnpdp_art45_dpo` | Art. 45-46 | DPO (Délégué à la Protection des Données) is designated | medium | ❌ |
| `lnpdp_art52_sanctions` | Art. 52-57 | Contractual sanctions for data breaches are described | low | ❌ |

**Total**: 15 rules — 9 mandatory, 2 critical, 9 high severity.

---

### 2.2 GDPR — Règlement Général sur la Protection des Données (EU 2016/679)

**Source**: Official text of the GDPR (Regulation (EU) 2016/679), available on EUR-Lex (eur-lex.europa.eu). Also used: the CNIL (Commission Nationale de l'Informatique et des Libertés) model Data Processing Agreement (DPA), which lists the 8 mandatory clauses required under Art. 28 GDPR for data processor contracts.

**Why GDPR applies to Tunisian contracts**: GDPR applies whenever:
- The data controller or processor is established in the EU
- The data subjects are EU citizens
- Cross-border data transfer between Tunisia and EU territory is present
- A Tunisian company processes data on behalf of an EU company

Weight in global score = **30%** (active only when `gdpr_relevant` or `unlawful_cross_border_transfer` flag is detected).

**Important note**: Tunisia does **not** have an EU adequacy decision as of 2026. This means any Tunisia ↔ EU data transfer requires a Standard Contractual Clause (SCC/CCT) or Binding Corporate Rules (BCR), which are checked by `gdpr_art44_international_transfer`.

**Articles encoded as rules:**

| Rule ID | Article | What it checks | Severity |
|---------|---------|---------------|----------|
| `gdpr_art5_principles` | Art. 5 | 7 GDPR principles present (lawfulness, purpose limitation, minimisation…) | high |
| `gdpr_art6_lawfulness` | Art. 6 | Legal basis for processing is explicitly stated | high |
| `gdpr_art13_transparency` | Art. 13 | Transparency notice / privacy policy is referenced | high |
| `gdpr_art17_erasure` | Art. 17 | Right to erasure ("right to be forgotten") is described | medium |
| `gdpr_art20_portability` | Art. 20 | Data portability right is mentioned | low |
| `gdpr_art25_privacy_by_design` | Art. 25 | Privacy by design and by default is committed to | medium |
| `gdpr_art28_processor_contract` | Art. 28 | All 8 mandatory DPA sub-clauses are present | critical |
| `gdpr_art32_security` | Art. 32 | Security measures proportional to risk are described | high |
| `gdpr_art33_breach_notification` | Art. 33-34 | 72-hour breach notification obligation is included | high |
| `gdpr_art35_dpia` | Art. 35 | DPIA (Data Protection Impact Assessment) commitment for high-risk processing | medium |
| `gdpr_art44_international_transfer` | Art. 44-49 | International transfer mechanism (SCC/BCR/derogation) is present | critical |
| `gdpr_art82_liability` | Art. 82 | Liability and compensation clauses are present | medium |

**Total**: 12 rules — 7 mandatory, 2 critical, 5 high severity.

---

### 2.3 ISO 27001:2022 — Information Security Management

**Source**: ISO/IEC 27001:2022 standard (restructured Annex A — 4 themes, 93 controls). The 2022 edition introduced new controls including 5.23 (cloud security), 8.10 (data deletion), and 8.34 (privacy protection in information systems).

Weight in global score = **15%** (active when `data_processing` label or `missing_security_measures` flag is detected).

**Controls encoded as rules:**

| Rule ID | Control | Severity |
|---------|---------|----------|
| `iso27001_a5_1_policies` | 5.1 — Information security policies | medium |
| `iso27001_a5_19_supplier_security` | 5.19 — Information security in supplier relationships | medium |
| `iso27001_a5_20_supplier_agreements` | 5.20 — Addressing information security within supplier agreements | high |
| `iso27001_a5_23_cloud_security` | 5.23 — Information security for use of cloud services | medium |
| `iso27001_a8_asset_classification` | 8.2 — Asset classification | medium |
| `iso27001_a8_10_data_deletion` | 8.10 — Information deletion | high |
| `iso27001_a8_24_cryptography` | 8.24 — Use of cryptography | high |
| `iso27001_a8_25_secure_development` | 8.25 — Secure development lifecycle | medium |
| `iso27001_a8_34_privacy_pia` | 8.34 — Privacy and protection of personally identifiable information | medium |
| `iso27001_a9_access_control` | 9.1 — Access control policy | high |
| `iso27001_a6_incident_management` | 6.8 — Information security event reporting | high |
| `iso27001_a5_31_compliance` | 5.31 — Legal, statutory, regulatory, contractual requirements | medium |

**Total**: 12 rules — 4 mandatory, 0 critical, 5 high severity.

---

### 2.4 ISO 9001:2015 — Quality Management (Service Contracts)

**Source**: ISO 9001:2015 standard sections 4, 6, 7, 8.

Weight in global score = **10%** (active only when `obligation` or `warranty` labels are detected — i.e., service contracts).

**5 rules** covering: scope definition, SLA commitments, non-conformity management, audit rights, customer satisfaction.

---

### 2.5 Mandatory Clause Checklist

**Source**: Cross-referenced from LNPDP Art. 3/5/7/14/22/23/29/30/36, GDPR Art. 28 (CNIL model DPA), and standard legal practice for Tunisian data processing agreements.

**22 mandatory clause definitions** with detection logic (by label, flag, or keyword). Organised into checklists per contract type:

| Contract type | Mandatory clauses | GDPR adds | Cross-border adds |
|---------------|-------------------|-----------|-------------------|
| `data_processing` | 9 | 5 | 2 |
| `service` | 7 | 3 | 2 |
| `employment` | 5 | 2 | — |
| `nda` | 4 | 2 | — |
| `commercial` | 4 | 2 | 2 |

---

### 2.6 Reference Datasets (Not Used Directly in Agent 3, Documented for Agent 2 V2)

These are publicly available NLP datasets referenced in `datasets_reference.json`:

| Dataset | Language | Use case |
|---------|----------|----------|
| **CUAD** (Contract Understanding Atticus Dataset) | English | 41 clause types taxonomy — used as reference for label design |
| **LEDGAR** | EN/FR | 60k contract provisions — could augment Agent 2 training |
| **EUR-Lex** | French | GDPR official text, Standard Contractual Clauses (Decision 2021/914) |
| **CNIL DPA model** | French | 8 mandatory Art. 28 clauses — used directly to write GDPR rules |
| **MAPA project** (EU H2020) | Multilingual | Legal NLP annotations — reference for entity types |
| **LexGLUE** | English | Legal NLP benchmark |
| **CamemBERT / XLM-RoBERTa** | FR/Multilingual | Pre-trained models already used by Agent 2 |

---

## 3. What Was Built — Technical Detail

### 3.1 Rule Matching Engine (`app/legal/rule_engine.py`, 213 lines)

The engine loads all 44 rules at startup from four JSON files. For each document (passed as a list of clause dicts from Agent 2), it:

**Step 1 — Determine active frameworks**

Checks which frameworks apply to this specific document based on its flags and labels:
- LNPDP: always active
- GDPR: active if `gdpr_relevant` or `unlawful_cross_border_transfer` flags are present, OR `data_processing` label
- ISO 27001: active if `data_processing` label or security-related flags
- ISO 9001: active if `obligation` or `warranty` labels (service contracts)

**Step 2 — Rule matching with specific-flag priority**

Each rule has `trigger_flags` and `trigger_labels`. The engine separates trigger flags into two categories:

- **Specific flags** (problem-indicating): `missing_retention_period`, `missing_consent_mechanism`, `missing_data_subject_rights`, `missing_security_measures`, `missing_dpo_reference`, `unlawful_cross_border_transfer`, `excessive_data_collection`
- **Context flags** (informational): `lnpdp_relevant`, `gdpr_relevant`

Matching logic:
- If a rule has specific flags → the clause **must** have at least one specific flag (AND label match)
- If a rule has only context flags → skip it as a clause-level violation (handled by missing-clause detection instead)
- Each rule fires **at most once per document** (first matching clause becomes the violation's `clause_id`)

This prevents context-only rules from generating false violations on every LNPDP-relevant document.

**Step 3 — Missing mandatory clause detection**

Separately from violations, the engine infers the contract type from labels (`data_processing`, `confidentiality`, `obligation`, etc.) and checks whether each mandatory clause is present using three detection methods:
1. Label match (e.g., `definition` label = role_definitions clause present)
2. Keyword match (e.g., "responsable du traitement" in text = role defined)
3. Flag match (e.g., `lnpdp_relevant` flag on a definitions clause)

Missing clause keys are reported separately from violations.

---

### 3.2 Scoring Engine (`app/legal/scorer.py`, 87 lines)

Takes the list of violations and active frameworks, returns scores.

**Per-framework score formula:**
```
framework_score(F) = max(0, 100 - Σ severity_weight(v) for v in violations[F])

severity_weights:
  critical → 30 points deducted
  high     → 20 points deducted
  medium   → 10 points deducted
  low      →  5 points deducted
```

**Global weighted score formula:**
```
global_score = Σ(score(F) × weight(F)) / Σ(weight(F) for active F)

Framework weights:
  LNPDP    → 45%
  GDPR     → 30%
  ISO27001 → 15%
  ISO9001  → 10%
```

**Litigation risk from global score:**
```
score < 40  → CRITICAL
score < 60  → HIGH
score < 80  → MEDIUM
score ≥ 80  → LOW
```

---

### 3.3 Database Model (`app/db/models/evaluation.py`)

New table `evaluations` with one row per document (UNIQUE constraint on `document_id`):

| Column | Type | Content |
|--------|------|---------|
| `global_score` | Float | 0–100 |
| `litigation_risk` | String(16) | low/medium/high/critical |
| `lnpdp_score` | Float | LNPDP framework score |
| `gdpr_score` | Float | GDPR framework score |
| `iso27001_score` | Float | ISO 27001 score |
| `iso9001_score` | Float | ISO 9001 score |
| `violations_json` | Text | JSON array of all violation objects |
| `missing_clauses_json` | Text | JSON array of missing clause keys |
| `active_frameworks_json` | Text | JSON array of active framework names |
| `violation_counts_json` | Text | JSON dict of per-framework counts |
| `evaluated_at` | DateTime | When evaluation ran |

Migration: `alembic/versions/0005_agent3_evaluation.py` (chain: 0003 → 0004 → **0005**)

---

### 3.4 Celery Task (`app/tasks/evaluation.py`, 176 lines)

Task name: `app.tasks.evaluation.run_evaluation`

Pipeline stages and document progress:
```
0%  → evaluating / "Starting legal evaluation…"
30% → eval_rules / "Matching legal rules…"
60% → eval_scoring / "Computing compliance scores…"
85% → eval_persisting / "Saving evaluation…"
100% → eval_completed / "Evaluation complete — X violations — score Y/100"
```

**Auto-chain**: `run_nlp_analysis_sync()` calls `enqueue_evaluation(document_id)` immediately after the NLP task completes. No manual trigger needed.

**Fallback**: if Celery broker is unavailable, `enqueue_evaluation()` falls back to synchronous execution.

**Document status lifecycle** (extended):
```
queued → extracting → extracted → analyzing → analyzed → evaluating → evaluated
                                                                    ↘ failed
```

---

### 3.5 REST API (`app/api/routes/evaluation.py`, 128 lines)

| Method | Endpoint | Response |
|--------|----------|----------|
| `GET` | `/documents/{id}/evaluation` | Full evaluation with all violations |
| `GET` | `/documents/{id}/evaluation/summary` | Scores only, no violation text |
| `POST` | `/documents/{id}/evaluate` | Manually trigger re-evaluation (202 Accepted) |

The manual trigger accepts documents in `analyzed` or `evaluated` status — useful for re-running after legal rules are updated.

---

### 3.6 LangGraph Node (`app/workflows/evaluate_node.py`)

Node `evaluate_document` added to the graph after `nlp_analyze_document`:

```
validate_input → extract_document → nlp_analyze_document → evaluate_document → END
```

Reads `clauses` from `AnalysisState`, writes `findings` (violation dicts) and `scores` (global score, framework scores, litigation risk) back into state.

---

### 3.7 Frontend Components

**`EvaluationViewer.tsx`** (218 lines) renders:

1. **Score gauge** — SVG circular progress with score 0–100, color-coded (green/amber/orange/red)
2. **Framework bars** — per-framework score bars with violation count badges
3. **Stats row** — total violations / missing clauses / active frameworks
4. **Missing clauses panel** — amber tag cloud of missing mandatory clause keys
5. **Violation cards** — sorted by severity (critical first), each card shows:
   - Framework badge + article reference
   - Severity chip
   - Title and description
   - Truncated clause text (excerpt from document)
   - Remediation hint with lightbulb icon

**`UploadPage.tsx`** updated:
- `IN_PROGRESS` now includes `"evaluating"` (polling continues during Agent 3)
- Fetches evaluation when `status === "evaluated"`
- Shows `EvaluationViewer` below `AnalysisViewer` when evaluation is available
- Clears `selectedEvaluation` on document change or delete

---

## 4. Data Flow Summary

```
Agent 2 output (clause list):
[
  {
    "clause_id": "c-001",
    "labels": ["data_processing"],
    "compliance_flags": ["lnpdp_relevant", "missing_retention_period"],
    ...
  }
]
          │
          ▼
rule_engine.evaluate(clauses)
  → active_frameworks: ["LNPDP", "GDPR", "ISO27001"]
  → violations: [
      { rule_id: "lnpdp_art23_retention", framework: "LNPDP", severity: "high", ... },
      { rule_id: "gdpr_art32_security", framework: "GDPR", severity: "high", ... }
    ]
  → missing_clause_keys: ["subprocessor_clause", "breach_notification_procedure"]
          │
          ▼
scorer.compute_scores(violations, active_frameworks)
  → framework_scores: { LNPDP: 60.0, GDPR: 80.0, ISO27001: 70.0 }
  → global_score: 68.5
  → litigation_risk: "medium"
          │
          ▼
DB: evaluations table (one row per document)
          │
          ▼
GET /documents/{id}/evaluation → JSON response
          │
          ▼
EvaluationViewer renders score gauge + violations
```

---

## 5. What Agent 3 Does NOT Do

| Capability | Status | Who does it |
|-----------|--------|-------------|
| Rewrite non-compliant clauses | ❌ | Agent 4 (planned) |
| Classify text semantically | ❌ | Agent 2 (done) |
| Use an LLM | ❌ | Agent 4 V2 |
| Learn from feedback | ❌ | Future V3 |
| Arabic language rules | ❌ | V2 scope |
| ISO 9001 full coverage | Partial | V2 scope |

---

## 6. How to Update Legal Rules (No Code Changes Needed)

The rule system is designed so that legal teams can update rules without touching Python code:

1. Open `backend/app/legal/rules/lnpdp.json` (or gdpr/iso27001/iso9001)
2. Add or modify a rule following the schema:
   ```json
   {
     "rule_id": "lnpdp_art_NEW",
     "article": "Art. XX",
     "framework": "LNPDP",
     "title": "...",
     "description": "...",
     "trigger_flags": ["missing_retention_period"],
     "trigger_labels": ["data_processing"],
     "severity": "high",
     "mandatory": true,
     "remediation_hint": "..."
   }
   ```
3. Add a matching template in `templates/recommendations_fr.json`
4. Restart the backend — rules are loaded on every Celery task execution

No Alembic migration, no Python changes, no retraining needed.

---

## 7. Files Created / Modified

### New files

| Path | Lines | Purpose |
|------|-------|---------|
| `backend/app/legal/rule_engine.py` | 213 | Rule matching engine |
| `backend/app/legal/scorer.py` | 87 | Scoring formula |
| `backend/app/legal/rules/lnpdp.json` | 272 | 15 LNPDP rules |
| `backend/app/legal/rules/gdpr.json` | 272 | 12 GDPR rules |
| `backend/app/legal/rules/iso27001.json` | 193 | 12 ISO 27001 rules |
| `backend/app/legal/rules/iso9001.json` | 88 | 5 ISO 9001 rules |
| `backend/app/legal/weights.json` | 49 | Framework weights + thresholds |
| `backend/app/legal/mandatory_clauses.json` | 329 | 22 mandatory clause definitions |
| `backend/app/legal/templates/recommendations_fr.json` | 369 | 24 French rewrite templates (Agent 4) |
| `backend/app/db/models/evaluation.py` | — | SQLAlchemy model |
| `backend/app/schemas/evaluation.py` | — | Pydantic schemas |
| `backend/app/api/routes/evaluation.py` | 128 | REST endpoints |
| `backend/app/tasks/evaluation.py` | 176 | Celery task |
| `backend/app/workflows/evaluate_node.py` | — | LangGraph node |
| `backend/alembic/versions/0005_agent3_evaluation.py` | — | DB migration |
| `frontend/src/components/EvaluationViewer.tsx` | 218 | Evaluation UI component |

### Modified files

| Path | Change |
|------|--------|
| `backend/app/core/config.py` | Added Agent 3 status/stage constants |
| `backend/app/db/models/__init__.py` | Exported `Evaluation` |
| `backend/app/main.py` | Registered evaluation router |
| `backend/app/tasks/nlp_analysis.py` | Chains `enqueue_evaluation()` after NLP |
| `backend/app/workflows/graph.py` | Added `evaluate_document` node |
| `frontend/src/types/documents.ts` | Added `EvaluationResponse`, `ViolationSchema`, new statuses |
| `frontend/src/api/documents.ts` | Added `getDocumentEvaluation()` |
| `frontend/src/pages/UploadPage.tsx` | Fetches and renders evaluation |
