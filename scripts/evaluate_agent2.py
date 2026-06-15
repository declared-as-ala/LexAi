"""
Evaluate Agent 2 (ClauseClassifier + EntityExtractor) on the test set.

Prints per-class precision, recall, F1 and micro/macro averages.

Usage:
    python scripts/evaluate_agent2.py

Requires:
    data/annotated/test/clauses.json  (produced by build_dataset.py)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from app.services.nlp.clause_classifier import ClauseClassifier
from app.services.nlp.clause_segmenter import ClauseSegment

DATA_DIR  = ROOT / "data"
TEST_FILE = DATA_DIR / "annotated" / "test" / "clauses.json"

LABELS = [
    "definition", "obligation", "liability", "termination",
    "data_processing", "confidentiality", "dispute_resolution",
    "force_majeure", "penalty", "ip_rights", "payment", "warranty",
]


def evaluate_classifier(records: list[dict]) -> None:
    print(f"Evaluating ClauseClassifier on {len(records)} test records …\n")
    classifier = ClauseClassifier(language="fr")

    y_true: list[set[str]] = []
    y_pred: list[set[str]] = []

    for i, record in enumerate(records):
        # Wrap text in a ClauseSegment (the classifier only uses .text)
        seg = ClauseSegment(
            clause_id=f"c-{i:04d}",
            text=record["text"],
            start_char=0,
            end_char=len(record["text"]),
        )
        result = classifier.classify(seg)
        y_true.append(set(record.get("labels", [])))
        y_pred.append(set(result.labels))

    # Per-label metrics
    print(f"{'Label':<25} {'P':>6} {'R':>6} {'F1':>6} {'Support':>8}")
    print("-" * 58)

    micro_tp = micro_fp = micro_fn = 0
    for label in LABELS:
        tp = sum(1 for t, p in zip(y_true, y_pred) if label in t and label in p)
        fp = sum(1 for t, p in zip(y_true, y_pred) if label not in t and label in p)
        fn = sum(1 for t, p in zip(y_true, y_pred) if label in t and label not in p)
        support = tp + fn
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall    = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1        = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        micro_tp += tp
        micro_fp += fp
        micro_fn += fn
        print(f"{label:<25} {precision:>6.3f} {recall:>6.3f} {f1:>6.3f} {support:>8}")

    print("-" * 58)
    micro_p = micro_tp / (micro_tp + micro_fp) if (micro_tp + micro_fp) > 0 else 0.0
    micro_r = micro_tp / (micro_tp + micro_fn) if (micro_tp + micro_fn) > 0 else 0.0
    micro_f1 = 2 * micro_p * micro_r / (micro_p + micro_r) if (micro_p + micro_r) > 0 else 0.0
    print(f"{'micro avg':<25} {micro_p:>6.3f} {micro_r:>6.3f} {micro_f1:>6.3f} {len(records):>8}")

    model_name = classifier._model_used
    print(f"\nModel used: {model_name}")


def main() -> None:
    if not TEST_FILE.exists():
        print(f"Test file not found: {TEST_FILE}")
        print("Run: python scripts/build_dataset.py")
        sys.exit(1)

    records = json.loads(TEST_FILE.read_text(encoding="utf-8"))
    evaluate_classifier(records)


if __name__ == "__main__":
    main()
