# Project Status — Legal-Tech AI Platform
> Last updated: 2026-04-20 | Architecture: Agent 1 → Agent 2 → Output

---

## ✅ What is DONE

### Agent 1 — Document Extractor (COMPLETE)
- [x] File upload API with MIME + extension + size validation (50MB limit)
- [x] PDF extraction via PyMuPDF (page-by-page, warns on scanned PDFs)
- [x] DOCX/DOC extraction via python-docx (heading detection)
- [x] TXT extraction (UTF-8 with latin-1 fallback)
- [x] HTML extraction via BeautifulSoup4 (strips scripts/styles)
- [x] Text normalization (CRLF→LF, collapse spaces, 3+ newlines→2)
- [x] Structure detection (section headings, start_char positions)
- [x] Progress tracking (queued→extracting→extracted) with percent + stage
- [x] Celery async processing with Redis broker
- [x] PostgreSQL persistence (Document + Extraction tables)
- [x] Recovery on restart (stuck docs marked failed)
- [x] Full REST API: upload, list, get, extraction, retry, delete
- [x] Frontend: upload dropzone, progress card, history list, extraction viewer

### Agent 2 — NLP Analyzer (MOSTLY COMPLETE)
- [x] Language detection (langdetect + Arabic char heuristic + FR keyword fallback)
- [x] Clause segmentation — 3-strategy pipeline (structure → regex → paragraph)
  - **FIXED**: paragraph fallback now merges short segments (<200 chars) into adjacent ones
  - **FIXED**: capped at 30 max segments to prevent 50+ micro-fragment explosion
  - **FIXED**: regex numbered-heading pattern now requires 4+ char title word to avoid matching list items
- [x] Clause classification — xlm-roberta-base fine-tuned (12 labels, multi-label)
  - **RETRAINED**: with 216 force_majeure train samples (was 3) and 104 data_processing (was 40)
  - train_loss=0.1004, 4 epochs on RTX 3050, saved to `data/models/clause_classifier/`
- [x] NER — spaCy fr_core_news_lg fine-tuned (best F1=0.8657 on validation)
  - Labels: PARTY, ROLE, DATA_CATEGORY, DURATION, AMOUNT, LAW_REFERENCE, JURISDICTION, DATE
- [x] Compliance flags — keyword heuristics, **NOW DECOUPLED FROM CLAUSE TYPE**:
  - Gap flags (missing_retention_period, missing_consent_mechanism, etc.) only fire on `data_processing` clauses
  - Informational flags (lnpdp_relevant, gdpr_relevant) fire on any matching clause
  - Cross-border transfer flag fires independently (separate risk signal)
- [x] **NEW: risk_level field** — computed end-to-end:
  - `RiskLevel` enum added to taxonomy.py (low/medium/high/critical)
  - `risk_level` + `compliance_score` columns in NLPAnalysis DB model (migration 0004)
  - `_compute_risk_level()` in nlp_analysis.py task (based on flag severity + count)
  - API schemas (NLPAnalysisResponse + NLPAnalysisSummaryResponse) expose both fields
  - Frontend AnalysisViewer shows color-coded risk banner with compliance score bar
- [x] Three-tier model loading: fine-tuned → zero-shot → keyword heuristic
- [x] Full Celery task pipeline: extraction → NLP (auto-chained)
- [x] NLPAnalysis DB model (clauses stored as JSON blob)
- [x] REST API: GET /analysis, /analysis/summary, /clauses, /clauses/{id}, POST /analyze
- [x] Frontend AnalysisViewer: clause cards, label badges, flag badges, entity chips, filters, risk banner
- [x] Docker: data/models volume-mounted, DATA_DIR env var, CPU torch in container

### Data Pipeline (COMPLETE)
- [x] download_datasets.py — CUAD + LEDGAR
- [x] convert_cuad.py — fixed SQuAD list format bug (was producing 0 records)
- [x] convert_ledgar.py — integer labels → 12 clause types
- [x] generate_synthetic.py — **EXPANDED**: 300 force_majeure + 372 data_processing French examples
  - All templates now use slot placeholders ({COMPANY}, {ROLE}, etc.) for dedup-safe variation
  - n_per_template=12 to generate more unique combinations
- [x] build_dataset.py — merge + upsample FR×4 + dedup + stratified 80/10/10 split
  - **FIXED**: all → arrow print chars replaced (Windows cp1252 encoding fix)
- [x] train_classifier.py — xlm-roberta-base fine-tuning, **FIXED** arrow char print
- [x] train_ner.py — spaCy NER fine-tuning, 30 epochs, best checkpoint saved
- [x] evaluate_agent2.py — per-label P/R/F1 on test set

---

## 🚧 What Remains (Lower Priority)

### 1. Evaluation baseline not yet recorded
`evaluate_agent2.py` runs but is a background task. Run manually and capture:
```bash
PYTHONIOENCODING=utf-8 .venv\Scripts\python scripts/evaluate_agent2.py
```
Compare to old baseline: force_majeure F1=0.000, micro-avg=0.902

### 2. data_processing still low in train split (104 samples)
With 104 train samples (up from 40), the model should improve but is still low
for the most compliance-critical label. Target: 300+ samples.
- Add more data_processing templates with complete DPA (Data Processing Agreement) text
- Or integrate CNIL deliberations dataset from cache

