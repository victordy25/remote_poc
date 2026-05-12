#!/usr/bin/env python3
"""GitHub Pages용: sample.json → 파이프라인 → docs/*.json 생성."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from pipeline import run_pipeline  # noqa: E402


def main() -> None:
    docs = ROOT / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    sample = ROOT / "sample.json"
    master = ROOT / "poc" / "patient_master.example.json"
    bundle = json.loads(sample.read_text(encoding="utf-8"))
    out = run_pipeline(bundle, master, extract_mode="mock", use_dummy_if_missing=False)
    (docs / "report.json").write_text(
        json.dumps(out["report"], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (docs / "facts.json").write_text(
        json.dumps(out["facts"], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (docs / "meta.json").write_text(
        json.dumps(out["meta"], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (docs / "input_sample.json").write_text(
        json.dumps(bundle, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print("OK:", docs)


if __name__ == "__main__":
    main()
