# Agent 2 — Complete Step-by-Step Guide to Finish

> **Start here.** You already downloaded the datasets. Follow every step in order.
> Each step has a command, what it does, and what you should see when it works.

---

## Current Status

| What | Status |
|------|--------|
| Datasets downloaded (CUAD + LEDGAR) | ✅ Done |
| PyTorch installed | ❌ BROKEN — DLL error (fix in Step 1) |
| spaCy installed | ❌ BROKEN — depends on PyTorch |
| transformers installed | ✅ OK (version 5.5.4) |
| scikit-learn installed | ✅ OK |
| CUAD converted | ❌ Not done yet |
| LEDGAR converted | ❌ Not done yet |
| French synthetic data generated | ❌ Not done yet |
| Final train/val/test dataset built | ❌ Not done yet |
| Classifier model trained | ❌ Not done yet |
| NER model trained | ❌ Not done yet |
| Agent 2 tested end-to-end | ❌ Not done yet |

---

## STEP 1 — Fix PyTorch (REQUIRED — do this first)

### The Problem
PyTorch 2.11.0 fails to load with this error:
```
OSError: [WinError 1114] A dynamic link library (DLL) initialization routine failed.
Error loading "torch\lib\c10.dll"
```
This happens because the installed torch version requires Visual C++ Redistributable or CUDA DLLs that are missing.

### The Fix — Reinstall PyTorch (CPU version, works without GPU)

Open a terminal in your project folder and run:

```bash
# Uninstall broken torch
.venv\Scripts\pip uninstall torch torchvision torchaudio -y

# Install CPU-only torch (always works on Windows, no DLL issues)
.venv\Scripts\pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

### Verify it works
```bash
.venv\Scripts\python -c "import torch; print('PyTorch OK:', torch.__version__)"
```
Expected output: `PyTorch OK: 2.x.x+cpu`

> **Note:** If you have an NVIDIA GPU and want to use it for faster training,
> install the CUDA version instead. Check your CUDA version first with `nvcc --version`,
> then visit pytorch.org to find the right install command for your CUDA version.

---

## STEP 2 — Fix spaCy + Download French Language Model

After fixing PyTorch in Step 1, reinstall spaCy and download the French model:

```bash
# Reinstall spaCy (it will now work because torch is fixed)
.venv\Scripts\pip install spacy

# Download the French language model (required for NER training)
.venv\Scripts\python -m spacy download fr_core_news_lg
```

### Verify it works
```bash
.venv\Scripts\python -c "import spacy; nlp = spacy.load('fr_core_news_lg'); print('spaCy OK:', spacy.__version__)"
```
Expected output: `spaCy OK: 3.x.x`

---

## STEP 3 — Convert CUAD Dataset

CUAD is in SQuAD question-answer format. This script converts it to our unified format
where each paragraph becomes a record with clause type labels.

```bash
.venv\Scripts\python scripts/convert_cuad.py
```

### What it does
- Reads `data/raw/datasets/cuad/CUAD_v1.json` (510 contracts, 20,910 QA pairs)
- For each paragraph: finds which of the 41 clause types are present (have answers)
- Maps those clause types to our 12 labels (termination, liability, ip_rights, etc.)
- Groups labels per paragraph, deduplicates

### Expected output
```
  Reading data/raw/datasets/cuad/CUAD_v1.json ...
  510 contracts found

CUAD converted: 4,XXX unique clause paragraphs -> data/raw/datasets/cuad_converted/cuad_clauses.json
Label distribution:
  obligation: XXXX
  termination: XXX
  dispute_resolution: XXX
  ...