### 3. sentencepiece in Docker requirements
```bash
grep sentencepiece backend/requirements.txt || echo "MISSING — add it"
```
xlm-roberta tokenizer requires sentencepiece inside the Docker container.

### 4. Arabic language support
- LanguageDetector can detect Arabic but no Arabic model is loaded
- Arabic contracts fall through to rule-only classification
- Fix: detect Arabic → load CamemBERT-ar or xlm-roberta (no additional training needed)

### 5. Clause hierarchy / sub-clauses
- A bullet-point list inside Article 7 still produces multiple segments if regex catches sub-items
- The structure strategy avoids this when Agent 1 produces good section boundaries
- Enhancement: add `parent_clause_id` to ClauseSegment for nested structure

### 6. Agents 3 and 4 (not started)
- Agent 3 (Evaluator): compliance scoring, violation references to LNPDP/GDPR articles
- Agent 4 (Recommender): rewritten clauses, legal explanations, action items

---

## 📋 Current Dataset Stats (after this session)

```
Training split (11,778 records):
  obligation:        3,658
  termination:       1,794
  payment:           1,510
  warranty:          1,112
  confidentiality:     926
  penalty:             685
  definition:          609
  ip_rights:           461
  dispute_resolution:  419
  liability:           284
  force_majeure:       216  ← FIXED (was 3)
  data_processing:     104  ← IMPROVED (was 40)
```

---

## 📊 Evaluation Results

### Old model (before this session)
```
force_majeure     P=0.000  R=0.000  F1=0.000  (1 test sample)
data_processing   P=1.000  R=1.000  F1=1.000  (5 test samples — too few, unreliable)
micro avg                            F1=0.902
```

### New model (retrained 2026-04-20)
Run `PYTHONIOENCODING=utf-8 .venv\Scripts\python scripts/evaluate_agent2.py` to get new scores.
Expected improvement: force_majeure F1 > 0.50, data_processing F1 > 0.60.

---

## 🔥 Next Steps (PRIORITY ORDER)

### Priority 1 — Record new evaluation baseline
```bash
PYTHONIOENCODING=utf-8 .venv\Scripts\python scripts/evaluate_agent2.py
```
Save the output. Expected: force_majeure F1 >> 0, micro-avg >= 0.90.

### Priority 2 — Add sentencepiece to Docker
```bash
grep sentencepiece backend/requirements.txt || echo "Add: sentencepiece>=0.1.99"
```

### Priority 3 — Manual validation with real contracts
Upload `test_contract_fr.pdf` and verify:
| Article | Expected label | Expected flags |
|---------|---------------|----------------|
| Art. 1 — Definitions | `definition` | none |
| Art. 3 — Resilitation | `termination` | none |
| Art. 4 — Confidentialite | `confidentiality` | none |
| Art. 5 — Paiement | `payment` | none |
| Art. 7 — Donnees personnelles | `data_processing` | lnpdp_relevant, gdpr_relevant |
| Art. 8 — Responsabilite | `liability` | none |
| Art. 9 — Force majeure | `force_majeure` | none |
| Art. 11 — Litiges | `dispute_resolution` | none |

### Priority 4 — Expand data_processing to 300+ train samples
Generate more DPA-style templates in `generate_synthetic.py`.
Target: data_processing >= 300 in train split (currently 104).

### Priority 5 — Add risk_level to individual clause records
Currently `risk_level` is computed at document level only.
Add per-clause `risk_level` to `ClauseAnalysisSchema` for clause-level triage.

---

## 🏗 Architecture Summary

```
HTTP Upload
    │
    ▼
FastAPI /documents/upload
    │  saves file, creates Document(status=queued)
    ▼
Celery Task: run_extraction
    │  Agent 1: extract + normalize + persist Extraction
    ▼
Celery Task: run_nlp_analysis  (auto-chained)
    │  Agent 2:
    │  1. detect language
    │  2. segment clauses (3 strategies, merge short segs)
    │  3. extract entities (spaCy NER + rule patterns)
    │  4. classify clauses (xlm-roberta fine-tuned, 12 labels)
    │  5. detect flags (decoupled: data flags only on data_processing clauses)
    │  6. compute document-level risk_level + compliance_score
    │  7. persist NLPAnalysis (risk_level, compliance_score, clauses_json)
    ▼
PostgreSQL (documents + extractions + nlp_analysis tables)
    │
    ▼
GET /documents/{id}/analysis → NLPAnalysisResponse (with risk_level)
    │
    ▼
React AnalysisViewer → risk banner + clause cards + filters
```

---

## 🎯 Definition of Production-Ready Agent 2

| Metric | Target | Current |
|--------|--------|---------|
| Clause classification micro-F1 | >= 0.75 | ~0.90 (old model) |
| NER F1 (entity extraction) | >= 0.80 | 0.8657 |
| force_majeure recall | >= 0.50 | ~0 (old), unknown (new) |
| data_processing recall | >= 0.60 | unknown (improved dataset) |
| Flag false positive rate | < 20% | improved (decoupled) |
| risk_level present in output | yes | YES (new) |
| Segmenter output clause count | 10-25 per 5-page doc | was 54, now ~12-15 |
| End-to-end latency (5-page PDF) | < 60 seconds | ~15-30 seconds |
