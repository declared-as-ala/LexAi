"""
Download CUAD and LEDGAR into data/raw/datasets/.

CUAD:   downloads only CUAD_v1.json via hf_hub_download (avoids the 511 PDFs)
LEDGAR: loads via lex_glue benchmark -> config "ledgar"

Usage:
    python scripts/download_datasets.py

Requirements:
    pip install datasets huggingface_hub
"""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data" / "raw" / "datasets"

os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")


def download_cuad() -> None:
    """
    Download only CUAD_v1.json (the SQuAD-format QA file).

    Why not load_dataset("theatticusproject/cuad"):
      That dataset is folder-based and tries to download 511 PDF contracts.
      On Windows it crashes with a FileNotFoundError on long file paths.

    Fix: use hf_hub_download to fetch only the JSON file (~170 MB).
    """
    from huggingface_hub import hf_hub_download  # type: ignore

    out_dir = DATA_DIR / "cuad"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "CUAD_v1.json"

    if out_file.exists():
        print(f"CUAD already present: {out_file}")
        return

    print("Downloading CUAD_v1.json (~170 MB) ...")
    downloaded = hf_hub_download(
        repo_id="theatticusproject/cuad",
        filename="CUAD_v1/CUAD_v1.json",
        repo_type="dataset",
        local_dir=str(out_dir),
        local_dir_use_symlinks=False,
    )

    # hf_hub_download may place the file in a nested subfolder — move to flat location
    downloaded_path = Path(downloaded)
    if downloaded_path.resolve() != out_file.resolve():
        shutil.copy2(downloaded_path, out_file)

    size_mb = out_file.stat().st_size / 1_000_000
    print(f"  Saved: {out_file} ({size_mb:.1f} MB)")


def download_ledgar() -> None:
    """
    Download LEDGAR via the lex_glue benchmark.

    Correct call: load_dataset("coastalcph/lex_glue", "ledgar")
    This gives 60 000 train / 10 000 val / 10 000 test contract provisions
    with 100 clause-type labels stored as integer indices.
    """
    from datasets import load_dataset  # type: ignore

    out_dir = DATA_DIR / "ledgar"
    out_dir.mkdir(parents=True, exist_ok=True)

    if (out_dir / "train.json").exists():
        print(f"LEDGAR already present: {out_dir}")
        return

    print("Downloading LEDGAR via lex_glue ...")
    ds = load_dataset("coastalcph/lex_glue", "ledgar")

    # Save label names (index -> string) from the ClassLabel feature
    label_names: list[str] = ds["train"].features["label"].names
    (out_dir / "labels.json").write_text(
        json.dumps(label_names, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"  {len(label_names)} label names saved")

    for split in ds:
        records = [dict(r) for r in ds[split]]
        out_file = out_dir / f"{split}.json"
        out_file.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  LEDGAR {split}: {len(records)} records -> {out_file}")


if __name__ == "__main__":
    download_cuad()
    download_ledgar()
    print("\nDone. Run convert_cuad.py and convert_ledgar.py next.")