```

### Output file
```
data/raw/datasets/cuad_converted/cuad_clauses.json
```
Each record looks like:
```json
{
  "text": "This Agreement shall be construed according to the laws of Illinois...",
  "labels": ["dispute_resolution"],
  "compliance_flags": [],
  "language": "en",
  "source": "cuad"
}
```

---

## STEP 4 — Convert LEDGAR Dataset

LEDGAR has 80,000 contract clauses with integer labels (0–99). This script converts
the integer labels to our 12 clause types.

```bash
.venv\Scripts\python scripts/convert_ledgar.py
```

### What it does
- Reads `data/raw/datasets/ledgar/{train,validation,test}.json`
- Reads `data/raw/datasets/ledgar/labels.json` to convert integer → label name
- Maps 100 LEDGAR label names → our 12 clause types (e.g. "Governing Laws" → "dispute_resolution")
- Filters out clauses shorter than 40 characters

### Expected output
```
Resolving LEDGAR label names ...
  100 labels loaded
LEDGAR train: 59,XXX records -> data/raw/datasets/ledgar_converted/train.json
  Label distribution:
    obligation: XXXXX
    ...
LEDGAR validation: 9,XXX records -> data/raw/datasets/ledgar_converted/validation.json
LEDGAR test: 9,XXX records -> data/raw/datasets/ledgar_converted/test.json
```

### Output files
```
data/raw/datasets/ledgar_converted/
├── train.json        (~59,000 records)
├── validation.json   (~9,000 records)
└── test.json         (~9,000 records)
```

---

## STEP 5 — Generate French Synthetic Data

No French legal clause dataset exists on HuggingFace. This script generates synthetic
French clauses using templates filled with realistic Tunisian legal vocabulary.

```bash
.venv\Scripts\python scripts/generate_synthetic.py
```

### What it does
- Generates ~450 French clause examples covering all 12 label types
- Uses slot-fill templates with Tunisian company names, courts, dates
- Adds compliance flags (lnpdp_relevant, missing_retention_period, etc.)
- Generates 131 NER-annotated sentences (for training the NER model)

### Expected output
```
Generating synthetic French clauses ...
  453 clause records written -> data/raw/datasets/synthetic_fr/synthetic_clauses.json
Generating synthetic NER annotations ...
  131 NER records written -> data/raw/datasets/synthetic_fr/synthetic_ner.json
Done.
```

### Output files
```
data/raw/datasets/synthetic_fr/
├── synthetic_clauses.json   (453 labeled French clauses)
└── synthetic_ner.json       (131 NER-annotated sentences)
```

### Why it matters
These French examples are upsampled 4× in the next step so the model learns
French legal vocabulary even though most training data is English.

---

## STEP 6 — Build the Final Dataset (Merge + Split)

This step merges all sources (CUAD + LEDGAR + French synthetic) into one clean
train/validation/test dataset.

```bash
.venv\Scripts\python scripts/build_dataset.py
```

### What it does
1. Loads all 3 sources
2. Validates each record (correct label, minimum 30 chars)
3. Upsamples French synthetic records 4× (so French competes with 60k English LEDGAR)
4. Deduplicates by first 300 characters of text
5. Caps each label at 5,000 records (prevents "obligation" from dominating)
6. Stratified split: **80% train / 10% val / 10% test** (by label)
7. Saves stats per label per split

### Expected output
```
Loading sources...
  cuad_converted:    4,XXX records
  ledgar_converted: 78,XXX records (train+val+test)
  synthetic_fr:        453 records (x4 = 1,812 after upsample)

After dedup + cap:
  train:  ~40,000 records
  val:    ~5,000 records
  test:   ~5,000 records

