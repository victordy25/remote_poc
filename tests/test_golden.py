"""골든 세트 회귀 테스트. 실행: remote_poc 디렉터리에서 python -m pytest tests/ -v"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from pipeline import run_pipeline  # noqa: E402
from pipeline.validate import validate_report  # noqa: E402


def test_dialogue_sample_schema():
    bundle = json.loads((ROOT / "dialogue_sample.json").read_text(encoding="utf-8"))
    out = run_pipeline(
        bundle,
        ROOT / "poc" / "patient_master.example.json",
        extract_mode="mock",
    )
    validate_report(out["report"])


def test_dummy_master():
    bundle = {"dialogue": [{"speaker": "환자", "text": "안녕하세요"}]}
    out = run_pipeline(bundle, None, extract_mode="mock", use_dummy_if_missing=True)
    validate_report(out["report"])
    assert out["report"]["A_대상자_정보"]["성명"] == "POC_미식별"


def test_eval_manifest_exit_code():
    import subprocess

    r = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "eval.py")],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stdout + r.stderr
