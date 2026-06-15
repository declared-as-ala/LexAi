# LegalTech AI Platform — Execution Roadmap

> **Current state as of 2026-04-14**
> Agent 1 (Extractor) — COMPLETE ✅
> Agent 2 (NLP Analyzer) — COMPLETE ✅
> Agent 3 (Evaluator) — COMPLETE ✅
> Dataset — Downloaded ✅ (CUAD, LEDGAR, MAUD, GDPR Classification, CNIL FR, Unfair ToS in `data/raw/datasets/`)
> Legal refs — Created ✅ (LNPDP, GDPR, COC key articles in `data/raw/legal_refs/`)
> Agent 4 (Recommender) — NOT STARTED
> Dashboard UI — PARTIAL (Agents 1+2+3 viewer done, radar chart / full dashboard pending)

---

## What Was Built (Agents 1, 2 & 3)

### Agent 1 ✅
- PDF / DOCX / TXT / HTML extraction via provider pattern
- Celery async task with real-time progress
- Alembic migrations, DB models, full REST API
- Frontend: upload dropzone, history list, progress card, extraction viewer

### Agent 2 ✅
- `LanguageDetector` — fr/ar/en detection with Arabic char heuristic + langdetect
- `ClauseSegmenter` — 3-strategy: structure_json → regex article headings → paragraph breaks
- `EntityExtractor` — spaCy NER + rule-based patterns for ROLE, DATA_CATEGORY, LAW_REFERENCE, DURATION, JURISDICTION
- `ClauseClassifier` — zero-shot (legal-xlm-roberta-large) with keyword heuristic fallback; module-level pipeline cache prevents re-download per clause
- Celery task chains automatically after extraction success
- New statuses: `analyzing` → `analyzed`
- DB model: `nlp_analysis` table (migration 0003)
- API: `GET /documents/{id}/analysis`, `/clauses`, `/clauses/{cid}`, `POST /documents/{id}/analyze`
- Frontend: `AnalysisViewer` with clause cards, label/flag filters, entity badges, compliance flag highlights

### Agent 3 ✅
- `RuleEngine` — loads YAML rule files, matches rules against clauses by label + compliance flag
- `ComplianceScorer` — weighted score (critical=4, high=3, medium=2, low=1), overall + per-framework
- `RiskClassifier` — deterministic heuristic: critical/high/medium/low
- YAML rule files: `lnpdp.yaml` (5 rules), `gdpr.yaml` (6 rules), `coc.yaml` (3 rules) — 14 rules total
- Celery task chains automatically after NLP analysis success
- New statuses: `evaluating` → `evaluated`
- DB model: `compliance_evaluation` table (migration 0004)
- API: `GET /documents/{id}/evaluation`, `/evaluation/summary`, `/violations`, `POST /documents/{id}/evaluate`
- Frontend: `EvaluationViewer` — circular score gauge, risk badge, per-framework bar chart, violation cards with recommendations
- LangGraph: `evaluate_compliance` node added → full pipeline: validate → extract → nlp_analyze → evaluate → END

### Datasets Downloaded ✅
- `data/raw/datasets/cuad/` — 510 annotated contracts, 41 clause types
- `data/raw/datasets/ledgar/` — 80,000 legal provisions, 100 labels
- `data/raw/datasets/maud/` — 39,000 M&A clause QA pairs
- `data/raw/datasets/gdpr_classification/` — 499 GDPR-labeled texts
- `data/raw/datasets/cnil_fr/` — 831 French DPA decisions
- `data/raw/datasets/unfair_tos/` — 9,414 ToS clauses, 8 unfairness labels

### Legal Reference Texts Created ✅
- `data/raw/legal_refs/lnpdp/lnpdp_key_articles.json` — Arts. 6, 7, 23, 28, 46
- `data/raw/legal_refs/gdpr/gdpr_key_articles.json` — Arts. 5, 6, 13, 28, 32, 37
- `data/raw/legal_refs/coc/coc_key_articles.json` — Arts. 27, 107, 275, 318

