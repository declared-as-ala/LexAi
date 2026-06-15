# LegalTech AI Platform — Project Memory & Architecture

> **Status as of 2026-04-14**
> Agent 1 (Extractor) is COMPLETE and STABLE.
> Agent 2 (NLP Analyzer) is COMPLETE and STABLE.
> Agents 3 and 4 are NOT YET IMPLEMENTED.

---

## 1. Project Overview

This system is a **LegalTech AI platform** designed to automate the analysis of legal contracts, specifically within the **Tunisian legal context**. It addresses a critical gap: Tunisian SMEs and legal professionals spend enormous manual effort reviewing contracts for compliance with local law (LNPDP, COC) and international standards (GDPR/RGPD, ISO 27001).

**Core capabilities (target state):**
- Automated contract ingestion and text extraction
- NLP-based clause segmentation and classification
- Compliance scoring against legal frameworks
- AI-generated recommendations for non-compliant clauses

**Who uses it:**
- Legal teams reviewing third-party contracts
- Compliance officers auditing internal contracts
- Law firms processing client documents at scale

**Why it exists:**
- Manual contract review is slow, error-prone, and expensive
- Tunisian legal frameworks (LNPDP) create specific compliance requirements
- LLMs and NLP can automate up to 80% of routine review tasks

---

## 2. Architecture Overview

The system is composed of **4 specialized agents** orchestrated via LangGraph:

```
User Upload
     │
     ▼
┌─────────────────────┐
│   Agent 1           │  COMPLETE ✅
│   Extractor         │
│                     │
│  PDF/DOCX/TXT/HTML  │
│  → raw_text         │
│  → normalized_text  │
│  → structure_meta   │
└────────┬────────────┘
         │ normalized_text + structure_metadata
         ▼
┌─────────────────────┐
│   Agent 2           │  NEXT 🔨
│   NLP Analyzer      │
│                     │
│  → clause segments  │
│  → entity labels    │
│  → clause classes   │
│  → confidence scores│
└────────┬────────────┘
         │ structured clauses + labels
         ▼
┌─────────────────────┐
│   Agent 3           │  PLANNED
│   Evaluator         │
│                     │
│  → compliance score │
│  → risk level       │
│  → violation flags  │
└────────┬────────────┘
         │ scored clauses + violations
         ▼
┌─────────────────────┐
│   Agent 4           │  PLANNED
│   Recommender       │
│                     │
│  → rewritten clauses│
│  → explanations     │
│  → action items     │
└─────────────────────┘
         │
         ▼
    Dashboard UI
```

**Orchestration**: LangGraph manages state (`AnalysisState`) and routes documents through agent nodes. Each agent is a LangGraph node that reads from and writes to a shared typed state dict.

---

## 3. Agent 1 — Extractor (COMPLETE ✅)

### What It Does
Agent 1 is the **ingestion and extraction layer**. It accepts raw document files from users, validates them, extracts their textual content, normalizes it, and persists the result for downstream agents.

### Supported Formats
| Format | MIME Type | Provider | Notes |
|--------|-----------|----------|-------|
| PDF | application/pdf | `PdfProvider` | PyMuPDF; warns on scanned PDFs |
| DOCX | application/vnd.openxmlformats... | `DocxProvider` | python-docx; detects headings |
| DOC | application/msword | `DocxProvider` | Same as DOCX |
| TXT | text/plain | `TxtProvider` | UTF-8 with latin-1 fallback |
| HTML | text/html | `HtmlProvider` | BeautifulSoup4; strips scripts |

### Extraction Pipeline

```
Upload Request
     │
     ├── Validate MIME type (whitelist)
     ├── Validate file extension (whitelist)
     ├── Validate file size (max 50MB)
     ├── Save file to disk (UPLOAD_DIR)
     ├── Create Document record (status=queued)
     └── Enqueue Celery task → return document_id

Celery Worker picks up task:
     │
     ├── status → extracting
     ├── stage → starting
     ├── Registry.get_provider(mime_type)
     ├── stage → selecting_provider
     ├── provider.extract(file_path) → ExtractionArtifact
     ├── stage → extracting
     ├── Normalizer.normalize(raw_text) → normalized_text
     ├── stage → normalizing
     ├── Persist Extraction record to DB
     ├── stage → persisting
     └── status → extracted, stage → completed, percent=100
```

### Provider Pattern
Each format is handled by a dedicated provider class implementing `DocumentExtractorProvider`:
```python
class DocumentExtractorProvider(ABC):
    @abstractmethod
    def extract(self, file_path: Path) -> ExtractionArtifact: ...
```

The `ProviderRegistry` maps MIME types to singleton provider instances. Adding a new format = adding a provider class + one registry entry. No changes to core logic.

