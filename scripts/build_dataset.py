"""
Build final train/val/test splits from all sources.

Sources (in priority order):
  1. data/raw/datasets/synthetic_fr/synthetic_clauses.json   (French, highest priority)
  2. data/raw/datasets/cuad_converted/cuad_clauses.json      (English)
  3. data/raw/datasets/ledgar_converted/train.json           (English)
  4. data/raw/datasets/ledgar_converted/validation.json
  5. data/raw/datasets/ledgar_converted/test.json

Strategy:
  - Cap each label at MAX_PER_LABEL to prevent class imbalance domination
  - French examples are upsampled (duplicated) to balance against English volume
  - 80% train / 10% val / 10% test split

Output:
  data/annotated/train/clauses.json
  data/annotated/val/clauses.json
  data/annotated/test/clauses.json
  data/annotated/stats.json

Usage: python scripts/build_dataset.py
"""

from __future__ import annotations

import json
import random
from collections import Counter, defaultdict
from pathlib import Path

DATA_DIR  = Path(__file__).parent.parent / "data"
OUT_DIR   = DATA_DIR / "annotated"

VALID_LABELS = {
    "definition", "obligation", "liability", "termination",
    "data_processing", "confidentiality", "dispute_resolution",
    "force_majeure", "penalty", "ip_rights", "payment", "warranty",
}

MAX_PER_LABEL   = 5000   # cap per label to avoid domination by LEDGAR "obligation"
FRENCH_UPSAMPLE = 4      # multiply French examples by this factor
TRAIN_RATIO     = 0.80
VAL_RATIO       = 0.10
# test = 1 - train - val = 0.10

random.seed(42)


def load_json(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_record(record: dict) -> dict | None:
    """Ensure record has required fields and valid labels. Returns None to skip."""
    text = record.get("text", "").strip()
    if len(text) < 30:
        return None

    labels = [lbl for lbl in record.get("labels", []) if lbl in VALID_LABELS]
    if not labels:
        return None

    return {
        "text": text,
        "labels": labels,
        "compliance_flags": record.get("compliance_flags", []),
        "language": record.get("language", "en"),
        "source": record.get("source", "unknown"),
    }


def load_all_sources() -> list[dict]:
    raw_dirs = DATA_DIR / "raw" / "datasets"
    sources = [
        raw_dirs / "synthetic_fr"     / "synthetic_clauses.json",
        raw_dirs / "cuad_converted"   / "cuad_clauses.json",
        raw_dirs / "ledgar_converted" / "train.json",
        raw_dirs / "ledgar_converted" / "validation.json",
        raw_dirs / "ledgar_converted" / "test.json",
    ]

    all_records: list[dict] = []
    for path in sources:
        raw = load_json(path)
        normalized = [normalize_record(r) for r in raw]
        valid = [r for r in normalized if r is not None]
        print(f"  {path.name}: {len(raw)} raw -> {len(valid)} valid")
        all_records.extend(valid)

    return all_records


def upsample_french(records: list[dict]) -> list[dict]:
    """Duplicate French examples to increase their representation."""
    french = [r for r in records if r["language"] == "fr"]
    non_french = [r for r in records if r["language"] != "fr"]
    # Upsample: add FRENCH_UPSAMPLE-1 additional copies
    upsampled = non_french + french * FRENCH_UPSAMPLE
    print(f"  French: {len(french)} × {FRENCH_UPSAMPLE} = {len(french) * FRENCH_UPSAMPLE} | English: {len(non_french)}")
    return upsampled


def deduplicate(records: list[dict]) -> list[dict]:
    """Remove exact text duplicates, keeping first occurrence."""
    seen: set[str] = set()
    result = []
    for r in records:
        key = r["text"][:300].lower().strip()
        if key not in seen:
            seen.add(key)
            result.append(r)
    before = len(records)
    print(f"  Dedup: {before} -> {len(result)} records")
    return result


def cap_by_label(records: list[dict]) -> list[dict]:
    """
    Cap each label at MAX_PER_LABEL.
    For multi-label records, the record counts toward all its labels.
    Simple greedy approach: sort French-first so French is kept over English.
    """
    records_sorted = sorted(records, key=lambda r: (0 if r["language"] == "fr" else 1))
    label_counts: Counter = Counter()
    result = []
    for r in records_sorted:
        labels = r["labels"]
        # Check if any label is still under cap
        if any(label_counts[lbl] < MAX_PER_LABEL for lbl in labels):
            result.append(r)
            for lbl in labels:
                label_counts[lbl] += 1
    print(f"  Cap {MAX_PER_LABEL}/label: {len(records)} -> {len(result)} records")
    return result


def split_dataset(records: list[dict]) -> tuple[list[dict], list[dict], list[dict]]:
    """Stratified split by primary label."""
    by_label: dict[str, list[dict]] = defaultdict(list)
    for r in records:
        primary = r["labels"][0]
        by_label[primary].append(r)

    train, val, test = [], [], []
    for label, items in by_label.items():
        random.shuffle(items)
        n = len(items)
        n_train = int(n * TRAIN_RATIO)
        n_val   = int(n * VAL_RATIO)
        train.extend(items[:n_train])
        val.extend(items[n_train:n_train + n_val])
        test.extend(items[n_train + n_val:])

    random.shuffle(train)
    random.shuffle(val)
    random.shuffle(test)
    return train, val, test


def save_split(records: list[dict], path: Path, name: str) -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    counts = Counter(r["labels"][0] for r in records)
    print(f"\n{name}: {len(records)} records -> {path}")
    for label in sorted(VALID_LABELS):
        print(f"  {label}: {counts.get(label, 0)}")
    return dict(counts)


def main() -> None:
    print("Loading sources …")
    records = load_all_sources()

    print("\nUpsampling French …")
    records = upsample_french(records)

    print("\nDeduplicating …")
    records = deduplicate(records)

    print("\nCapping labels …")
    records = cap_by_label(records)

    print("\nSplitting …")
    train, val, test = split_dataset(records)

    train_counts = save_split(train, OUT_DIR / "train" / "clauses.json", "TRAIN")
    val_counts   = save_split(val,   OUT_DIR / "val"   / "clauses.json", "VAL")
    test_counts  = save_split(test,  OUT_DIR / "test"  / "clauses.json", "TEST")

    stats = {
        "total": len(records),
        "train": len(train),
        "val":   len(val),
        "test":  len(test),
        "train_label_counts": train_counts,
        "val_label_counts":   val_counts,
        "test_label_counts":  test_counts,
    }
    stats_file = OUT_DIR / "stats.json"
    stats_file.write_text(json.dumps(stats, indent=2), encoding="utf-8")
    print(f"\nStats saved -> {stats_file}")
    print(f"\nFinal: {len(train)} train / {len(val)} val / {len(test)} test")


if __name__ == "__main__":
    main()