Saved: data/annotated/train/clauses.json
Saved: data/annotated/val/clauses.json
Saved: data/annotated/test/clauses.json
Saved: data/annotated/stats.json
```

### Output files
```
data/annotated/
├── train/clauses.json    (80% of data — used to train the model)
├── val/clauses.json      (10% — used during training to pick best checkpoint)
├── test/clauses.json     (10% — used ONLY at the end to measure final accuracy)
└── stats.json            (label distribution per split)
```

---

## STEP 7 — Train the Clause Classifier (The Main Model)

This fine-tunes `xlm-roberta-base` (a multilingual transformer) on your dataset.
The result is Agent 2's core brain: given a contract clause in French or English,
it classifies it into one or more of the 12 clause types.

```bash
.venv\Scripts\python scripts/train_classifier.py
```

### What it does
- Loads `data/annotated/train/clauses.json` and `val/clauses.json`
- Tokenizes text with XLM-RoBERTa tokenizer (max 512 tokens)
- Fine-tunes with BCEWithLogitsLoss (multi-label — each of 12 labels is independent)
- Evaluates micro-F1 after each epoch, saves the best checkpoint
- Saves the final model to `data/models/clause_classifier/`

### How long it takes
| Hardware | Time |
|----------|------|
| CPU only | 2–4 hours |
| GPU (NVIDIA, CUDA) | 20–40 minutes |

### Expected output (during training)
```
Loading dataset: 40,XXX train / 5,XXX val
Model: xlm-roberta-base
Labels: 12
Training on: CPU

Epoch 1/5 | loss: 0.4231 | micro-F1: 0.612
Epoch 2/5 | loss: 0.3104 | micro-F1: 0.698
Epoch 3/5 | loss: 0.2541 | micro-F1: 0.743
Epoch 4/5 | loss: 0.2103 | micro-F1: 0.768  ← best saved
Epoch 5/5 | loss: 0.1987 | micro-F1: 0.771  ← best saved

Best model saved to: data/models/clause_classifier/
```

### Output files
```
data/models/clause_classifier/
├── config.json             (model architecture config)
├── pytorch_model.bin       (trained weights)
├── tokenizer_config.json   (tokenizer settings)
├── vocab.json              (vocabulary)
└── label_map.json          (index → clause label name)
```

### Customize training (optional)
Set environment variables before running:
```bash
set MODEL_NAME=xlm-roberta-base    # or xlm-roberta-large (slower but better)
set EPOCHS=5                        # more epochs = better accuracy
set BATCH_SIZE=16                   # reduce to 8 if you get out-of-memory errors
set LR=2e-5                         # learning rate
set MAX_LEN=256                     # max token length (reduce for speed)

.venv\Scripts\python scripts/train_classifier.py
```

---

## STEP 8 — Train the NER Model (Optional but Recommended)

This fine-tunes spaCy's French NER model to recognize legal entities in contracts:
PARTY, ROLE, DATA_CATEGORY, DURATION, AMOUNT, LAW_REFERENCE, JURISDICTION, DATE.

```bash
.venv\Scripts\python scripts/train_ner.py
```

### What it does
- Loads `data/raw/datasets/synthetic_fr/synthetic_ner.json` (131 annotated sentences)
- Splits 85% train / 15% val
- Fine-tunes `fr_core_news_lg` — only the NER component is updated
- Saves best model by NER F1 score

### How long it takes
~10–15 minutes on CPU.

### Expected output
```
Training NER model...
  Train: 111 examples | Val: 20 examples
  Epoch 1 | NER F1: 0.54
  Epoch 2 | NER F1: 0.67
  ...
  Best model (F1=0.XX) saved to: data/models/ner_model/
```

### Output files
```
data/models/ner_model/       (full spaCy model directory)
```

> **If you skip this step:** Agent 2 will still work. It falls back to the generic
> `fr_core_news_lg` model for entity extraction. The NER quality will be lower
> (it won't recognize PARTY, LAW_REFERENCE, DATA_CATEGORY labels) but it won't crash.

---

## STEP 9 — Evaluate Agent 2

Measure the final accuracy of your trained classifier on the test set
(data the model has NEVER seen during training).

```bash
.venv\Scripts\python scripts/evaluate_agent2.py
```

### Expected output
```
Loading test set: 5,XXX records
Model mode: finetuned

Per-label results:
  termination        P=0.85  R=0.82  F1=0.83
  confidentiality    P=0.88  R=0.86  F1=0.87
  liability          P=0.79  R=0.75  F1=0.77
  dispute_resolution P=0.91  R=0.89  F1=0.90
  ...

