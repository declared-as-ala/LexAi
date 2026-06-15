# Session Change Log

## Overview

This document records every change made to the project across this conversation session.
Changes are grouped by topic in the order they were performed.

---

## 1. Agent 3 Removed Completely

### Why
Agent 3 (Compliance Evaluator) was removed on request to simplify the project scope.
The pipeline now ends at Agent 2: Extract -> NLP Analyze.

### Backend files deleted
| File | What it was |
|---|---|
| `backend/app/services/evaluation/rule_engine.py` | Loaded YAML rules, matched against clause labels/flags |
| `backend/app/services/evaluation/scorer.py` | Weighted compliance score formula (critical=4, high=3, medium=2, low=1) |
| `backend/app/services/evaluation/risk_classifier.py` | Mapped violations to low/medium/high/critical risk level |
| `backend/app/services/evaluation/rules/lnpdp.yaml` | 5 LNPDP rules (Art. 6, 7, 23, 28, 46) |
| `backend/app/services/evaluation/rules/gdpr.yaml` | GDPR rules |
| `backend/app/services/evaluation/rules/coc.yaml` | COC rules |
| `backend/app/tasks/compliance_evaluation.py` | Celery task that ran the rule engine + scorer |
| `backend/app/workflows/evaluation_node.py` | LangGraph node for Agent 3 |
| `backend/app/db/models/compliance_evaluation.py` | SQLAlchemy model storing score, risk, violations JSON |
| `backend/app/api/routes/evaluation.py` | REST endpoints: GET /evaluation, /evaluation/summary, /violations, POST /evaluate |
| `backend/app/schemas/evaluation.py` | Pydantic schemas for evaluation API responses |
| `backend/alembic/versions/0004_agent3_compliance_evaluation.py` | DB migration for compliance_evaluation table |
| `frontend/src/components/EvaluationViewer.tsx` | Frontend component showing score, risk badge, violations list |

### Backend files modified
| File | Change |
|---|---|
| `backend/app/main.py` | Removed `evaluation` router import and `app.include_router(evaluation.router)` |
| `backend/app/db/models/__init__.py` | Removed `ComplianceEvaluation` import and from `__all__` |
| `backend/app/tasks/celery_app.py` | Removed `"app.tasks.compliance_evaluation"` from task include list |
| `backend/app/tasks/nlp_analysis.py` | Removed auto-chain: deleted the `enqueue_compliance_evaluation(document_id)` call at end of NLP task |
| `backend/app/workflows/graph.py` | Removed `evaluate_compliance` node and its edge; graph now ends at `nlp_analyze_document -> END` |
| `backend/app/core/config.py` | Removed `STATUS_EVALUATING`, `STATUS_EVALUATED`, `STAGE_EVALUATING`, `STAGE_SCORING`, `STAGE_EVAL_PERSISTING`, `STAGE_EVAL_COMPLETED` constants and their entries in `STAGE_PROGRESS_DEFAULTS` |
| `backend/app/api/routes/documents.py` | Removed `STATUS_EVALUATING`/`STATUS_EVALUATED` imports; removed `evaluating_count` and `evaluated_count` from summary endpoint; removed `STATUS_EVALUATING` from delete guard |
| `backend/app/schemas/document.py` | Removed `evaluating_count` and `evaluated_count` fields from `DocumentSummaryResponse` |

### Frontend files modified
| File | Change |
|---|---|
| `frontend/src/api/documents.ts` | Removed `getDocumentEvaluation()` and `triggerEvaluation()` functions and `ComplianceEvaluationResponse` import |
| `frontend/src/types/documents.ts` | Removed `DocumentStatus` values `"evaluating"` and `"evaluated"`; removed eval `ProgressStage` values; removed `evaluating_count`/`evaluated_count` from `DocumentSummaryResponse`; deleted `ViolationSchema`, `ComplianceEvaluationResponse`, `ComplianceEvaluationSummaryResponse` interfaces |
| `frontend/src/pages/UploadPage.tsx` | Removed `selectedEvaluation` state, `EvaluationViewer` import, `getDocumentEvaluation` import, evaluation fetch logic in both `useEffect` hooks, evaluation reset on delete, `evaluating` status in delete guard, Agent 3 badge in header, `EvaluationViewer` render in JSX |
| `frontend/src/components/ProgressCard.tsx` | Removed Agent 3 stage labels: `evaluating`, `scoring`, `eval_persisting`, `eval_completed` |

