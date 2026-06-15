"""
Convert CUAD (SQuAD-format QA) → our unified clause classification format.

CUAD structure:
  Each record = one paragraph from a contract + answers for 41 clause-type questions.
  question = clause type name (e.g. "Termination For Convenience")
  answers  = {"text": [...], "answer_start": [...]}  (empty = clause not present)

Our output format per record:
  {
    "text": "<paragraph text>",
    "labels": ["termination", "liability"],   // mapped ClauseLabel values
    "compliance_flags": [],
    "language": "en",
    "source": "cuad"
  }

Run after: python scripts/download_datasets.py
Usage:     python scripts/convert_cuad.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
IN_DIR   = DATA_DIR / "raw" / "datasets" / "cuad"
OUT_DIR  = DATA_DIR / "raw" / "datasets" / "cuad_converted"

# ── Label mapping: CUAD question keyword → our ClauseLabel ──────────────────
# Only CUAD categories with a meaningful mapping are listed.
# "None" = skip this category (metadata, not a clause type we model).
CUAD_LABEL_MAP: dict[str, str | None] = {
    "document name":                    None,
    "parties":                          None,
    "agreement date":                   None,
    "effective date":                   None,
    "expiration date":                  "termination",
    "renewal term":                     "termination",
    "notice period to terminate":       "termination",
    "termination for convenience":      "termination",
    "governing law":                    "dispute_resolution",
    "dispute resolution":               "dispute_resolution",
    "arbitration":                      "dispute_resolution",
    "jurisdiction":                     "dispute_resolution",
    "most favored nation":              "obligation",
    "non-compete":                      "obligation",
    "exclusivity":                      "obligation",
    "no-solicit of customers":          "obligation",
    "no-solicit of employees":          "obligation",
    "non-disparagement":                "obligation",
    "rofr":                             "obligation",
    "change of control":                "obligation",
    "anti-assignment":                  "obligation",
    "minimum commitment":               "obligation",
    "volume restriction":               "obligation",
    "post-termination services":        "obligation",
    "audit rights":                     "obligation",
    "covenant not to sue":              "obligation",
    "third party beneficiary":          "obligation",
    "revenue/profit sharing":           "payment",
    "price restrictions":               "payment",
    "payment":                          "payment",
    "ip ownership assignment":          "ip_rights",
    "joint ip ownership":               "ip_rights",
    "license grant":                    "ip_rights",
    "non-transferable license":         "ip_rights",
    "affiliate license":                "ip_rights",
    "irrevocable or perpetual license": "ip_rights",
    "source code escrow":               "ip_rights",
    "uncapped liability":               "liability",
    "cap on liability":                 "liability",
    "limitation of liability":          "liability",
    "indemnification":                  "liability",
    "liquidated damages":               "penalty",
    "warranty":                         "warranty",
    "insurance":                        "obligation",
    "confidentiality":                  "confidentiality",
    "data":                             "data_processing",
    "privacy":                          "data_processing",
    "force majeure":                    "force_majeure",
    "definition":                       "definition",
}

MIN_CLAUSE_CHARS = 40  # skip very short paragraphs


def _map_question(question: str) -> str | None:
    """Map a CUAD question string to our ClauseLabel value (or None to skip)."""
    q = question.lower()
    for keyword, label in CUAD_LABEL_MAP.items():
        if keyword in q:
            return label
    return "obligation"  # default: treat as generic obligation


def convert_file() -> list[dict]:
    """
    Convert CUAD_v1.json.

    CUAD SQuAD format:
      {
        "data": [
          {
            "title": "ContractName",
            "paragraphs": [
              {
                "context": "paragraph text",
                "qas": [
                  {
                    "question": "Highlight the parts...",
                    "id": "...",
                    "answers": {"text": [...], "answer_start": [...]},
                    "is_impossible": false
                  }
                ]
              }
            ]
          }
        ]
      }
    """
    in_file = IN_DIR / "CUAD_v1.json"
    if not in_file.exists():
        print(f"  CUAD_v1.json not found in {IN_DIR}")
        print("  Run: python scripts/download_datasets.py")
        return []

    print(f"  Reading {in_file} ...")
    raw = json.loads(in_file.read_text(encoding="utf-8"))
    contracts = raw.get("data", [])
    print(f"  {len(contracts)} contracts found")

    records_by_context: dict[str, dict] = {}

    for contract in contracts:
        for paragraph in contract.get("paragraphs", []):
            context: str = paragraph.get("context", "").strip()
            if len(context) < MIN_CLAUSE_CHARS:
                continue

            for qa in paragraph.get("qas", []):
                question: str = qa.get("question", "")
                answers = qa.get("answers", [])

                # answers is a list of {"text": ..., "answer_start": ...} dicts
                # (older SQuAD format used a dict with a "text" key — handle both)
                if isinstance(answers, list):
                    answer_texts = [a["text"] for a in answers if a.get("text")]
                else:
                    answer_texts = answers.get("text", [])
                if not answer_texts:
                    continue

                label = _map_question(question)
                if label is None:
                    continue

                # Accumulate all labels per paragraph
                if context not in records_by_context:
                    records_by_context[context] = {
                        "text": context,
                        "labels": [],
                        "compliance_flags": [],
                        "language": "en",
                        "source": "cuad",
                    }
                if label not in records_by_context[context]["labels"]:
                    records_by_context[context]["labels"].append(label)

    return [r for r in records_by_context.values() if r["labels"]]


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    all_records = convert_file()

    # Deduplicate by text
    seen: set[str] = set()
    deduped = []
    for r in all_records:
        key = r["text"][:200]
        if key not in seen:
            seen.add(key)
            deduped.append(r)

    # Label distribution
    from collections import Counter
    label_counts: Counter = Counter()
    for r in deduped:
        for lbl in r["labels"]:
            label_counts[lbl] += 1

    out_file = OUT_DIR / "cuad_clauses.json"
    out_file.write_text(json.dumps(deduped, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\nCUAD converted: {len(deduped)} unique clause paragraphs -> {out_file}")
    print("Label distribution:")
    for label, count in label_counts.most_common():
        print(f"  {label}: {count}")


if __name__ == "__main__":
    main()
