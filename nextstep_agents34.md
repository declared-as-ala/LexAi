# Agent 3 & Agent 4 — Complete Plan

> **Date**: 2026-04-20
> **Status**: Agent 1 ✅ DONE | Agent 2 ✅ DONE | Agent 3 🔨 NEXT | Agent 4 📋 PLANNED

---

## Current State

| Agent | Role | Status | Output |
|-------|------|--------|--------|
| Agent 1 | Extractor | ✅ COMPLETE | `normalized_text`, `structure_json` |
| Agent 2 | NLP Analyzer | ✅ COMPLETE | `clauses[]`, `entities[]`, `labels[]`, `risk_level`, `compliance_score` |
| Agent 3 | Evaluator | ❌ NOT STARTED | `evaluation`, `framework_scores`, `violations[]` |
| Agent 4 | Recommender | ❌ NOT STARTED | `recommendations[]`, `rewritten_clauses[]` |

**What Agent 2 currently produces per document:**
```json
{
  "document_id": 42,
  "risk_level": "high",
  "compliance_score": 60.0,
  "clauses": [
    {
      "clause_id": "c-001",
      "text": "...",
      "labels": ["data_processing", "gdpr_relevant"],
      "entities": [{"text": "données personnelles", "label": "DATA_CATEGORY"}],
      "confidence": 0.91,
      "compliance_flags": ["missing_retention_period", "lnpdp_relevant"]
    }
  ]
}
```

**What is missing:** Agent 2's `compliance_score` is a coarse heuristic (deduction per flag count). Agent 3 must replace/extend this with a structured, explainable, per-framework evaluation grounded in actual legal articles.

---

## Agent 3 — Goal

**Agent 3 (Evaluator)** transforms raw NLP clause analysis into a structured legal compliance evaluation.

### Primary Outputs

1. **Per-framework compliance scores** (LNPDP, GDPR, ISO 27001, ISO 9001) — 0–100
2. **Global contract compliance score** — weighted average of frameworks
3. **Litigation risk level** — `low | medium | high | critical`
4. **Violation records** — each mapped to a legal article, severity, and affected clause
5. **Missing clause alerts** — required clauses absent from the document

### What Agent 3 Does NOT Do
- It does not rewrite clauses (that is Agent 4)
- It does not classify text (that is Agent 2)
- It does not require an LLM in V1 (pure rule-based)

---

## Agent 4 — Goal

**Agent 4 (Recommender)** takes Agent 3 violations and generates actionable, legally grounded recommendations.

### Primary Outputs

1. **Per-violation recommendations** — what to change and why
2. **Rewritten clause templates** — drop-in replacement text (French)
3. **Legal rationale** — which article requires the change
4. **Priority ranking** — critical → high → medium → low
5. **Export-ready report** — JSON + human-readable summary

### What Agent 4 Does NOT Do
- It does not score compliance (Agent 3)
- It does not analyze semantics (Agent 2)
- V1 uses templates only, not an LLM

---

## Requirements

### Functional Requirements

#### Agent 3
- [ ] Evaluate each clause against LNPDP 2004-63 articles
- [ ] Evaluate each clause against GDPR articles (for cross-border contracts)
- [ ] Evaluate each clause against ISO 27001 controls (for data security clauses)
- [ ] Evaluate document-level: detect missing mandatory clauses (e.g., no DPO clause, no retention clause)
- [ ] Produce a per-framework score (0–100) and global weighted score
- [ ] Map each violation to: framework, article, severity, affected_clause_id, description
- [ ] Determine litigation risk from violation severity distribution
- [ ] Store evaluation result in DB and expose via REST API
- [ ] Trigger automatically after Agent 2 completes (Celery chain)

#### Agent 4
- [ ] For each violation from Agent 3, select or generate a recommendation
- [ ] Use a template library keyed by `(framework, violation_type)` pairs
- [ ] Slot-fill templates with entities extracted by Agent 2 (data controller name, retention period, etc.)
- [ ] Rank recommendations by severity
- [ ] Store recommendations in DB and expose via REST API
- [ ] Trigger automatically after Agent 3 completes (Celery chain)
- [ ] V2: replace template generation with Mistral 7B local LLM