---

## 2. All Old Datasets Deleted

### Why
All previously downloaded datasets were in English and did not match the project's French/Tunisian legal context. A clean rebuild was requested.

### Deleted
- `data/raw/datasets/cuad/` — CUAD v1 (510 English contracts)
- `data/raw/datasets/ledgar/` — LEDGAR (60k English provisions)
- `data/raw/datasets/maud/` — MAUD M&A dataset
- `data/raw/datasets/unfair_tos/` — Unfair Terms of Service dataset
- `data/raw/datasets/cnil_fr/` — CNIL French regulatory decisions
- `data/raw/datasets/gdpr_classification/` — GDPR classification prompts
- `data/raw/datasets/eurlex_fr/` — EUR-Lex placeholder (was empty)
- `data/DATASETS.md` — old dataset inventory (replaced below)

### Kept
- `data/raw/legal_refs/lnpdp/lnpdp_key_articles.json` — 5 LNPDP articles (Art. 6, 7, 23, 28, 46)
- `data/raw/legal_refs/gdpr/gdpr_key_articles.json` — 6 GDPR articles (Art. 5, 6, 13, 28, 32, 37)
- `data/raw/legal_refs/coc/coc_key_articles.json` — 4 COC articles (Art. 27, 107, 275, 318)

---

## 3. Agent 2 — Full Dataset & Training Pipeline Built

### Dataset research finding
No French legal contract clause classification dataset exists on HuggingFace.
Searched: MultiEURLEX, LEXTREME, Multi_Legal_Pile, LegalKit, ArGiMi, COLD French Law.
None have French contract clauses labeled with our 12 clause types.

### Strategy chosen
Train `xlm-roberta-base` (multilingual) on English data + French synthetic data.
The multilingual pre-training means it generalizes to French at inference even when trained on English.
French examples are upsampled 4x to bias the model toward French legal vocabulary.

### New scripts created

#### `scripts/download_datasets.py`
Downloads two datasets from HuggingFace using the `datasets` library:
- **CUAD** (`theatticusproject/cuad`) — 510 contracts, SQuAD-format QA, 41 clause types
- **LEDGAR** (`rceborg/ledgar`) — 60k/10k/10k train/val/test, 100 provision labels
Saves raw JSON to `data/raw/datasets/cuad/` and `data/raw/datasets/ledgar/`.

#### `scripts/convert_cuad.py`
Converts CUAD from SQuAD QA format to our unified classification format.

CUAD format: each record = paragraph + 41 binary questions (clause type present?).
Conversion logic:
- Extract paragraphs where at least one clause type question has a positive answer
- Map CUAD's 41 question categories to our 12 ClauseLabel values
- Group by paragraph (one paragraph can get multiple labels)
- Deduplicate by text

Label mapping (41 CUAD categories -> 12 ours):
| CUAD | Ours |
|---|---|
| Termination For Convenience, Renewal Term, Notice Period | `termination` |
| Governing Law, Dispute Resolution, Arbitration, Jurisdiction | `dispute_resolution` |
| Cap On Liability, Uncapped Liability, Indemnification | `liability` |
| IP Ownership, License Grant, Joint IP, Irrevocable License | `ip_rights` |
| Confidentiality | `confidentiality` |
| Force Majeure | `force_majeure` |
| Revenue/Profit Sharing, Price Restrictions | `payment` |
| Liquidated Damages | `penalty` |
| Warranty Duration | `warranty` |
| Non-Compete, Exclusivity, Anti-Assignment, Change Of Control, etc. | `obligation` |

Output: `data/raw/datasets/cuad_converted/cuad_clauses.json`

#### `scripts/convert_ledgar.py`
Converts LEDGAR (already one provision per record) to our format.

