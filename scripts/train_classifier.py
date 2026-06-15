"""
Fine-tune xlm-roberta-base for multi-label clause classification.

Model: xlm-roberta-base  (multilingual — trained on English + French data)
Task:  Multi-label classification over 12 ClauseLabel values
Loss:  BCEWithLogitsLoss (each label is independent binary decision)

Input:  data/annotated/train/clauses.json
        data/annotated/val/clauses.json
Output: data/models/clause_classifier/

Usage:
    pip install transformers datasets scikit-learn torch accelerate
    python scripts/train_classifier.py

Hardware: CPU works but is slow (~2–4h for 20k records).
          GPU recommended: set DEVICE=cuda or use accelerate.

Training config (tunable via env vars):
    MAX_LEN=256       token limit per clause
    BATCH_SIZE=16
    EPOCHS=4
    LR=2e-5
    MODEL_NAME=xlm-roberta-base   (or camembert-base for French-only)
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import torch
from torch.utils.data import Dataset
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    Trainer,
    TrainingArguments,
    EvalPrediction,
)
from sklearn.metrics import f1_score, classification_report
import numpy as np

# ── Config ────────────────────────────────────────────────────────────────────
DATA_DIR   = Path(__file__).parent.parent / "data"
TRAIN_FILE = DATA_DIR / "annotated" / "train" / "clauses.json"
VAL_FILE   = DATA_DIR / "annotated" / "val"   / "clauses.json"
OUT_DIR    = DATA_DIR / "models" / "clause_classifier"

MODEL_NAME = os.getenv("MODEL_NAME", "xlm-roberta-base")
MAX_LEN    = int(os.getenv("MAX_LEN",    "256"))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "16"))
EPOCHS     = int(os.getenv("EPOCHS",     "4"))
LR         = float(os.getenv("LR",       "2e-5"))

LABELS = [
    "definition", "obligation", "liability", "termination",
    "data_processing", "confidentiality", "dispute_resolution",
    "force_majeure", "penalty", "ip_rights", "payment", "warranty",
]
LABEL2ID = {lbl: i for i, lbl in enumerate(LABELS)}
ID2LABEL = {i: lbl for i, lbl in enumerate(LABELS)}
NUM_LABELS = len(LABELS)


# ── Dataset ───────────────────────────────────────────────────────────────────

class ClauseDataset(Dataset):
    def __init__(self, records: list[dict], tokenizer, max_len: int):
        self.records   = records
        self.tokenizer = tokenizer
        self.max_len   = max_len

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, idx: int) -> dict:
        record = self.records[idx]
        text   = record["text"]

        encoding = self.tokenizer(
            text,
            max_length=self.max_len,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )

        # Multi-hot label vector
        label_vec = torch.zeros(NUM_LABELS, dtype=torch.float)
        for lbl in record.get("labels", []):
            if lbl in LABEL2ID:
                label_vec[LABEL2ID[lbl]] = 1.0

        return {
            "input_ids":      encoding["input_ids"].squeeze(),
            "attention_mask": encoding["attention_mask"].squeeze(),
            "labels":         label_vec,
        }


# ── Metrics ───────────────────────────────────────────────────────────────────

def compute_metrics(pred: EvalPrediction) -> dict:
    logits = pred.predictions
    labels = pred.label_ids

    # Sigmoid threshold at 0.5 for multi-label
    probs = torch.sigmoid(torch.tensor(logits)).numpy()
    preds = (probs >= 0.5).astype(int)

    # Micro-F1 across all labels
    micro_f1 = f1_score(labels, preds, average="micro", zero_division=0)
    # Per-label macro-F1
    macro_f1 = f1_score(labels, preds, average="macro", zero_division=0)

    return {
        "micro_f1": round(micro_f1, 4),
        "macro_f1": round(macro_f1, 4),
    }


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    if not TRAIN_FILE.exists():
        raise FileNotFoundError(
            f"{TRAIN_FILE} not found.\n"
            "Run the following first:\n"
            "  python scripts/download_datasets.py\n"
            "  python scripts/convert_cuad.py\n"
            "  python scripts/convert_ledgar.py\n"
            "  python scripts/generate_synthetic.py\n"
            "  python scripts/build_dataset.py"
        )

    print(f"Model:      {MODEL_NAME}")
    print(f"Max length: {MAX_LEN}")
    print(f"Batch size: {BATCH_SIZE}")
    print(f"Epochs:     {EPOCHS}")
    print(f"LR:         {LR}")

    # Load data
    train_records = json.loads(TRAIN_FILE.read_text(encoding="utf-8"))
    val_records   = json.loads(VAL_FILE.read_text(encoding="utf-8"))
    print(f"\nTrain: {len(train_records)} | Val: {len(val_records)}")

    # Tokenizer + model
    print(f"\nLoading {MODEL_NAME} …")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_NAME,
        num_labels=NUM_LABELS,
        id2label=ID2LABEL,
        label2id=LABEL2ID,
        problem_type="multi_label_classification",
    )

    train_dataset = ClauseDataset(train_records, tokenizer, MAX_LEN)
    val_dataset   = ClauseDataset(val_records,   tokenizer, MAX_LEN)

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    training_args = TrainingArguments(
        output_dir=str(OUT_DIR),
        num_train_epochs=EPOCHS,
        per_device_train_batch_size=BATCH_SIZE,
        per_device_eval_batch_size=BATCH_SIZE * 2,
        learning_rate=LR,
        weight_decay=0.01,
        warmup_ratio=0.1,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="micro_f1",
        greater_is_better=True,
        logging_dir=str(OUT_DIR / "logs"),
        logging_steps=100,
        save_total_limit=2,
        fp16=torch.cuda.is_available(),
        report_to="none",
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        compute_metrics=compute_metrics,
    )

    print("\nTraining …")
    trainer.train()

    # Save final model + tokenizer
    model.save_pretrained(str(OUT_DIR))
    tokenizer.save_pretrained(str(OUT_DIR))

    # Save label mapping so inference code can load it
    label_map = {"labels": LABELS, "label2id": LABEL2ID, "id2label": {str(k): v for k, v in ID2LABEL.items()}}
    (OUT_DIR / "label_map.json").write_text(json.dumps(label_map, indent=2), encoding="utf-8")

    print(f"\nModel saved -> {OUT_DIR}")

    # Final eval on val
    results = trainer.evaluate()
    print(f"Val micro-F1: {results.get('eval_micro_f1', 'N/A')}")
    print(f"Val macro-F1: {results.get('eval_macro_f1', 'N/A')}")


if __name__ == "__main__":
    main()