---

## Priority Order (Remaining)

1. **Agent 4 — Recommender** (LLM clause rewriting — unblocks full dashboard)
2. **Dashboard UI** (dedicated page: radar chart, violations table, recommendations panel)
3. **Fine-tune Agent 2 models** (annotate 50 contracts, train CamemBERT)
4. **Infrastructure** (OCR, WebSockets, auth, audit logs)

---

## Step 4 — Build Agent 4: Recommender

### Goal
For each violation from Agent 3, generate a **compliant rewrite** and an **explanation** using a local LLM (Ollama/Mistral).

### LangGraph node
```
... → evaluate_compliance → recommend_improvements → END
```

### Submodules to implement

#### 4.1 `LegalContextRetriever` — `backend/app/services/recommendation/retriever.py`
- FAISS vector store, embed LNPDP + GDPR + COC articles at startup
- Model: `intfloat/multilingual-e5-base`
- Input: violation description + clause text
- Output: top-3 relevant legal articles (text snippets) injected into prompt

#### 4.2 `LLMClient` — `backend/app/services/recommendation/llm_client.py`
Local Ollama (no API cost, runs in Docker):
```python
httpx.post("http://ollama:11434/api/generate", json={
    "model": "mistral:7b-instruct",
    "prompt": "...",
    "stream": False,
})
```
Add `ollama` service to `docker-compose.yml`. Pull `mistral:7b-instruct` on startup.

Fallback: if Ollama unreachable, return the rule's `recommendation` field from Agent 3 YAML as a static suggestion.

#### 4.3 `RecommendationEngine` — `backend/app/services/recommendation/engine.py`
Prompt template (French):
```
Tu es un expert juridique spécialisé en droit tunisien et RGPD.
Clause originale: {clause_text}
Problème identifié: {violation_description}
Références légales applicables: {legal_refs}
Réécris cette clause pour la rendre conforme à {framework}.
Réponds avec:
CLAUSE_RÉVISÉE: [version corrigée]
EXPLICATION: [pourquoi ce changement est nécessaire]
```

### New DB table: `recommendations`
```sql
CREATE TABLE recommendations (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    evaluation_id INTEGER REFERENCES compliance_evaluation(id) ON DELETE CASCADE,
    clause_id VARCHAR(50),
    rule_id VARCHAR(100),
    original_text TEXT,
    revised_text TEXT,
    explanation TEXT,
    model_used VARCHAR(128),
    created_at TIMESTAMP DEFAULT NOW()
);
```
Migration: `backend/alembic/versions/0005_agent4_recommendations.py`

### New document status
`recommending` → `recommended`

### API endpoints — `backend/app/api/routes/recommendations.py`
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/documents/{id}/recommendations` | All clause recommendations |
| POST | `/documents/{id}/recommendations/regenerate` | Re-run with different model |

### Celery task
`backend/app/tasks/recommendations.py` — chained after `compliance_evaluation` on success

### docker-compose.yml changes
```yaml
ollama:
  image: ollama/ollama
  ports:
    - "11434:11434"
  volumes:
    - ollama_data:/root/.ollama
  command: ["serve"]
```
Add `ollama_data` volume. Add startup script to pull `mistral:7b-instruct`.

---

## Step 5 — Dashboard UI

Build in `frontend/src/pages/DashboardPage.tsx` (new route `/dashboard`).

### Goal
A dedicated full-page dashboard showing the compliance analysis of a selected document, with all agents' output synthesized visually.

### Components to build
| Component | File | Purpose |
|-----------|------|---------|
| `ComplianceRadarChart` | `frontend/src/components/ComplianceRadarChart.tsx` | Recharts RadarChart — LNPDP/GDPR/COC axes |
| `ViolationTable` | `frontend/src/components/ViolationTable.tsx` | Sortable/filterable table: clause, severity, framework, article |
| `RecommendationPanel` | `frontend/src/components/RecommendationPanel.tsx` | Side-by-side diff: original vs revised clause, accept button |
| `DocumentSelector` | `frontend/src/components/DocumentSelector.tsx` | Dropdown to pick any evaluated document |

### Frontend API calls to add
```typescript
export const getDocumentRecommendations = (id: number) =>
  apiRequest<Recommendation[]>(`/documents/${id}/recommendations`);
