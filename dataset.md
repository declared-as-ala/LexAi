# Dataset Strategy — LegalTech AI Platform

> This document defines every dataset required to build and train Agents 2, 3, and 4.
> It covers what to collect, where to find it, how to annotate it, and how to structure it on disk.

---

## Overview

The system needs three categories of data:

| Category | Used By | Effort |
|----------|---------|--------|
| Raw contracts (PDF/DOCX) | Agent 1 input, Agent 2 training | Medium — collect files |
| Legal reference texts | Agent 3 rule engine, Agent 4 RAG | Low — public documents |
| Annotated clause dataset | Agent 2 fine-tuning, Agent 3 ML | High — manual annotation |

---

## 1. Raw Contract Corpus

### What It Is
A collection of real legal contracts in French and/or Arabic covering common contract types used in Tunisia.

### Target Volume
- **Minimum**: 50 contracts to start annotation
- **Target**: 200+ contracts for a robust model
- **Format**: PDF or DOCX (Agent 1 handles both)

### Contract Types to Collect

| Type | Description | Why Important |
|------|-------------|---------------|
| Contrat de prestation de services | Service agreements between companies | Most common B2B contract |
| Contrat de travail | Employment contracts | High LNPDP relevance (employee data) |
| Accord de confidentialité (NDA) | Non-disclosure agreements | Heavy confidentiality clause coverage |
| Contrat de traitement de données | Data processing agreements (DPA) | Core LNPDP/GDPR relevance |
| Contrat commercial | Commercial supply/distribution contracts | COC coverage |
| Contrat de sous-traitance | Subcontracting agreements | Multi-party data flow |
| Conditions Générales d'Utilisation | Terms of service / CGU | Consumer-facing data clauses |

### Where to Find Them

#### Free / Public Sources
- **Marchés publics tunisiens** — `www.marchespublics.gov.tn` — public procurement contracts published by Tunisian government agencies
- **INNORPI** — standardized contract templates published by the Tunisian standards institute
- **Journal Officiel de la République Tunisienne (JORT)** — `www.legislation.tn` — legal texts and official contracts
- **OpenLex Tunisia** — open legal document initiatives
- **EUR-Lex** — French-language EU contracts and agreements (useful for GDPR-relevant DPAs)

#### Internal / Private Sources
- Your own firm or client contracts (anonymize before use)
- Law firm template libraries
- Academic legal repositories

### Storage
```
data/raw/contracts/
├── services/
│   ├── contract_001.pdf
│   └── contract_002.docx
├── employment/
│   ├── contract_003.pdf
│   └── ...
├── nda/
├── data_processing/
├── commercial/
└── subcontracting/
```

> **Important**: Add `data/raw/contracts/` to `.gitignore`. Real contracts contain PII and must not be committed to version control.

---

## 2. Legal Reference Texts