Micro-average F1: 0.81
```

### What the scores mean
| Micro-F1 Score | What it means |
|---------------|--------------|
| 0.45 | Heuristic only (keyword matching) — before training |
| 0.60 | Zero-shot transformer (no fine-tuning) |
| 0.78 | Fine-tuned on CUAD + LEDGAR (English only) |
| **0.82** | **Fine-tuned + French synthetic (target after all steps)** |

---

## STEP 10 — Verify Agent 2 Works End-to-End

Start the backend and upload a real French contract PDF to confirm the full pipeline works.

```bash
# Terminal 1 — Start Redis (required for Celery)
docker run -p 6379:6379 redis:7

# Terminal 2 — Start Celery worker
cd backend
..\\.venv\Scripts\celery -A app.tasks.celery_app worker --loglevel=info

# Terminal 3 — Start FastAPI
cd backend
..\\.venv\Scripts\uvicorn app.main:app --reload

# Terminal 4 — Start frontend
cd frontend
npm run dev
```

Then open `http://localhost:5173` in your browser, upload any contract PDF, and verify:
1. Document goes through `queued → extracting → extracted → analyzing → analyzed`
2. Clause tab shows detected clauses with labels and confidence scores
3. Entities tab shows extracted legal entities (parties, dates, amounts)

---

## Complete Command Sequence (Copy-Paste Ready)

```bash
# Step 1 — Fix PyTorch
.venv\Scripts\pip uninstall torch torchvision torchaudio -y
.venv\Scripts\pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Step 2 — Fix spaCy
.venv\Scripts\pip install spacy
.venv\Scripts\python -m spacy download fr_core_news_lg

# Step 3 — Convert CUAD
.venv\Scripts\python scripts/convert_cuad.py

# Step 4 — Convert LEDGAR
.venv\Scripts\python scripts/convert_ledgar.py

# Step 5 — Generate French synthetic data
.venv\Scripts\python scripts/generate_synthetic.py

# Step 6 — Build final dataset
.venv\Scripts\python scripts/build_dataset.py

# Step 7 — Train clause classifier (~2-4h CPU)
.venv\Scripts\python scripts/train_classifier.py

# Step 8 — Train NER model (~15min CPU)
.venv\Scripts\python scripts/train_ner.py

# Step 9 — Evaluate
.venv\Scripts\python scripts/evaluate_agent2.py
```

---

## What Happens After All Steps

Once training is done, the models are saved to:
```
data/models/
├── clause_classifier/    ← loaded by ClauseClassifier automatically
└── ner_model/            ← loaded by EntityExtractor automatically
```

**No code changes needed.** The backend services auto-detect the fine-tuned models
on startup and switch from zero-shot/heuristic mode to fine-tuned mode.

You can verify which mode is active by checking the backend logs on startup:
```
[ClauseClassifier] Fine-tuned model loaded from data/models/clause_classifier/
[EntityExtractor]  Fine-tuned NER model loaded from data/models/ner_model/
```

---

## Troubleshooting

### "FileNotFoundError: CUAD_v1.json not found"
Run Step 0 again: `python scripts/download_datasets.py`

### "labels.json contains integers, not label names"
Delete `data/raw/datasets/ledgar/` and re-run `python scripts/download_datasets.py`

### "CUDA out of memory" during training
Reduce batch size: `set BATCH_SIZE=4` then retry Step 7

### "OSError: [WinError 1114]" (torch DLL error)
Go back to Step 1 and reinstall PyTorch CPU version

### Training takes too long on CPU
You can stop training at any time with Ctrl+C. The best checkpoint seen so far
is already saved. The model will work — just with slightly less accuracy.

### spaCy model not found: "fr_core_news_lg"
Re-run: `.venv\Scripts\python -m spacy download fr_core_news_lg`
