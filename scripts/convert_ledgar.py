"""
Convert LEDGAR (from lex_glue) -> our unified clause classification format.

lex_glue/ledgar record structure:
  { "text": "...", "label": 97 }   <-- label is an INTEGER index

The 100 label names are stored in the dataset's ClassLabel feature.
We resolve them by loading the dataset info, or fall back to the labels.json
saved by download_datasets.py.

100 fine-grained labels -> our 12 ClauseLabel values.

Run after: python scripts/download_datasets.py
Usage:     python scripts/convert_ledgar.py
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
IN_DIR   = DATA_DIR / "raw" / "datasets" / "ledgar"
OUT_DIR  = DATA_DIR / "raw" / "datasets" / "ledgar_converted"

MIN_CLAUSE_CHARS = 40

# ── Label mapping: LEDGAR label → our ClauseLabel ────────────────────────────
# Covers all 100 LEDGAR labels. Unmapped ones default to "obligation".
LEDGAR_LABEL_MAP: dict[str, str] = {
    # Termination
    "Termination": "termination",
    "Term": "termination",
    "Expiration": "termination",
    "Extension": "termination",
    "Renewal": "termination",
    "Survival": "termination",

    # Definition
    "Definitions": "definition",

    # Confidentiality
    "Confidentiality": "confidentiality",
    "Non-Disclosure": "confidentiality",
    "Confidentiality And Non-Disclosure": "confidentiality",

    # Liability
    "Indemnification": "liability",
    "Indemnification And Insurance": "liability",
    "Limitation Of Liability": "liability",
    "Indemnity": "liability",
    "Limitation On Liability": "liability",
    "Indemnification; Contribution": "liability",

    # IP Rights
    "Intellectual Property": "ip_rights",
    "Ownership": "ip_rights",
    "License": "ip_rights",
    "Licenses": "ip_rights",
    "License Grant": "ip_rights",
    "Intellectual Property Rights": "ip_rights",
    "Intellectual Property Ownership": "ip_rights",

    # Dispute Resolution
    "Dispute Resolution": "dispute_resolution",
    "Arbitration": "dispute_resolution",
    "Governing Law": "dispute_resolution",
    "Jurisdiction": "dispute_resolution",
    "Choice Of Law": "dispute_resolution",
    "Governing Law And Jurisdiction": "dispute_resolution",
    "Governing Law; Jurisdiction": "dispute_resolution",
    "Governing Law And Dispute Resolution": "dispute_resolution",

    # Force Majeure
    "Force Majeure": "force_majeure",

    # Payment
    "Payment Terms": "payment",
    "Payments": "payment",
    "Payment": "payment",
    "Compensation": "payment",
    "Fees": "payment",
    "Consideration": "payment",
    "Fees And Expenses": "payment",
    "Fees And Payment": "payment",
    "Payment And Fees": "payment",
    "Pricing": "payment",
    "Royalties": "payment",

    # Warranty
    "Warranties": "warranty",
    "Representations": "warranty",
    "Representations And Warranties": "warranty",
    "Warranty": "warranty",
    "Warranties And Representations": "warranty",
    "Disclaimer Of Warranties": "warranty",
    "Representations, Warranties And Covenants": "warranty",

    # Data Processing
    "Privacy": "data_processing",
    "Data Protection": "data_processing",
    "Data Security": "data_processing",
    "Data Privacy": "data_processing",

    # Penalty
    "Penalties": "penalty",
    "Damages": "penalty",
    "Liquidated Damages": "penalty",
    "Remedies": "penalty",
}

DEFAULT_LABEL = "obligation"


def _map_label(ledgar_label: str) -> str:
    return LEDGAR_LABEL_MAP.get(ledgar_label, DEFAULT_LABEL)


def _load_index_to_name() -> dict[int, str]:
    """
    lex_glue stores labels as integer indices.
    download_datasets.py saves the ClassLabel names to labels.json as a list of strings.
    We build an index -> name dict from that list.
    """
    labels_file = IN_DIR / "labels.json"
    if not labels_file.exists():
        raise FileNotFoundError(
            f"{labels_file} not found.\n"
            "Run: python scripts/download_datasets.py"
        )

    names = json.loads(labels_file.read_text(encoding="utf-8"))

    # After the fix, names is a list of strings like ["Agreements", "Amendments", ...]
    # Before the fix it was a list of ints [0, 1, 2, ...] — handle both
    if names and isinstance(names[0], int):
        raise ValueError(
            "labels.json contains integers, not label names.\n"
            "Delete data/raw/datasets/ledgar/ and re-run: python scripts/download_datasets.py"
        )

    return {i: name for i, name in enumerate(names)}


def convert_split(split: str, index_to_name: dict[int, str]) -> list[dict]:
    in_file = IN_DIR / f"{split}.json"
    if not in_file.exists():
        print(f"  {split}.json not found, skipping")
        return []

    raw = json.loads(in_file.read_text(encoding="utf-8"))
    results = []

    for record in raw:
        text = record.get("text", "").strip()
        if len(text) < MIN_CLAUSE_CHARS:
            continue

        raw_label = record.get("label", "")
        # lex_glue uses integer index; original LEDGAR used string name
        if isinstance(raw_label, int):
            label_name = index_to_name.get(raw_label, str(raw_label))
        else:
            label_name = str(raw_label)

        our_label = _map_label(label_name)
        results.append({
            "text": text,
            "labels": [our_label],
            "compliance_flags": [],
            "language": "en",
            "source": "ledgar",
        })

    return results


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Resolving LEDGAR label names ...")
    index_to_name = _load_index_to_name()
    if index_to_name:
        print(f"  {len(index_to_name)} labels loaded")

    for split in ["train", "test", "validation"]:
        records = convert_split(split, index_to_name)
        if not records:
            continue

        out_file = OUT_DIR / f"{split}.json"
        out_file.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")

        label_counts: Counter = Counter(r["labels"][0] for r in records)
        print(f"LEDGAR {split}: {len(records)} records → {out_file}")
        print("  Label distribution:")
        for label, count in label_counts.most_common():
            print(f"    {label}: {count}")


if __name__ == "__main__":
    main()