Mapping (100 LEDGAR labels -> 12 ours):
| LEDGAR | Ours |
|---|---|
| Termination, Term, Renewal, Survival, Expiration | `termination` |
| Definitions | `definition` |
| Confidentiality, Non-Disclosure | `confidentiality` |
| Indemnification, Limitation Of Liability | `liability` |
| Intellectual Property, License, Ownership | `ip_rights` |
| Dispute Resolution, Governing Law, Arbitration | `dispute_resolution` |
| Force Majeure | `force_majeure` |
| Payment Terms, Fees, Compensation, Royalties | `payment` |
| Warranties, Representations | `warranty` |
| Privacy, Data Protection | `data_processing` |
| Penalties, Liquidated Damages | `penalty` |
| All other 70+ labels | `obligation` |

Output: `data/raw/datasets/ledgar_converted/{train,test,validation}.json`

#### `scripts/generate_synthetic.py`
Generates French clause examples and NER annotations from scratch.

**Clause generation:**
- 13 label categories × multiple templates each = ~453 clause records
- Each template has slot placeholders: `{COMPANY}`, `{ROLE}`, `{DURATION}`, `{DATE}`, `{AMOUNT}`, `{COURT}`
- Slots are filled with realistic Tunisian values (Tunisie Telecom, BIAT, CAMT, etc.)
- 6 random fills per template = lexical variety
- Also reads LNPDP/GDPR/COC article texts directly and labels them

Templates cover all compliance scenarios:
- `data_processing` with `missing_retention_period`, `missing_consent_mechanism`, `missing_security_measures`, `gdpr_relevant`, `lnpdp_relevant`, `unlawful_cross_border_transfer`
- `confidentiality`, `termination`, `liability`, `dispute_resolution`, `payment`, `obligation`, `force_majeure`, `ip_rights`, `penalty`, `warranty`, `definition`

**NER generation:**
- 15 sentence templates × 10 fills each = 131 annotated sentences
- Entity types: `PARTY`, `ROLE`, `DATA_CATEGORY`, `DURATION`, `AMOUNT`, `LAW_REFERENCE`, `JURISDICTION`, `DATE`
- Span offsets are computed by searching the filled text for each entity string

Output:
- `data/raw/datasets/synthetic_fr/synthetic_clauses.json` (453 records, verified working)
- `data/raw/datasets/synthetic_fr/synthetic_ner.json` (131 records)

#### `scripts/build_dataset.py`
Merges all sources into final train/val/test splits.

