# How LexAI Works — Complete Technical Explanation

## Table of Contents
1. [Big Picture](#1-big-picture)
2. [What Happens When You Upload a Contract](#2-what-happens-when-you-upload-a-contract)
3. [Agent 1 — Extractor](#3-agent-1--extractor)
4. [Agent 2 — NLP Analyzer](#4-agent-2--nlp-analyzer)
5. [Agent 3 — Evaluator](#5-agent-3--evaluator)
6. [Agent 4 — Recommender](#6-agent-4--recommender)
7. [How the Models Work](#7-how-the-models-work)
8. [How the Orchestration Works (LangGraph)](#8-how-the-orchestration-works-langgraph)
9. [Data Flow Summary](#9-data-flow-summary)

---

## 1. Big Picture

LexAI is a **legal contract analysis platform** built specifically for the Tunisian legal context. It automates what a lawyer or compliance officer does manually:

1. Read a contract
2. Identify what each clause is about
3. Check if the clauses comply with Tunisian law (LNPDP), GDPR, and ISO standards
4. Suggest corrections for any non-compliant clauses

The system is split into **4 specialized AI agents** that run in sequence. Each agent does one job well and passes its result to the next agent. The agents are orchestrated by **LangGraph**, which acts like a traffic controller managing state between agents.

**Technology Stack:**
- **Backend**: FastAPI (REST API) + Celery (background task queue) + Redis (message broker) + PostgreSQL (database)
- **NLP**: spaCy (tokenization + NER) + HuggingFace Transformers (BERT-class classifiers)
- **LLM**: Llama 3 / Groq API (text generation for Agent 4)
- **Orchestration**: LangGraph state machine
- **Frontend**: React + TypeScript + Tailwind CSS

---

## 2. What Happens When You Upload a Contract

Here is the complete lifecycle of a document, from upload to final recommendations:

```
User uploads PDF/DOCX/TXT/HTML
         │
         ▼
FastAPI endpoint: POST /documents/upload
  - Validates MIME type and file size (max 50MB)
  - Saves file to disk
  - Creates a Document record in PostgreSQL (status = "queued")
  - Sends a task to the Celery queue
  - Returns document_id immediately (non-blocking)
         │
         ▼ (background, Celery worker picks up the task)
Agent 1 — Extractor
  - Reads the file → raw text
  - Normalizes text (UTF-8, line endings, whitespace)
  - Saves to Extraction table in DB
  - Sets status = "extracted"
         │
         ▼
Agent 2 — NLP Analyzer
  - Reads normalized_text from DB
  - Splits text into clause segments (sections/articles/paragraphs)
  - Classifies each clause (data_processing? liability? termination? etc.)
  - Extracts named entities from each clause (parties, roles, dates, amounts)
  - Detects compliance flags (missing retention period, missing consent, etc.)
  - Saves NLPAnalysis record to DB
  - Sets status = "analyzed"
         │
         ▼
Agent 3 — Evaluator
  - Reads clauses + compliance flags from DB
  - Loads legal rules from JSON files (LNPDP, GDPR, ISO 27001, ISO 9001)
  - Matches each clause against rules → produces violations
  - Computes a compliance score (0–100) per framework
  - Computes a global weighted score and litigation risk level
  - Saves EvaluationResult to DB
  - Sets status = "evaluated"
         │
         ▼
Agent 4 — Recommender
  - Reads violations from DB
  - For each violation, picks a recommendation template
  - Optionally: sends the clause + violation to Groq LLM for enhanced rewriting
  - Saves list of Recommendation records to DB
  - Sets status = "recommended"
         │
         ▼
Frontend polls /documents/{id} every 2 seconds
  → displays progress, then shows results in tabs:
    [Extraction] [NLP Analysis] [Compliance Score] [Recommendations] [Rewrite]
```

---

## 3. Agent 1 — Extractor

**Job**: Turn any document format into clean, normalized plain text.

### How It Extracts Text

Agent 1 uses the **Provider Pattern** — each file format has its own dedicated class:

| Format | Provider | Library | What it does |
|--------|----------|---------|--------------|
| PDF | `PdfProvider` | PyMuPDF (fitz) | Reads page by page, extracts text blocks, records page numbers |
| DOCX | `DocxProvider` | python-docx | Reads paragraphs and tables, detects headings by style |
| TXT | `TxtProvider` | built-in | Reads UTF-8, falls back to latin-1 if needed |
| HTML | `HtmlProvider` | BeautifulSoup4 | Strips `<script>`, `<style>`, extracts visible text |

A `ProviderRegistry` maps MIME types to the right provider. Adding a new format only requires adding one new class — nothing else changes.

### What It Produces

After extraction, a **Normalizer** cleans the text:
- Converts all encodings to valid UTF-8
- Converts `\r\n` (Windows) to `\n`
- Collapses multiple spaces within a line to one
- Collapses 3+ blank lines to 2 (preserves paragraph structure)
- Strips leading/trailing whitespace

The output saved to DB:
```json
{
  "raw_text": "...original extracted text...",
  "normalized_text": "...cleaned text...",
  "structure_json": {
    "sections": [
      {"title": "Objet du contrat", "level": 1, "start_char": 0},
      {"title": "Durée", "level": 1, "start_char": 520}
    ]
  },
  "page_metadata_json": {"pages": [{"page_number": 1, "char_count": 1200}]},
  "warnings": []
}
```

The `structure_json` is critical — Agent 1 detects headings (e.g., "Article 1 —", "SECTION 2") and records their character positions. Agent 2 uses these positions to know where clause boundaries are.

---

## 4. Agent 2 — NLP Analyzer

**Job**: Split the contract into clauses, classify each clause, extract entities, detect compliance gaps.

Agent 2 has three internal submodules that run in sequence on each document.

### Submodule A — ClauseSegmenter

Splits the full contract text into individual clause segments. It tries three strategies in order:

**Strategy 1 — Structure-based** (best quality, used when DOCX/PDF has headings)
Uses the `structure_json` from Agent 1. If Agent 1 detected sections at character positions 0, 520, 1040..., the segmenter simply cuts the text at those positions.

**Strategy 2 — Regex heading detection** (used when structure_json is empty)
Searches for patterns that look like article/section headers:
```
Article 3 — Durée du contrat       ← matched by regex
§5. Confidentialité                ← matched by regex
IV. CLAUSE DE NON-CONCURRENCE     ← matched by regex (ALL CAPS)
```
Each match starts a new clause segment.

**Strategy 3 — Paragraph breaks** (fallback for plain text)
Splits on double newlines (`\n\n`). Merges very short paragraphs into the previous segment to avoid creating 50+ tiny useless segments. Caps at 30 segments maximum.

Each clause gets an ID like `c-001`, `c-002`, etc.

### Submodule B — ClauseClassifier

Labels each clause with one or more **clause types** from a fixed taxonomy of 12 types:

```
definition, obligation, liability, termination, data_processing,
confidentiality, dispute_resolution, force_majeure, penalty,
ip_rights, payment, warranty
```

It also detects **compliance flags** — specific legal gaps:
```
lnpdp_relevant, gdpr_relevant, missing_retention_period,
missing_consent_mechanism, missing_security_measures,
missing_data_subject_rights, unlawful_cross_border_transfer
```

The classifier tries three models in order (see Section 7 for full model details):

1. **Fine-tuned BERT model** (`data/models/clause_classifier/`) — trained on CUAD + LEDGAR datasets
2. **Zero-shot XLM-RoBERTa** — uses NLI (natural language inference) without any training
3. **Keyword heuristics** — simple French keyword matching, always works offline

Compliance flags are only attached to data-relevant clauses to avoid false positives (e.g., a `force_majeure` clause never gets a "missing retention period" flag).

### Submodule C — EntityExtractor

Extracts named entities from each clause. It knows about 8 legal entity types:

| Entity Type | Examples |
|------------|---------|
| `PARTY` | "Société XYZ S.A.", "M. Jean Dupont" |
| `ROLE` | "responsable du traitement", "DPO", "sous-traitant" |
| `DATA_CATEGORY` | "données personnelles", "données de santé" |
| `DURATION` | "30 jours", "5 ans", "pendant la durée du contrat" |
| `AMOUNT` | "50 000 DT", "10%" |
| `LAW_REFERENCE` | "LNPDP", "Art. 23", "RGPD", "loi n°2004-63" |
| `JURISDICTION` | "Tunisie", "Union européenne", "France" |
| `DATE` | "1er janvier 2025", "31/12/2024" |

Two extraction methods run together:

- **spaCy model**: A neural NER model (fine-tuned `ner_model` or generic `fr_core_news_lg`) handles general entities (persons, organizations, dates, amounts).
- **Rule-based regex patterns**: 30+ hand-crafted regex patterns specifically for legal entities that spaCy misses (e.g., "responsable du traitement", "loi n°2004-63", "données à caractère personnel").

Results from both are merged, with deduplication by character overlap.

### Agent 2 Output

```json
{
  "document_id": 42,
  "clause_count": 12,
  "model_used": "finetuned/clause_classifier",
  "risk_level": "medium",
  "compliance_score": 67.3,
  "language": "fr",
  "clauses": [
    {
      "clause_id": "c-001",
      "text": "Le responsable du traitement s'engage à...",
      "section_title": "Traitement des données personnelles",
      "labels": ["data_processing", "obligation"],
      "compliance_flags": ["lnpdp_relevant", "missing_retention_period"],
      "entities": [
        {"text": "responsable du traitement", "label": "ROLE", "confidence": 1.0},
        {"text": "données personnelles", "label": "DATA_CATEGORY", "confidence": 1.0}
      ],
      "confidence": 0.91,
      "language": "fr",
      "model_used": "finetuned/clause_classifier"
    }
  ]
}
```

---

## 5. Agent 3 — Evaluator

**Job**: Compare clauses against legal rules → produce violations → compute a compliance score.

### Rule Engine

Agent 3 loads rules from 4 JSON files in `backend/app/legal/rules/`:
- `lnpdp.json` — Tunisian data protection law (Loi n°2004-63)
- `gdpr.json` — European GDPR / RGPD
- `iso27001.json` — Information security management
- `iso9001.json` — Quality management

Each rule looks like this (simplified):
```json
{
  "rule_id": "LNPDP-001",
  "framework": "LNPDP",
  "article": "Art. 23",
  "title": "Durée de conservation non définie",
  "description": "Tout traitement doit préciser la durée de conservation des données",
  "severity": "high",
  "triggers_on_flags": ["missing_retention_period"],
  "remediation_hint": "Précisez la durée maximale de conservation dans la clause de traitement"
}
```

**Framework activation**: Before checking rules, Agent 3 decides which frameworks apply to this specific contract. LNPDP activates if any clause has `lnpdp_relevant` or `data_processing` labels. GDPR activates if `gdpr_relevant` is flagged. This avoids penalizing a simple employment contract for "missing GDPR DPO reference."

**Violation matching**: For each rule in active frameworks, Agent 3 checks if the document's compliance flags match the rule's trigger conditions. If yes, a `Violation` object is created. Each rule fires at most once per document to avoid duplicate violations.

**Mandatory clause check**: Some clauses are legally required to exist (e.g., a data processing agreement must have a data retention clause). If they're missing from the entire document, a document-level violation is created.

### Scorer

Once all violations are collected, the scorer computes a score:

```
For each active framework F:
  score(F) = max(0, 100 - Σ severity_weight(violation))

Where:
  critical violation → -30 points
  high violation     → -20 points
  medium violation   → -10 points
  low violation      →  -5 points

global_score = weighted average of framework scores
  (LNPDP weight: 0.40, GDPR weight: 0.35, ISO 27001 weight: 0.15, ISO 9001 weight: 0.10)
```

The global score maps to a litigation risk level:
- **≥ 80**: Low risk — contract is largely compliant
- **60–79**: Medium risk — some corrections needed
- **40–59**: High risk — significant compliance gaps
- **< 40**: Critical risk — contract should not be signed as-is

---

## 6. Agent 4 — Recommender

**Job**: Turn each violation into an actionable recommendation, optionally enhanced by an LLM.

### Template Engine

Agent 4 loads `backend/app/legal/templates/recommendations_fr.json` — a library of French-language recommendation templates keyed by `rule_id`.

For violation `LNPDP-001`, the template might contain:
```json
{
  "rule_id": "LNPDP-001",
  "recommendation_text": "Ajoutez une clause précisant que les données personnelles collectées seront conservées pendant {DURATION} maximum.",
  "rewritten_clause": "Les données à caractère personnel collectées dans le cadre du présent contrat seront conservées pour une durée maximale de {DURATION}, à compter de la fin de la relation contractuelle...",
  "slots": {
    "DURATION": {"entity_label": "DURATION", "default": "5 ans"}
  }
}
```

The `{DURATION}` slot is filled by looking up `DURATION` entities that Agent 2 already extracted from that clause. If Agent 2 found "30 jours" in the clause, the template uses it. If not, it falls back to the default "5 ans".

### LLM Enhancement (Optional)

If `LLM_API_KEY` is configured in the environment, Agent 4 also calls the Groq API with `llama3-70b-8192`. It sends:
- The original clause text
- The detected violations
- The legal framework and article reference
- A French-language prompt asking for a compliant rewrite

The LLM response is merged with the template output, producing a richer, more context-aware recommendation. If the API is unavailable or the key is missing, the template-only output is used as a fallback.

### Rewrite Session

Users can then interact with recommendations in the UI:
- **Accept**: Use the AI-proposed rewrite
- **Reject**: Keep reviewing
- **Keep Original**: Explicitly decide the original clause is fine

When satisfied, clicking "Generate revised contract" merges accepted rewrites with the original normalized text and exports a new DOCX or PDF.

---

## 7. How the Models Work

### Model 1 — Clause Classifier (HuggingFace Transformers)

**Purpose**: Multi-label classification — given a clause text, output one or more clause type labels.

**Architecture**: BERT-based transformer (CamemBERT for French, XLM-RoBERTa for multilingual). The model reads the clause text (up to 512 tokens) and outputs a probability score for each of the 12 clause types.

**Three modes, tried in this order:**

#### Mode A — Fine-tuned model (best accuracy)
A BERT model was fine-tuned on a dataset combining:
- **CUAD** (Contract Understanding Atticus Dataset) — 510 annotated contracts, English legal
- **LEDGAR** — 60,000+ labeled contract provisions
- **Synthetic French contracts** — generated by `scripts/generate_synthetic.py`

Training ran via `scripts/train_classifier.py` using HuggingFace `Trainer`. The output model lives at `data/models/clause_classifier/`. It has been excluded from git (too large for GitHub) but lives on your server.

At inference time:
```python
pipe = pipeline("text-classification", model="data/models/clause_classifier/", top_k=None)
result = pipe(clause_text[:512])
# Returns: [{"label": "data_processing", "score": 0.92}, {"label": "obligation", "score": 0.71}, ...]
# Labels with score >= 0.40 are kept
```

#### Mode B — Zero-shot XLM-RoBERTa (no training needed)
If no fine-tuned model is found, the system downloads `joelniklaus/legal-xlm-roberta-large` — a model pre-trained on legal text in multiple languages. It uses **Natural Language Inference (NLI)**:

For each candidate label (e.g., "data_processing"), the model answers the question: "Does this clause entail that it is about data_processing?" Labels with entailment score ≥ 0.25 are kept.

This works without any training data but is slower and slightly less accurate than the fine-tuned model.

#### Mode C — Keyword heuristics (offline fallback)
If no GPU/internet is available, the classifier scans for French legal keywords:
- "données personnelles" → `data_processing`
- "confidentiel", "divulguer" → `confidentiality`
- "résiliation", "préavis" → `termination`
- etc.

No model files required. Always works. Less accurate but never fails.

**Model loading is lazy and cached**: The model is loaded once on the first classification call and kept in memory for the entire Celery worker lifetime. Subsequent tasks reuse the same loaded model.

---

### Model 2 — Named Entity Recognizer (spaCy)

**Purpose**: Extract spans of text that are legal entities (parties, roles, dates, amounts, etc.).

**Architecture**: spaCy's NER pipeline — a Transition-based parser over token embeddings. It reads a sequence of word tokens and predicts which tokens form entity spans.

**Two modes:**

#### Mode A — Fine-tuned spaCy NER model
`data/models/ner_model/` — trained by `scripts/train_ner.py` on synthetic French legal contracts. The training data was generated by `scripts/generate_synthetic.py`, which creates realistic contract snippets with manually defined entity spans for all 8 legal entity types.

spaCy training uses its native `train` command with a custom config. The resulting model replaces generic entity types (`PER`, `ORG`) with legal-domain ones (`PARTY`, `ROLE`, `DATA_CATEGORY`, etc.).

#### Mode B — Generic French model + regex rules
If the fine-tuned model is absent, `fr_core_news_lg` (a spaCy model trained on French news) is used for baseline NER. It catches persons, organizations, dates, and amounts. The regex rule layer (30+ patterns) then supplements it with legal-specific entities that news models miss.

---

### Model 3 — LLM (Llama 3 via Groq)

**Purpose**: Generate fluent, legally-informed clause rewrites in French.

**Architecture**: Llama 3 70B — a large autoregressive language model. It receives a structured prompt and generates text token by token.

**How Agent 4 uses it:**
```
Prompt structure (simplified):
  System: "Tu es un expert juridique spécialisé en droit tunisien et RGPD..."
  User: "Clause originale: {clause_text}
         Violations détectées: {violations}
         Réécris cette clause pour la rendre conforme à {framework} {article}."

Model responds with a JSON object:
  {
    "rewritten_clause": "Les données à caractère personnel...",
    "legal_rationale": "Conformément à l'Art. 23 de la LNPDP..."
  }
```

The API call goes to `https://api.groq.com/openai/v1/chat/completions` using an OpenAI-compatible interface. Groq provides very fast inference (Llama 3 at ~700 tokens/sec) compared to self-hosting.

If the API key is missing or the call fails, Agent 4 silently falls back to the template-based rewrite — the UI just shows "Template" instead of "AI Enhanced" on the badge.

---

## 8. How the Orchestration Works (LangGraph)

LangGraph manages the state passed between agents. Think of it as a typed dictionary that each agent reads from and writes to:

```python
class AnalysisState(TypedDict):
    document_id: int
    normalized_text: str          # written by Agent 1, read by Agent 2
    clauses: list[dict]           # written by Agent 2, read by Agents 3 & 4
    findings: list[dict]          # written by Agent 3, read by Agent 4
    scores: dict                  # written by Agent 3
    recommendations: list[dict]   # written by Agent 4
    errors: list[str]             # any agent can write errors here
    audit_trace: list[dict]       # each node logs its execution
```

The graph is a linear pipeline:
```
validate_input → extract_document → nlp_analyze_document → evaluate_document → recommend_clauses → END
```

Each node is a Python function that receives the current `AnalysisState`, does its work, and returns a partial state update (only the keys it changed). LangGraph merges the update into the shared state.

In practice, each agent also persists its output directly to PostgreSQL (not just to LangGraph state), so the frontend can read partial results as each agent completes — you don't have to wait for all 4 agents to finish before seeing any results.

---

## 9. Data Flow Summary

```
PDF file
  │
  ▼ Agent 1
normalized_text = "Article 1 — Objet\nLe présent contrat a pour objet..."
structure_json  = [{"title": "Objet", "start_char": 0}, {"title": "Durée", "start_char": 520}]
  │
  ▼ Agent 2 (ClauseSegmenter)
clauses = [
  ClauseSegment(id="c-001", text="Article 1 — Objet\nLe présent...", section_title="Objet"),
  ClauseSegment(id="c-002", text="Article 2 — Durée\nLe contrat est...", section_title="Durée"),
  ...
]
  │
  ▼ Agent 2 (ClauseClassifier + EntityExtractor)
clauses = [
  {
    "clause_id": "c-001",
    "labels": ["obligation"],
    "compliance_flags": [],
    "entities": [{"text": "prestataire", "label": "ROLE"}],
    "confidence": 0.88
  },
  {
    "clause_id": "c-004",
    "labels": ["data_processing", "obligation"],
    "compliance_flags": ["lnpdp_relevant", "missing_retention_period", "missing_consent_mechanism"],
    "entities": [
      {"text": "données personnelles", "label": "DATA_CATEGORY"},
      {"text": "responsable du traitement", "label": "ROLE"}
    ],
    "confidence": 0.93
  }
]
  │
  ▼ Agent 3 (RuleEngine + Scorer)
violations = [
  {
    "rule_id": "LNPDP-001",
    "framework": "LNPDP",
    "article": "Art. 23",
    "severity": "high",
    "clause_id": "c-004",
    "description": "Durée de conservation non spécifiée"
  },
  {
    "rule_id": "LNPDP-002",
    "framework": "LNPDP",
    "article": "Art. 24",
    "severity": "high",
    "clause_id": "c-004",
    "description": "Base légale du consentement absente"
  }
]
scores = {
  "global_score": 67.3,
  "litigation_risk": "medium",
  "framework_scores": {"LNPDP": 60.0, "GDPR": 72.5}
}
  │
  ▼ Agent 4 (Recommender + optional LLM)
recommendations = [
  {
    "framework": "LNPDP",
    "article": "Art. 23",
    "severity": "high",
    "issue_description": "Durée de conservation non spécifiée",
    "recommendation_text": "Ajoutez une clause précisant la durée maximale de conservation...",
    "rewritten_clause": "Les données à caractère personnel collectées seront conservées pour une durée maximale de 5 ans...",
    "legal_rationale": "L'Art. 23 de la LNPDP impose de préciser la durée de conservation.",
    "generated_by": "llm_v2"
  }
]
  │
  ▼ Frontend
User sees: compliance score 67/100 · risk: medium · 2 violations · 2 recommendations
User accepts rewrite for c-004 → exports revised DOCX
```

---

*Generated from source code of the LexAI platform — all details reflect actual implementation.*