### Technical Requirements
- Python 3.11+, FastAPI, SQLAlchemy 2.0, Celery 5, PostgreSQL 16
- No new ML model needed for V1 (rule-based)
- Alembic migrations for new tables
- Pydantic schemas for all API I/O
- LangGraph nodes for both agents (extending existing graph)
- Frontend components in React 18 + TypeScript + Tailwind CSS

### Legal Requirements
- Legal reference library must be maintainable (JSON files, not hardcoded)
- Each rule must cite its source article explicitly
- Scores must be explainable (breakdown visible to user)
- System must distinguish LNPDP-only vs GDPR-only vs both

### Performance Requirements
- Agent 3 evaluation: < 2 seconds per document (rule-based, no model inference)
- Agent 4 template generation: < 1 second per document (V1 template lookup)
- Both agents must be non-blocking (run in Celery worker)
- Polling interval (2s) sufficient — no WebSocket needed for V1

---

## Architecture Proposal

### Processing Flow (Extended)

```
Document uploaded
       │
  [Agent 1] Extract text
       │
  [Agent 2] NLP analysis → clauses + flags + risk_level
       │
  [Agent 3] Legal evaluation → violations + framework_scores
       │
  [Agent 4] Recommendations → rewrites + action_items
       │
  Frontend dashboard
```

### Celery Chain

```python
# backend/app/tasks/pipeline.py
chain(
    nlp_analysis_task.s(document_id),
    evaluate_document_task.s(),   # Agent 3
    recommend_for_document_task.s()  # Agent 4
)
```