```

### Route
Add to router: `<Route path="/dashboard" element={<DashboardPage />} />`
Add nav link in app header.

### Install Recharts
```
npm install recharts
```

---

## Step 6 — Fine-tune Agent 2 Models

### Goal
Replace zero-shot classifier with fine-tuned model (~85–90% accuracy vs ~65–70% zero-shot).

### Steps
1. Collect 50 French contracts from `marchespublics.gov.tn` and `legislation.tn`
2. Run Agent 1 on all contracts → normalized_text in DB
3. Run `python scripts/segment_for_annotation.py` → export clause segments
4. Annotate in Label Studio (`pip install label-studio && label-studio start`)
5. Export → `data/annotated/train/`, `val/`, `test/`
6. Fine-tune:
   ```bash
   python scripts/train_clause_classifier.py \
     --model camembert-base \
     --train data/annotated/train/ \
     --val data/annotated/val/ \
     --output data/models/clause_classifier/
   ```
7. Update `ClauseClassifier` to load from `data/models/clause_classifier/`

### Annotation scripts to write
- `scripts/segment_for_annotation.py`
- `scripts/import_to_labelstudio.py`
- `scripts/export_annotations.py`
- `scripts/train_val_test_split.py`
- `scripts/train_clause_classifier.py`

### Datasets to use for fine-tuning
- CUAD (`data/raw/datasets/cuad/`) — map 41 labels to our 12 ClauseLabel types
- LEDGAR (`data/raw/datasets/ledgar/`) — 100-label pre-training
- GDPR Classification (`data/raw/datasets/gdpr_classification/`) — compliance flag detection
- CNIL FR (`data/raw/datasets/cnil_fr/`) — French regulatory language

---

## Step 7 — Infrastructure

### 7.1 OCR Pipeline
- Stub already exists: `backend/app/services/ingestion/providers/ocr.py`
- Add: `pytesseract` + `pdf2image` to Dockerfile
- Trigger: when `PdfProvider` detects <50 chars/page (warning already logged)
- Languages: `tesseract-ocr-fra` + `tesseract-ocr-ara`

### 7.2 WebSockets (replace 2s polling)
- `backend/app/api/routes/ws.py`
- Frontend: replace `setInterval` with `new WebSocket(ws://backend/ws/documents/{id})`

### 7.3 Authentication
- User table already exists: `backend/app/db/models/user.py`
- Add: `python-jose` + `passlib` to requirements
- Endpoints: `POST /auth/register`, `POST /auth/token`
- Frontend: login page + JWT in localStorage

### 7.4 Audit Logs
- New table: `audit_log(id, user_id, document_id, action, details_json, created_at)`
- Migration: `0006_audit_log.py`
- Log every upload, extraction, analysis, evaluation, recommendation, deletion

---

## Milestone Summary

| Milestone | Status | Deliverable |
|-----------|--------|------------|
| M1 | ✅ DONE | Agent 1 — extraction pipeline |
| M2 | ✅ DONE | Agent 2 — zero-shot NLP analyzer |
| M3 | ✅ DONE | Datasets downloaded (CUAD, LEDGAR, MAUD, GDPR, CNIL, UnfairToS) |
| M4 | ✅ DONE | Agent 3 — rule-based compliance evaluator |
| M5 | 🔨 NEXT | Agent 4 — LLM recommender (Ollama/Mistral) |
| M6 | ⏳ | Full dashboard UI (radar, violations table, recommendations) |
| M7 | ⏳ | Agent 2 fine-tuned classifier (50 annotated contracts) |
| M8 | ⏳ | Production hardening (auth, audit logs, WebSockets) |