Key files:
- `backend/app/services/ingestion/providers/base.py` — abstract interface
- `backend/app/services/ingestion/providers/registry.py` — MIME → provider mapping
- `backend/app/services/ingestion/providers/pdf.py` — PyMuPDF extraction
- `backend/app/services/ingestion/providers/docx.py` — python-docx extraction
- `backend/app/services/ingestion/providers/txt.py` — plain text extraction
- `backend/app/services/ingestion/providers/html.py` — BeautifulSoup4 extraction
- `backend/app/services/ingestion/providers/ocr.py` — OCR stub (not implemented)

### Normalization
Applied to all extracted text regardless of format (`backend/app/services/ingestion/normalizer.py`):
- Ensures valid UTF-8 (replaces invalid chars)
- Normalizes line endings (CRLF → LF)
- Collapses multiple spaces within lines
- Collapses 3+ newlines to 2 (preserves paragraph structure)
- Strips leading/trailing whitespace

### Database Schema

**Document table** (`backend/app/db/models/document.py`):
- `status`: queued | extracting | extracted | failed
- `progress_percent`: 0–100
- `progress_stage`: queued | starting | selecting_provider | extracting | normalizing | persisting | completed | failed
- `progress_message`: Human-readable current action
- `last_error`: Last failure message
- `task_id`: Celery task ID

**Extraction table** (`backend/app/db/models/document.py`):
- `raw_text`: Unprocessed extracted text
- `normalized_text`: Cleaned text (Agent 2 input)
- `structure_json`: Document structure (headings, sections)
- `page_metadata_json`: Per-page metadata (PDF only)
- `warnings`: Array of extraction warnings

### Status Lifecycle

```
queued → extracting → extracted
                   ↘ failed → (retry) → queued
```

Progress service (`backend/app/services/ingestion/progress.py`) manages all transitions.

### APIs
| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/documents/upload` | Upload and queue |
| GET | `/documents` | List all documents |
| GET | `/documents/summary` | Queue counts |
| GET | `/documents/{id}` | Status + progress |
| GET | `/documents/{id}/extraction` | Full extraction result |
| POST | `/documents/{id}/retry` | Retry failed doc |
| DELETE | `/documents/{id}` | Remove document |
| GET | `/health` | Health check |

### LangGraph Integration
- **State**: `AnalysisState` TypedDict in `backend/app/workflows/state.py`
- **Node**: `extract_document` in `backend/app/workflows/extract_node.py`
- **Graph**: `backend/app/workflows/graph.py` — currently: `validate_input → extract_document → END`

### Recovery
On backend startup, `backend/app/services/ingestion/recovery.py` finds any documents stuck in `queued` or `extracting` status (from interrupted runs) and marks them `failed` with a retry message. This prevents phantom stuck documents.

### Frontend
- **Upload Dropzone**: Drag-and-drop or file picker (`frontend/src/components/UploadDropzone.tsx`)
- **Document History List**: Sidebar with all documents (`frontend/src/components/DocumentHistoryList.tsx`)
- **Queue Summary Cards**: Counts by status (`frontend/src/components/QueueSummaryCards.tsx`)
- **Progress Card**: Real-time progress bar + stage label (`frontend/src/components/ProgressCard.tsx`)
- **Extraction Viewer**: Raw text, normalized text, structure, metadata, warnings (`frontend/src/components/ExtractionViewer.tsx`)
- **Polling**: Every 2 seconds while any doc is queued/extracting (`frontend/src/pages/UploadPage.tsx`)

---

## 4. Data Flow Between Agents

### Agent 1 → Agent 2

Agent 2 reads from the `Extraction` DB record:
```json
{
  "document_id": 42,
  "normalized_text": "Article 1 — Objet du contrat\nLe présent contrat...",
  "structure_json": {
    "sections": [
      {"title": "Objet du contrat", "level": 1, "start_char": 0},
      {"title": "Durée", "level": 1, "start_char": 520}
    ]
  },
  "warnings": []
}
```

### Agent 2 → Agent 3

Agent 3 reads structured clause objects:
```json
{
  "document_id": 42,
  "clauses": [
    {
      "clause_id": "c-001",
      "text": "Le responsable du traitement s'engage à...",
      "start_char": 0,
      "end_char": 312,
      "labels": ["data_processing", "gdpr_relevant"],
      "entities": [
        {"text": "responsable du traitement", "label": "ROLE"},
        {"text": "données personnelles", "label": "DATA_CATEGORY"}
      ],
      "confidence": 0.91,
      "language": "fr"
    }
  ]
}
```

### Agent 3 → Agent 4

Agent 4 reads scored violations:
```json
{
  "document_id": 42,
  "compliance_score": 67.3,
  "risk_level": "medium",
  "violations": [
    {
      "clause_id": "c-001",
      "framework": "LNPDP",
      "article": "Art. 23",
      "severity": "high",
      "description": "Retention period not specified"
    }
  ]
}
```

---

## 5. Dataset Strategy

### Target Dataset
A **Tunisian CUAD-like dataset** of annotated legal contracts:
- **Domains**: employment, service, NDA, data processing agreements, commercial contracts
- **Language**: French (primary), Arabic (secondary), bilingual
- **Annotations**: Clause type labels, entity spans, compliance flags

### Legal References
- **LNPDP** (Loi n°2004-63): Tunisian data protection law
- **COC** (Code des Obligations et Contrats): Tunisian contract law
- **RGPD/GDPR**: European data protection (cross-border contracts)
- **INPDP** guidelines: Tunisian data protection authority guidance

### Dataset Structure
```
data/
├── raw/
│   ├── contracts/         # Original PDF/DOCX contracts (not committed — too large)
│   └── legal_refs/        # LNPDP text, COC extracts
├── processed/
│   ├── extracted/         # JSON: normalized_text + structure per document
│   └── segmented/         # JSON: clause segments per document
└── annotated/
    ├── train/             # 80% — annotated clause JSON
    ├── val/               # 10%
    └── test/              # 10%