Each task receives the document_id and reads its inputs from the DB (not from the previous task's return value — avoids large Celery payloads).

### LangGraph Extension

```
validate_input → extract_document → analyze_document → evaluate_document → recommend_clauses → END
```

New nodes:
- `evaluate_document` in `backend/app/workflows/evaluate_node.py`
- `recommend_clauses` in `backend/app/workflows/recommend_node.py`

### Legal Reference System

Rules live in JSON files (not hardcoded in Python). This allows legal team to update rules without touching code.

```
backend/app/legal/
├── rules/
│   ├── lnpdp.json          # LNPDP 2004-63 rules
│   ├── gdpr.json           # GDPR articles
│   ├── iso27001.json       # ISO 27001 controls
│   └── iso9001.json        # ISO 9001 clauses
├── templates/
│   ├── recommendations_fr.json   # Recommendation templates (French)
│   └── recommendations_ar.json   # (future: Arabic)
└── weights.json            # Framework weights for global score
```

**Rule format (lnpdp.json example):**
```json
{
  "rules": [
    {
      "rule_id": "lnpdp_art23_retention",
      "article": "Art. 23",
      "framework": "LNPDP",
      "description": "La durée de conservation des données doit être précisée.",
      "trigger_flags": ["missing_retention_period"],
      "trigger_labels": ["data_processing"],
      "severity": "high",
      "required": true
    },
    {
      "rule_id": "lnpdp_art14_consent",
      "article": "Art. 14",
      "framework": "LNPDP",
      "description": "Le mécanisme de consentement doit être explicité.",
      "trigger_flags": ["missing_consent_mechanism"],
      "trigger_labels": ["data_processing"],
      "severity": "high",
      "required": true
    },
    {
      "rule_id": "lnpdp_art29_security",
      "article": "Art. 29",
      "framework": "LNPDP",
      "description": "Les mesures de sécurité techniques doivent être décrites.",
      "trigger_flags": ["missing_security_measures"],
      "trigger_labels": ["data_processing"],
      "severity": "medium",
      "required": false
    }
  ]
}
```

**Framework weights (weights.json):**
```json
{
  "LNPDP":    { "weight": 0.45, "applies_when": "always" },
  "GDPR":     { "weight": 0.30, "applies_when": "cross_border_transfer_detected" },
  "ISO27001": { "weight": 0.15, "applies_when": "data_processing_detected" },
  "ISO9001":  { "weight": 0.10, "applies_when": "service_contract_detected" }
}
```

### Scoring Formula

```
framework_score(F) = 100 - Σ(severity_weight(v) for v in violations[F])

severity_weight:
  critical → 30
  high     → 20
  medium   → 10
  low      →  5

global_score = Σ(framework_score(F) × weight(F)) / Σ(weight(F) for active F)
global_score = max(0, min(100, global_score))

litigation_risk:
  global_score < 40  → critical
  global_score < 60  → high
  global_score < 80  → medium
  else               → low
```

### Database Schema

#### `evaluations` table

```python
class Evaluation(Base):
    __tablename__ = "evaluations"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"), unique=True)
    global_score: Mapped[float | None]
    litigation_risk: Mapped[str | None]          # low|medium|high|critical
    lnpdp_score: Mapped[float | None]
    gdpr_score: Mapped[float | None]
    iso27001_score: Mapped[float | None]
    iso9001_score: Mapped[float | None]
    missing_clauses_json: Mapped[str | None]     # JSON list of missing mandatory clauses
    violations_json: Mapped[str | None]          # JSON list of Violation objects
    evaluated_at: Mapped[datetime | None]
    created_at: Mapped[datetime] = mapped_column(default=func.now())
```

#### `recommendations` table

```python
class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"))
    clause_id: Mapped[str | None]                # e.g., "c-001"
    violation_rule_id: Mapped[str | None]        # e.g., "lnpdp_art23_retention"
    framework: Mapped[str | None]
    article: Mapped[str | None]
    severity: Mapped[str | None]
    priority: Mapped[int | None]                 # 1=highest
    issue_description: Mapped[str | None]
    recommendation_text: Mapped[str | None]      # What to do
    rewritten_clause: Mapped[str | None]         # Drop-in replacement (French)
    legal_rationale: Mapped[str | None]
    generated_by: Mapped[str | None]             # "template_v1" or "mistral_7b"
    created_at: Mapped[datetime] = mapped_column(default=func.now())
```

### API Endpoints

#### Agent 3

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/documents/{id}/evaluation` | Get evaluation result |
| POST | `/documents/{id}/evaluate` | Trigger evaluation manually |

**Response schema:**
```json
{
  "document_id": 42,
  "global_score": 58.5,
  "litigation_risk": "high",
  "framework_scores": {
    "LNPDP": 55.0,
    "GDPR": 60.0,
    "ISO27001": 70.0
  },
  "violations": [
    {
      "violation_id": "v-001",
      "rule_id": "lnpdp_art23_retention",
      "framework": "LNPDP",
      "article": "Art. 23",
      "severity": "high",
      "clause_id": "c-003",
      "description": "Durée de conservation non précisée"
    }
  ],
  "missing_clauses": ["dpo_designation", "data_subject_rights"],
  "evaluated_at": "2026-04-20T14:30:00Z"
}
```

#### Agent 4

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/documents/{id}/recommendations` | Get all recommendations |
| POST | `/documents/{id}/recommend` | Trigger recommendation manually |

**Response schema:**
```json
{
  "document_id": 42,
  "total": 3,
  "recommendations": [
    {
      "id": 1,
      "priority": 1,
      "framework": "LNPDP",
      "article": "Art. 23",
      "severity": "high",
      "clause_id": "c-003",
      "issue_description": "La durée de conservation des données n'est pas précisée.",
      "recommendation_text": "Ajoutez une clause spécifiant la durée de conservation maximale des données personnelles.",
      "rewritten_clause": "Les données personnelles collectées seront conservées pendant une durée maximale de [DURÉE] à compter de [ÉVÉNEMENT_DÉCLENCHEUR]. À l'expiration de ce délai, les données seront supprimées ou anonymisées conformément à l'article 23 de la loi n°2004-63.",
      "legal_rationale": "L'article 23 de la LNPDP impose que la durée de conservation soit déterminée et proportionnée à la finalité du traitement.",
      "generated_by": "template_v1"
    }
  ]
}
```

### Recommendation Template Format

```json
{
  "templates": [
    {
      "rule_id": "lnpdp_art23_retention",
      "issue_description": "La durée de conservation des données n'est pas précisée.",
      "recommendation_text": "Ajoutez une clause spécifiant la durée maximale de conservation des données personnelles.",
      "rewritten_clause": "Les données personnelles collectées seront conservées pendant une durée maximale de {DURATION} à compter de {TRIGGER_EVENT}. À l'expiration de ce délai, les données seront supprimées ou anonymisées conformément à l'article 23 de la loi n°2004-63.",
      "legal_rationale": "L'article 23 de la LNPDP impose que la durée de conservation soit déterminée et proportionnée à la finalité du traitement.",
      "slots": {
        "DURATION": { "entity_label": "DURATION", "default": "[À PRÉCISER]" },
        "TRIGGER_EVENT": { "entity_label": "EVENT", "default": "la fin de la relation contractuelle" }
      }
    }
  ]
}
```

Slot-filling uses Agent 2 entities: if Agent 2 extracted a `DURATION` entity from the document, use it; otherwise fall back to the default placeholder.

---

## File Structure

### New Backend Files

```
backend/app/
├── legal/
│   ├── __init__.py
│   ├── rule_engine.py              # Loads rules, evaluates clauses → violations
│   ├── scorer.py                   # Computes framework + global scores
│   ├── recommender.py              # Template lookup + slot-fill
│   └── rules/
│       ├── lnpdp.json
│       ├── gdpr.json
│       ├── iso27001.json
│       └── iso9001.json
├── legal/templates/
│   └── recommendations_fr.json
├── db/models/
│   ├── evaluation.py               # Evaluation SQLAlchemy model
│   └── recommendation.py          # Recommendation SQLAlchemy model
├── schemas/
│   ├── evaluation.py               # Pydantic I/O schemas
│   └── recommendation.py
├── api/routes/
│   ├── evaluation.py               # GET/POST /documents/{id}/evaluation
│   └── recommendation.py          # GET/POST /documents/{id}/recommendations
├── tasks/
│   ├── evaluation.py               # Celery task: evaluate_document_task
│   └── recommendation.py          # Celery task: recommend_for_document_task
└── workflows/
    ├── evaluate_node.py            # LangGraph node
    └── recommend_node.py           # LangGraph node
```

### New Alembic Migrations

```
backend/alembic/versions/
├── 0005_agent3_evaluation.py       # Creates evaluations table
└── 0006_agent4_recommendations.py  # Creates recommendations table
```

### New Frontend Files

```
frontend/src/
├── types/
│   └── evaluation.ts               # EvaluationResponse, RecommendationResponse types
├── api/
│   └── evaluation.ts               # getEvaluation(), getRecommendations() API calls
└── components/
    ├── EvaluationScoreCard.tsx     # Global score + risk badge
    ├── FrameworkComplianceTable.tsx # Per-framework breakdown table
    ├── ViolationList.tsx           # List of violations with article refs
    └── RecommendationPanel.tsx     # Expandable recommendations with rewrite
```

---

## Document Status Lifecycle (Extended)

```
queued → extracting → extracted → analyzing → analyzed → evaluating → evaluated → recommending → complete
                   ↘ failed                ↘ failed               ↘ failed               ↘ failed
```

New statuses added to `Document.status`:
- `evaluating` — Agent 3 running
- `evaluated` — Agent 3 done
- `recommending` — Agent 4 running
- `complete` — all agents done

Frontend polling already handles arbitrary status strings — no polling changes needed.

---

## Frontend Components

### EvaluationScoreCard

Shows the global compliance score as a large circular gauge, risk level badge, and evaluated-at timestamp.

```
┌─────────────────────────────────────┐
│  Compliance Score          ⚠ HIGH   │
│                                     │
│         ◉ 58 / 100                  │
│                                     │
│  LNPDP ████████░░░░ 55%             │
│  GDPR  ████████████ 60%             │
│  ISO   ██████████░░ 70%             │
└─────────────────────────────────────┘
```

### ViolationList

Collapsible list. Each violation card shows: framework badge, article, severity chip, affected clause text (truncated), full description.

```
┌─────────────────────────────────────┐
│ LNPDP  Art. 23  ● HIGH              │
│ Durée de conservation non précisée  │
│ → Clause c-003: "Les données..."    │
└─────────────────────────────────────┘
```

### RecommendationPanel

Tabs: Summary | Rewritten Clauses | Export

Each recommendation expandable accordion:
```
▼ [1] Art. 23 — Retention Period (HIGH)
  Issue: Durée de conservation non précisée.
  Action: Ajoutez une clause spécifiant...
  ─────────────────────────────────────
  Rewritten clause:
  "Les données personnelles collectées seront
   conservées pendant une durée maximale de
   [À PRÉCISER]..."
  ─────────────────────────────────────
  Legal basis: Art. 23 LNPDP 2004-63
```

---

## TODO List

### Phase 1 — Agent 3: Rule Engine & Scoring (Week 1–2)

- [ ] Create `backend/app/legal/` package
- [ ] Write `lnpdp.json` rules (target: 15 rules covering Arts. 4, 14, 23, 24, 25, 29, 30, 36)
- [ ] Write `gdpr.json` rules (target: 8 rules covering Arts. 5, 6, 13, 17, 25, 28, 32, 44)
- [ ] Write `iso27001.json` rules (target: 6 controls: A.8, A.9, A.10, A.12, A.13, A.18)
- [ ] Implement `rule_engine.py`: load rules, iterate clauses, match triggers, produce violations
- [ ] Implement `scorer.py`: per-framework score, global weighted score, litigation risk
- [ ] Create `evaluation.py` SQLAlchemy model
- [ ] Write Alembic migration `0005_agent3_evaluation.py`
- [ ] Create `schemas/evaluation.py` Pydantic schemas
- [ ] Create `api/routes/evaluation.py` endpoints
- [ ] Create `tasks/evaluation.py` Celery task
- [ ] Wire into Celery pipeline after `nlp_analysis_task`
- [ ] Create `workflows/evaluate_node.py` LangGraph node
- [ ] Update `workflows/graph.py` to include evaluation node

### Phase 2 — Agent 3: Missing Clause Detection (Week 2)

- [ ] Define mandatory clause checklist per contract type (data_processing, employment, service, nda)
- [ ] Implement document-level mandatory clause check in rule engine
- [ ] Contract type inference from Agent 2 labels (`contract_type:*`)
- [ ] Add `missing_clauses` to Evaluation DB + schema
- [ ] Surface missing clauses in frontend as a separate warning section

### Phase 3 — Agent 4: Recommendation Templates (Week 3)

- [ ] Write `recommendations_fr.json`: 1 template per rule (15 LNPDP + 8 GDPR + 6 ISO = 29 templates)
- [ ] Implement `recommender.py`: violation → template lookup → slot-fill with Agent 2 entities
- [ ] Create `recommendation.py` SQLAlchemy model
- [ ] Write Alembic migration `0006_agent4_recommendations.py`
- [ ] Create `schemas/recommendation.py` Pydantic schemas
- [ ] Create `api/routes/recommendation.py` endpoints
- [ ] Create `tasks/recommendation.py` Celery task
- [ ] Wire into Celery pipeline after `evaluate_document_task`
- [ ] Create `workflows/recommend_node.py` LangGraph node
- [ ] Update `workflows/graph.py` to include recommend node

### Phase 4 — Frontend Integration (Week 4)

- [ ] Add `EvaluationResponse` and `RecommendationResponse` to `types/evaluation.ts`
- [ ] Implement `api/evaluation.ts` (getEvaluation, getRecommendations API calls)
- [ ] Build `EvaluationScoreCard.tsx` with score gauge + risk badge
- [ ] Build `FrameworkComplianceTable.tsx` (per-framework score bars)
- [ ] Build `ViolationList.tsx` (collapsible violation cards)
- [ ] Build `RecommendationPanel.tsx` (accordion with rewritten clauses)
- [ ] Update `UploadPage.tsx` to render evaluation and recommendation panels
- [ ] Update polling to include `evaluating` and `recommending` in IN_PROGRESS
- [ ] Extend `DocumentStatusCard.tsx` with new statuses
- [ ] Update `QueueSummaryCards.tsx` with new status counts

---

## MVP Scope

The following constitutes a shippable MVP for Agents 3 and 4:

**MVP Definition:**
- Agent 3 evaluates data processing clauses against LNPDP + GDPR (the two primary frameworks)
- Agent 3 produces global score, LNPDP score, GDPR score, and violation list
- Agent 4 generates template-based recommendations for each violation (French only)
- Frontend shows score card, violation list, and recommendation panel
- Both agents run automatically in Celery pipeline
- No LLM required — rule-based and template-based only

**MVP Exclusions (V2):**
- ISO 27001 and ISO 9001 scoring
- Missing clause detection
- Arabic templates
- LLM-powered clause rewriting (Mistral 7B)
- PDF/DOCX export of recommendation report
- User-editable scores or feedback loop

---

## V2 Scope

After MVP ships and is validated:

1. **ISO 27001 / ISO 9001 scoring** — add rules JSON, wire into scorer
2. **Missing mandatory clause detection** — per contract type checklist
3. **LLM rewriting (Agent 4 V2)** — replace template lookup with Mistral 7B:
   - `POST /generate` local endpoint (Ollama)
   - Prompt: `"Réécris cette clause pour être conforme à {article} de la {framework}: {original_text}"`
   - Fallback to template if LLM unavailable
4. **Arabic language support** — `recommendations_ar.json` + RTL frontend
5. **Report export** — generate PDF report with all violations and recommendations
6. **User feedback loop** — thumbs up/down on recommendations feeds fine-tuning dataset
7. **Audit log** — track who evaluated which document, when, what changed

---

## Risks & Challenges

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Legal rules are wrong / outdated | Medium | High | Have a lawyer review lnpdp.json before demo |
| Rule matching too coarse (false positives) | High | Medium | Add `trigger_labels` + `trigger_flags` guards; require BOTH to match |
| Agent 2 flag accuracy < 90% → wrong violations | Medium | High | V1 uses only high-confidence flags; add confidence threshold in rule engine |
| LLM integration (V2) too slow for demo | High | Medium | Template fallback always available; LLM is optional in V2 |
| New DB columns break existing API contracts | Low | High | Add new columns nullable; existing API endpoints unaffected |
| Frontend over-cluttered with 4 new panels | Medium | Medium | Collapse evaluation + recommendations into tabbed view below extraction viewer |
| Docker build size grows (if Mistral added) | High | Medium | Keep Mistral behind feature flag; do not add to V1 Docker image |

---

## Final Recommendation

**Start with Agent 3, rule-based MVP only.**

Rationale:
- Agent 3 requires no new ML model — pure JSON rules + arithmetic scoring
- Produces immediate, visible value (compliance score + legal citations)
- Can be demoed in 2 weeks without Agent 4
- Agent 4 template-based is a 3-day add-on once Agent 3 is stable
- LLM rewriting (Mistral) should be V2 — do not block the MVP on it

**Implementation order:**
1. Write `lnpdp.json` + `gdpr.json` (Day 1–2) — get a lawyer to review
2. Implement `rule_engine.py` + `scorer.py` (Day 3–4)
3. DB migration + Celery task + API endpoints (Day 5)
4. Frontend EvaluationScoreCard + ViolationList (Day 6–7)
5. Agent 4 templates + RecommendationPanel (Day 8–10)
6. Integration testing end-to-end (Day 11–12)
7. ISO 27001 rules + missing clause detection (V2, after demo)

**The rule-based approach is the right call for a PFE demo:**
- Fully explainable (no black box)
- Easy to audit by the jury
- Directly tied to real legal articles
- No GPU required
- Extendable to LLM in V2 without architectural changes
