"""
Train a spaCy NER model on synthetic French legal entity annotations.

Base model: fr_core_news_lg  (fine-tune existing French NER)
Entities:   PARTY, ROLE, DATA_CATEGORY, DURATION, AMOUNT,
            LAW_REFERENCE, JURISDICTION, DATE

Input:  data/raw/datasets/synthetic_fr/synthetic_ner.json
Output: data/models/ner_model/

Usage:
    pip install spacy[fr]
    python -m spacy download fr_core_news_lg
    python scripts/train_ner.py
"""

from __future__ import annotations

import json
import random
from pathlib import Path

import spacy
from spacy.tokens import DocBin
from spacy.training import Example

DATA_DIR  = Path(__file__).parent.parent / "data"
NER_FILE  = DATA_DIR / "raw" / "datasets" / "synthetic_fr" / "synthetic_ner.json"
OUT_DIR   = DATA_DIR / "models" / "ner_model"

EPOCHS      = 30
BATCH_SIZE  = 8
DROPOUT     = 0.2
random.seed(42)


def load_ner_data(path: Path) -> list[tuple[str, dict]]:
    """
    Load NER annotations.
    Returns list of (text, {"entities": [(start, end, label), ...]})
    """
    records = json.loads(path.read_text(encoding="utf-8"))
    training_data = []
    for r in records:
        text     = r["text"]
        entities = []
        for ent in r.get("entities", []):
            start = ent["start"]
            end   = ent["end"]
            label = ent["label"]
            # Validate span
            if 0 <= start < end <= len(text):
                entities.append((start, end, label))
        if entities:
            training_data.append((text, {"entities": entities}))
    return training_data


def convert_to_docbin(nlp, data: list[tuple[str, dict]]) -> DocBin:
    """Convert training data to spaCy DocBin format."""
    db = DocBin()
    for text, annotations in data:
        doc = nlp.make_doc(text)
        ents = []
        for start_char, end_char, label in annotations["entities"]:
            span = doc.char_span(start_char, end_char, label=label, alignment_mode="contract")
            if span is not None:
                ents.append(span)
        try:
            doc.ents = ents
            db.add(doc)
        except Exception:
            # Skip conflicting spans
            pass
    return db


def main() -> None:
    if not NER_FILE.exists():
        raise FileNotFoundError(
            f"{NER_FILE} not found.\n"
            "Run: python scripts/generate_synthetic.py"
        )

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Loading base model: fr_core_news_lg …")
    nlp = spacy.load("fr_core_news_lg")

    # Add our custom NER labels to the existing NER component
    ner = nlp.get_pipe("ner") if nlp.has_pipe("ner") else nlp.add_pipe("ner", last=True)

    our_labels = ["PARTY", "ROLE", "DATA_CATEGORY", "DURATION", "AMOUNT",
                  "LAW_REFERENCE", "JURISDICTION"]
    for label in our_labels:
        ner.add_label(label)

    # Load training data
    training_data = load_ner_data(NER_FILE)
    random.shuffle(training_data)

    split_idx    = int(len(training_data) * 0.85)
    train_data   = training_data[:split_idx]
    val_data     = training_data[split_idx:]

    print(f"Training samples: {len(train_data)} | Val: {len(val_data)}")

    # Convert to DocBin for efficient loading
    train_db = convert_to_docbin(nlp, train_data)
    val_db   = convert_to_docbin(nlp, val_data)
    train_db.to_disk(OUT_DIR / "train.spacy")
    val_db.to_disk(OUT_DIR / "val.spacy")

    # Fine-tune: disable other pipes, only train NER
    other_pipes = [pipe for pipe in nlp.pipe_names if pipe != "ner"]
    with nlp.disable_pipes(*other_pipes):
        optimizer = nlp.resume_training()

        print(f"\nFine-tuning NER for {EPOCHS} epochs …")
        best_score = 0.0
        for epoch in range(EPOCHS):
            random.shuffle(train_data)
            losses: dict = {}
            examples = []
            for text, annotations in train_data:
                doc  = nlp.make_doc(text)
                example = Example.from_dict(doc, annotations)
                examples.append(example)

            # Mini-batch training
            for batch in spacy.util.minibatch(examples, size=BATCH_SIZE):
                nlp.update(batch, drop=DROPOUT, losses=losses, sgd=optimizer)

            # Validation
            val_examples = []
            for text, annotations in val_data:
                doc = nlp.make_doc(text)
                val_examples.append(Example.from_dict(doc, annotations))

            scores = nlp.evaluate(val_examples)
            ner_f1 = scores.get("ents_f", 0.0)

            print(f"  Epoch {epoch + 1:02d}/{EPOCHS} | loss={losses.get('ner', 0):.4f} | NER F1={ner_f1:.4f}")

            if ner_f1 > best_score:
                best_score = ner_f1
                nlp.to_disk(OUT_DIR)
                print(f"    → Best model saved (F1={best_score:.4f})")

    print(f"\nBest NER F1: {best_score:.4f}")
    print(f"Model saved → {OUT_DIR}")


if __name__ == "__main__":
    main()