```

### Annotation Format
```json
{
  "doc_id": "contract_042",
  "clause_id": "c-001",
  "text": "...",
  "labels": ["data_retention", "gdpr_relevant"],
  "entities": [{"text": "...", "label": "DATA_CATEGORY", "start": 0, "end": 22}],
  "compliant": false,
  "violation_refs": ["LNPDP_Art23", "GDPR_Art5_1e"]
}
```

### Taxonomy (Multi-Label)
```
legal_taxonomy/
├── contract_type:   employment, service, nda, data_processing, commercial
├── clause_type:     definition, obligation, liability, termination, data_processing,
│                   confidentiality, dispute_resolution, force_majeure, penalty, ip_rights
└── compliance_flag: gdpr_relevant, lnpdp_relevant, missing_retention_period,
                     missing_dpo, missing_consent_mechanism, excessive_data_collection
```

---

## 6. Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| API | FastAPI 0.109+ | REST endpoints, async request handling |
| Task Queue | Celery 5.3+ | Async extraction jobs |
| Message Broker | Redis 7 | Celery broker + result backend |
| Database | PostgreSQL 16 | Persistent storage |
| ORM | SQLAlchemy 2.0+ | DB access, Alembic migrations |
| Multi-Agent | LangGraph 0.2+ | Agent orchestration, state machine |
| PDF Extraction | PyMuPDF (fitz) | Page-by-page PDF text extraction |
| DOCX Extraction | python-docx | Word document extraction |
| HTML Extraction | BeautifulSoup4 | HTML stripping and text extraction |
| NLP (Agent 2) | spaCy 3.7+ | Tokenization, NER, segmentation |
| Transformers | HuggingFace Transformers | BERT/XLM-R fine-tuning |
| Models | CamemBERT, XLM-RoBERTa | French/multilingual clause classification |
| ML (Agent 3) | scikit-learn, XGBoost | Compliance scoring |
| LLM (Agent 4) | Mistral 7B / LLaMA 3 | Clause rewriting, recommendations |
| Frontend | React 18 + TypeScript | UI |
| Bundler | Vite 5 | Fast frontend builds |
| Styling | Tailwind CSS 3 | Utility-first CSS |
| Containerization | Docker + Compose | Reproducible dev environment |

---

## 7. Current Limitations

These are **known gaps** — not bugs. They define the remaining roadmap.

| Gap | Impact | When to Address |
|-----|--------|-----------------|
| No OCR pipeline | Scanned PDFs not extractable | After Agent 2 — use Tesseract or AWS Textract |
| No Agent 2 | No NLP analysis | Next milestone |
| No Agent 3 | No compliance scoring | After Agent 2 |
| No Agent 4 | No recommendations | After Agent 3 |
| No authentication | All users see all docs | Before production |
| No audit logs | No traceability | Before production |
| No anonymization | PII in storage | Before production |
| Local file storage only | Not scalable | When moving to cloud |
| Polling (not WebSocket) | 2s update latency | Nice-to-have improvement |
| No advanced security | No antivirus scan | Before production |

---

## 8. Design Principles

1. **Modularity**: Each agent is self-contained. Agent 2 doesn't know about Agent 4.
2. **Provider Pattern**: Document formats are plugins — new formats don't touch core logic.
3. **Async by Default**: Long-running tasks go to Celery. The API never blocks.
4. **Typed Everything**: Pydantic schemas for all I/O. SQLAlchemy models for all DB entities.
5. **Fail Gracefully**: Errors are caught, persisted, and surfaced to the user with retry capability.
6. **Progress Visibility**: Every long operation reports progress to the DB in real time.
7. **Clean Architecture**: API → Service → Provider → DB. No circular dependencies.
8. **LangGraph-First**: Multi-agent orchestration is built in from day one, not bolted on later.