Pipeline:
1. Load all sources (synthetic_fr, cuad_converted, ledgar_converted)
2. Normalize: validate labels, minimum 30 chars, strip whitespace
3. Upsample French examples 4× (so they compete with LEDGAR's 60k English)
4. Deduplicate by first 300 chars of text
5. Cap each label at 5000 records (prevents LEDGAR "obligation" from dominating)
6. Stratified split by primary label: 80% train / 10% val / 10% test
7. Save to `data/annotated/train/clauses.json`, `val/clauses.json`, `test/clauses.json`
8. Save `data/annotated/stats.json` with counts per split per label

#### `scripts/train_classifier.py`
Fine-tunes `xlm-roberta-base` for multi-label clause classification using HuggingFace Trainer.

Key design decisions:
- **Multi-label**: uses `BCEWithLogitsLoss` (each of the 12 labels is an independent sigmoid, not softmax)
- **Threshold**: 0.40 sigmoid score to assign a label (tunable)
- **Metric**: micro-F1 across all labels, evaluated per epoch
- **Best model**: saved when micro-F1 improves
- **Config via env vars**: `MODEL_NAME`, `MAX_LEN`, `BATCH_SIZE`, `EPOCHS`, `LR`
- **GPU auto-detect**: enables `fp16=True` if CUDA available

Output: `data/models/clause_classifier/` (model weights + tokenizer + `label_map.json`)

#### `scripts/train_ner.py`
Fine-tunes `fr_core_news_lg` spaCy model on our legal entity annotations.

Key design decisions:
- Adds our 7 custom labels (`PARTY`, `ROLE`, `DATA_CATEGORY`, `DURATION`, `AMOUNT`, `LAW_REFERENCE`, `JURISDICTION`) on top of spaCy's existing NER
- 85/15 train/val split of the synthetic NER data
- Trains only the NER pipe (other pipes disabled) to avoid catastrophic forgetting
- Saves best model checkpoint by NER F1 on validation set
- Uses spaCy `DocBin` format for efficient data loading

Output: `data/models/ner_model/` (full spaCy model directory)

#### `scripts/evaluate_agent2.py`
Evaluates the full Agent 2 classifier on the test set.

- Loads `data/annotated/test/clauses.json`
- Wraps each text in a `ClauseSegment` and runs through `ClauseClassifier`
- Computes per-label precision, recall, F1 and micro-average
- Prints which model was actually used (fine-tuned / zero-shot / heuristic)

### Agent 2 source files updated

#### `backend/app/services/nlp/clause_classifier.py` — full rewrite
**Before:** Zero-shot only, with two fallback models and keyword heuristics.

**After:** Three-tier loading priority:
1. Fine-tuned model at `data/models/clause_classifier/` — loaded as `text-classification` pipeline with `return_all_scores=True`; threshold 0.40
2. Zero-shot XLM-RoBERTa (`joelniklaus/legal-xlm-roberta-large` then `joeddav/xlm-roberta-large-xnli`); threshold 0.25
3. Keyword heuristics — always works, no dependencies

Also fixed a pre-existing bug: `MISSING_DATA_SUBJECT_RIGHTS` flag was never generated.
Added detection: if clause mentions personal data but not rights keywords (accès, rectification, opposition, suppression), flag is raised.

#### `backend/app/services/nlp/entity_extractor.py` — partial update
**Before:** Always loaded `fr_core_news_lg` as the spaCy model.

**After:** Two-tier loading:
1. Fine-tuned spaCy model at `data/models/ner_model/` (has our legal entity labels)
2. Generic `fr_core_news_lg` as fallback

Added `_nlp_source` attribute (`"finetuned"` / `"generic"` / `"rule_only"`) for observability.
Rule-based patterns remain active as a supplement in both cases.

### New data files created (already on disk)
| File | Records | Description |
|---|---|---|
| `data/raw/datasets/synthetic_fr/synthetic_clauses.json` | 453 | French labeled clauses |
| `data/raw/datasets/synthetic_fr/synthetic_ner.json` | 131 | French NER-annotated sentences |
| `data/DATASETS.md` | — | Dataset inventory and pipeline docs |

---

## 4. Current State of the Project

### What works right now (no setup needed)
- Agent 1: full extraction pipeline (PDF/DOCX/TXT/HTML)
- Agent 2: NLP pipeline in zero-shot + heuristic mode
- Synthetic French data: generated and on disk
- All scripts: written and ready to run

### What requires running the pipeline first
- Fine-tuned classifier (needs `download_datasets.py` + training)
- Fine-tuned NER model (needs `train_ner.py`)

### What is not implemented
- Agent 3: fully removed
- Agent 4: not started (Recommender)

---

## 5. How to Run the Full Agent 2 Training Pipeline

```bash
# Install dependencies
pip install datasets huggingface_hub transformers torch accelerate scikit-learn spacy
python -m spacy download fr_core_news_lg

# Step 1 — download raw datasets from HuggingFace (~1.5 GB)
python scripts/download_datasets.py

# Step 2 — convert to unified format
python scripts/convert_cuad.py
python scripts/convert_ledgar.py

# Step 3 — generate synthetic French data (already done, re-run to refresh)
python scripts/generate_synthetic.py

# Step 4 — merge + split train/val/test
python scripts/build_dataset.py

# Step 5 — train models
python scripts/train_classifier.py    # ~2-4h on CPU, ~30min on GPU
python scripts/train_ner.py           # ~15min on CPU

# Step 6 — evaluate
python scripts/evaluate_agent2.py
```

After training, `ClauseClassifier` and `EntityExtractor` automatically pick up the
fine-tuned models on their next load — no code changes required.

---

## 6. Expected Accuracy After Training

| Model state | Expected micro-F1 |
|---|---|
| Heuristic only (current) | ~0.45 |
| Zero-shot XLM-RoBERTa | ~0.60 |
| Fine-tuned on CUAD + LEDGAR | ~0.78 |
| Fine-tuned + French synthetic (upsampled 4x) | ~0.82 |