### What They Are
The full text of legal frameworks that define compliance rules. Used by:
- **Agent 3** rule engine (to define what is/isn't compliant)
- **Agent 4** RAG retriever (to ground LLM recommendations in real law)

### Required Texts

#### 2.1 LNPDP — Loi Organique n°2004-63 (PRIMARY)
- **Full name**: Loi organique n° 2004-63 du 27 juillet 2004 portant sur la protection des données à caractère personnel
- **Language**: French + Arabic
- **Source**: `www.legislation.tn` or INPDP official website
- **Why critical**: Defines all Tunisian data protection obligations — consent, retention, DPO, cross-border transfer, rights of data subjects
- **Key articles to extract**:
  - Art. 4 — Definitions (données personnelles, responsable du traitement)
  - Art. 6 — Conditions of lawful processing
  - Art. 7 — Consent requirements
  - Art. 23 — Data retention obligations
  - Art. 46 — Cross-border transfer restrictions
  - Art. 51–57 — Sanctions

#### 2.2 COC — Code des Obligations et Contrats (PRIMARY)
- **Full name**: Code des Obligations et Contrats tunisien (Décret du 15 décembre 1906 et modifications)
- **Language**: French + Arabic
- **Source**: `www.legislation.tn`
- **Why critical**: Governs general contract validity, obligations, liability, and termination in Tunisia
- **Key articles to extract**:
  - Art. 2–23 — Formation and validity of contracts
  - Art. 230–280 — Effects of obligations
  - Art. 281–316 — Liability for non-performance
  - Art. 752–836 — Service contracts
  - Art. 1099–1108 — Termination and cancellation

#### 2.3 RGPD / GDPR (SECONDARY)
- **Full name**: Règlement Général sur la Protection des Données (EU 2016/679)
- **Language**: French (official EU translation)
- **Source**: `eur-lex.europa.eu`
- **Why needed**: Many Tunisian contracts with EU clients reference GDPR obligations; required for DPAs
- **Key articles to extract**:
  - Art. 5 — Principles of processing
  - Art. 6 — Legal basis for processing
  - Art. 13–14 — Information obligations
  - Art. 17 — Right to erasure
  - Art. 28 — Processor obligations (DPA requirements)
  - Art. 32 — Security measures
  - Art. 35 — DPIA requirements
  - Art. 44–49 — Cross-border transfer rules

#### 2.4 INPDP Guidelines (SUPPLEMENTARY)
- **Source**: `www.inpdp.nat.tn` — official Tunisian data protection authority
- **Content**: Guidance notes, recommendations, and decisions interpreting LNPDP
- **Why useful**: Practical interpretation of LNPDP articles for compliance rules

### Storage
```
data/raw/legal_refs/
├── lnpdp_2004_63_fr.txt          # Full French text
├── lnpdp_2004_63_ar.txt          # Full Arabic text
├── coc_tunisien_fr.txt            # COC full text
├── gdpr_2016_679_fr.txt           # GDPR French version
├── inpdp_guidelines/
│   ├── guide_consentement.pdf
│   └── guide_transfert_international.pdf
└── extracted/
    ├── lnpdp_articles.json        # Structured per-article JSON
    ├── coc_articles.json
    └── gdpr_articles.json
```

### Article JSON Format (for RAG indexing)
```json
{
  "framework": "LNPDP",
  "article_id": "LNPDP_Art23",
  "article_number": "23",
  "title": "Conservation des données",
  "text": "Les données à caractère personnel ne peuvent être conservées sous une forme permettant l'identification des personnes concernées au-delà de la durée nécessaire...",
  "keywords": ["conservation", "durée", "données personnelles", "retention"],
  "related_articles": ["LNPDP_Art6", "GDPR_Art5_1e"]
}
```

---

## 3. Annotated Clause Dataset

### What It Is
The core training dataset for Agent 2 (clause classification + NER) and Agent 3 (risk classification). Built by running Agent 1 on raw contracts, segmenting them into clauses, and manually annotating each clause.

### Annotation Dimensions

Each clause gets annotated across 4 dimensions:

#### 3.1 Clause Type (Multi-Label Classification)
```
definition              — defines terms used in the contract
obligation              — imposes duties on one or both parties
liability               — limits or assigns liability
termination             — defines when/how contract ends
data_processing         — describes how personal data is handled
confidentiality         — covers information secrecy obligations
dispute_resolution      — covers arbitration, jurisdiction, governing law
force_majeure           — covers exceptional circumstances / act of God
penalty                 — fines, damages, breach consequences
ip_rights               — intellectual property ownership/licensing
payment                 — payment terms, amounts, schedules
warranty                — guarantees about service/product quality
```

#### 3.2 Compliance Flags (Multi-Label)
```
lnpdp_relevant                — clause triggers LNPDP obligations
gdpr_relevant                 — clause triggers GDPR obligations
missing_retention_period      — data processing clause lacks retention duration
missing_consent_mechanism     — no valid consent basis specified
missing_dpo_reference         — no DPO contact when required
excessive_data_collection     — data collected beyond stated purpose
missing_security_measures     — no technical/organizational measures specified
unlawful_cross_border_transfer — data transferred abroad without safeguards
missing_data_subject_rights   — fails to mention data subject rights
unclear_liability_cap         — liability limitation is ambiguous or missing
```

#### 3.3 Named Entity Spans (Token-Level NER)
```
PARTY           — contracting parties (company or person names)
ROLE            — responsable du traitement, sous-traitant, DPO, prestataire
DATA_CATEGORY   — données personnelles, données sensibles, données de santé
DURATION        — 30 jours, 5 ans, pendant la durée du contrat
AMOUNT          — monetary values, percentages, quantities
LAW_REFERENCE   — LNPDP, RGPD, Art. 23, Loi n°2004-63
JURISDICTION    — Tunisie, Union européenne, territoire national
DATE            — specific dates or date ranges
```

#### 3.4 Compliance Verdict
```json
{
  "compliant": false,
  "violation_refs": ["LNPDP_Art23", "GDPR_Art5_1e"],
  "severity": "high",
  "comment": "Retention period not specified for personal data processing"
}
```

### Full Annotated Clause Format
```json
{
  "doc_id": "contract_042",
  "doc_type": "data_processing",
  "language": "fr",
  "clause_id": "c-042-007",
  "text": "Le prestataire s'engage à traiter les données personnelles des utilisateurs uniquement pour les finalités définies au contrat et à les conserver de manière sécurisée.",
  "start_char": 1842,
  "end_char": 2031,
  "section_title": "Article 7 — Protection des données",
  "labels": ["data_processing", "obligation"],
  "compliance_flags": ["lnpdp_relevant", "gdpr_relevant", "missing_retention_period"],
  "entities": [
    {"text": "prestataire", "label": "ROLE", "start": 3, "end": 14},
    {"text": "données personnelles", "label": "DATA_CATEGORY", "start": 40, "end": 60},
    {"text": "finalités définies au contrat", "label": "DATA_CATEGORY", "start": 102, "end": 131}
  ],
  "compliant": false,
  "violation_refs": ["LNPDP_Art23"],
  "severity": "high",
  "comment": "No retention period specified. LNPDP Art. 23 requires explicit duration."
}
```

### Target Volume

| Split | Contracts | Clauses | Purpose |
|-------|-----------|---------|---------|
| Train | 40 | ~1,600 | Model fine-tuning |
| Val | 5 | ~200 | Hyperparameter tuning |
| Test | 5 | ~200 | Final evaluation |
| **Total** | **50** | **~2,000** | Minimum viable dataset |

Expand to 200 contracts / ~8,000 clauses for production-quality models.

### Storage
```
data/annotated/
├── train/
│   ├── contract_001_clauses.json
│   ├── contract_002_clauses.json
│   └── ...
├── val/
│   ├── contract_041_clauses.json
│   └── ...
└── test/
    ├── contract_046_clauses.json
    └── ...
```

---

## 4. Pre-Trained Models (No Collection Needed)

These are downloaded from HuggingFace Hub — no annotation required.

| Model | Task | HuggingFace ID | Notes |
|-------|------|----------------|-------|
| CamemBERT | French clause classification | `camembert-base` | Best for French-only contracts |
| XLM-RoBERTa | Multilingual classification | `xlm-roberta-base` | Handles French + Arabic |
| XLM-RoBERTa Large XNLI | Zero-shot classification | `joeddav/xlm-roberta-large-xnli` | Use before fine-tuning |
| Legal-BERT | English legal NLP | `nlpaueb/legal-bert-base-uncased` | Reference only — English |
| Multilingual E5 | Embeddings for RAG | `intfloat/multilingual-e5-base` | For Agent 4 retriever |
| Sentence Transformers | Embeddings for RAG | `paraphrase-multilingual-mpnet-base-v2` | Alternative for RAG |

### Zero-Shot Strategy (Start Immediately, No Data Needed)

Before any annotation, use zero-shot classification to get a working prototype:

```python
from transformers import pipeline

classifier = pipeline(
    "zero-shot-classification",
    model="joeddav/xlm-roberta-large-xnli"
)

clause = "Le prestataire s'engage à traiter les données personnelles..."
labels = ["data_processing", "confidentiality", "liability", "termination", "obligation"]

result = classifier(clause, candidate_labels=labels, multi_label=True)
# Returns scores per label — no training required
```

Zero-shot accuracy is ~60–70%. Fine-tuning on 2,000 annotated clauses brings it to ~85–90%.

---

## 5. Annotation Workflow

### Tool: Label Studio (Free, Open Source)

```bash
pip install label-studio
label-studio start
# Opens at http://localhost:8080
```

### Label Studio Configuration

Create a project with this interface template:

```xml
<View>
  <Text name="text" value="$text"/>

  <!-- Clause Type Labels -->
  <Choices name="clause_type" toName="text" choice="multiple">
    <Choice value="data_processing"/>
    <Choice value="confidentiality"/>
    <Choice value="liability"/>
    <Choice value="termination"/>
    <Choice value="obligation"/>
    <Choice value="penalty"/>
    <Choice value="dispute_resolution"/>
    <Choice value="force_majeure"/>
    <Choice value="ip_rights"/>
    <Choice value="definition"/>
  </Choices>

  <!-- Compliance Flags -->
  <Choices name="compliance_flags" toName="text" choice="multiple">
    <Choice value="lnpdp_relevant"/>
    <Choice value="gdpr_relevant"/>
    <Choice value="missing_retention_period"/>
    <Choice value="missing_consent_mechanism"/>
    <Choice value="missing_security_measures"/>
    <Choice value="missing_data_subject_rights"/>
  </Choices>

  <!-- Named Entity Annotation -->
  <Labels name="entities" toName="text">
    <Label value="PARTY" background="#FF6B6B"/>
    <Label value="ROLE" background="#4ECDC4"/>
    <Label value="DATA_CATEGORY" background="#45B7D1"/>
    <Label value="DURATION" background="#96CEB4"/>
    <Label value="LAW_REFERENCE" background="#FFEAA7"/>
    <Label value="JURISDICTION" background="#DDA0DD"/>
    <Label value="DATE" background="#98D8C8"/>
  </Labels>

  <!-- Compliance Verdict -->
  <Choices name="compliant" toName="text" choice="single">
    <Choice value="compliant"/>
    <Choice value="non_compliant"/>
    <Choice value="uncertain"/>
  </Choices>
</View>
```

### Annotation Pipeline

```
Step 1: Run Agent 1 on raw contracts → normalized_text stored in DB

Step 2: Run clause segmenter script → pre-segment into clauses
        python scripts/segment_for_annotation.py --input data/raw/contracts/ \
                                                  --output data/processed/segmented/

Step 3: Import clause segments into Label Studio
        python scripts/import_to_labelstudio.py --input data/processed/segmented/ \
                                                 --project-id 1

Step 4: Annotators label each clause in Label Studio UI
        (target: 1 annotator × 2 weeks = ~50 contracts)

Step 5: Export annotations from Label Studio → JSON
        python scripts/export_annotations.py --project-id 1 \
                                             --output data/annotated/

Step 6: Split into train/val/test
        python scripts/train_val_test_split.py --input data/annotated/ \
                                               --train 0.8 --val 0.1 --test 0.1
```

### Inter-Annotator Agreement
If you have multiple annotators, compute Cohen's Kappa before training:
```bash
python scripts/compute_iaa.py --annotator1 annotator1.json --annotator2 annotator2.json
# Target kappa > 0.7 for reliable training data
```

---

## 6. Data Augmentation

To expand beyond 50 contracts without more annotation effort:

### 6.1 Back-Translation (French → Arabic → French)
```python
# Use Helsinki-NLP translation models
from transformers import pipeline

fr_to_ar = pipeline("translation", model="Helsinki-NLP/opus-mt-fr-ar")
ar_to_fr = pipeline("translation", model="Helsinki-NLP/opus-mt-ar-fr")

augmented = ar_to_fr(fr_to_ar(clause_text)[0]["translation_text"])[0]["translation_text"]
# Paraphrases the clause — adds variety without changing meaning
```

### 6.2 Synonym Replacement
Replace legal terms with known synonyms:
```python
synonyms = {
    "responsable du traitement": ["contrôleur des données", "responsable de traitement"],
    "données personnelles": ["données à caractère personnel", "informations personnelles"],
    "prestataire": ["fournisseur", "sous-traitant", "partie prestataire"],
}
```

### 6.3 LLM Synthetic Generation (After Agent 4 is Built)
Once Agent 4 is operational, generate synthetic contract clauses:
```
Prompt: "Génère 5 variations d'une clause de traitement de données non conforme 
         à l'article 23 de la LNPDP (sans période de conservation). 
         Chaque clause doit être différente et réaliste."
```
Label synthetics as `compliant=false` + appropriate `violation_refs`. Use only to augment — not as primary training data.

---

## 7. Dataset Quality Checklist

Before using the dataset for training, verify:

- [ ] No raw PII from real contracts has been committed to git
- [ ] Every clause has at least one `clause_type` label
- [ ] Every `lnpdp_relevant` or `gdpr_relevant` clause has a `compliant` verdict
- [ ] Every `compliant=false` clause has at least one `violation_refs` entry
- [ ] Entity spans do not overlap
- [ ] Entity span character offsets match the actual text
- [ ] Train/val/test splits are stratified by clause type (no class only in test)
- [ ] Inter-annotator agreement kappa > 0.7 (if multiple annotators)
- [ ] Class distribution is logged — oversample minority classes if needed

---

## 8. Dataset Folder Summary

```
data/
├── .gitignore                      # Exclude raw/contracts/ from git
├── raw/
│   ├── contracts/                  # Original PDFs and DOCX (NOT in git)
│   │   ├── services/
│   │   ├── employment/
│   │   ├── nda/
│   │   ├── data_processing/
│   │   ├── commercial/
│   │   └── subcontracting/
│   └── legal_refs/                 # Legal framework texts
│       ├── lnpdp_2004_63_fr.txt
│       ├── lnpdp_2004_63_ar.txt
│       ├── coc_tunisien_fr.txt
│       ├── gdpr_2016_679_fr.txt
│       └── inpdp_guidelines/
├── processed/
│   ├── extracted/                  # Agent 1 output JSONs per document
│   └── segmented/                  # Pre-segmented clause JSONs for annotation
├── annotated/
│   ├── train/                      # 80% — annotated clause JSONs
│   ├── val/                        # 10%
│   └── test/                       # 10%
└── models/
    ├── clause_classifier/          # Fine-tuned CamemBERT/XLM-R checkpoint
    ├── ner_model/                  # Fine-tuned NER model
    └── risk_classifier/            # XGBoost risk model (.pkl)
```

---

## 9. Build Order

| Phase | Action | Output | Blocks |
|-------|--------|--------|--------|
| P1 | Collect 50 raw contracts + legal texts | `data/raw/` | Nothing — start now |
| P2 | Run Agent 1 on all contracts | Extractions in DB | Agent 2 segmenter |
| P3 | Run segmenter → import to Label Studio | Pre-annotated tasks | Human annotation |
| P4 | Annotate 50 contracts (2–3 weeks) | `data/annotated/` | Agent 2 fine-tuning |
| P5 | Fine-tune CamemBERT / XLM-R | `data/models/clause_classifier/` | Agent 2 production |
| P6 | Add compliance labels → train XGBoost | `data/models/risk_classifier/` | Agent 3 ML |
| P7 | Index legal texts in FAISS/ChromaDB | Vector store | Agent 4 RAG |
