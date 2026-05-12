#!/usr/bin/env python3
"""골든 세트: 스키마 검증 + 기대 리포트 일치 + (선택) 근거 턴 검사."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from pipeline import run_pipeline  # noqa: E402
from pipeline.validate import validate_report  # noqa: E402

LIST_SORT_KEYS = frozenset({"환자_상태", "서비스_제공내용", "관리방법", "증상"})


def normalize_report(d: dict) -> dict:
    """지정 키의 리스트는 순서 무관 비교를 위해 정렬."""

    def walk(x: object) -> object:
        if isinstance(x, dict):
            out = {}
            for k, v in x.items():
                if k in LIST_SORT_KEYS and isinstance(v, list):
                    out[k] = sorted(str(i) for i in v)
                else:
                    out[k] = walk(v)
            return out
        if isinstance(x, list):
            return [walk(i) for i in x]
        return x

    return walk(d)  # type: ignore[return-value]


def check_evidence(facts_doc: dict, spec_path: Path) -> list[str]:
    data = json.loads(spec_path.read_text(encoding="utf-8"))
    errs: list[str] = []
    facts = facts_doc.get("facts") or []
    for chk in data.get("checks", []):
        sub = chk.get("path_contains", "")
        must_turn = chk.get("evidence_must_include_turn")
        matched = [f for f in facts if sub in str(f.get("path", ""))]
        if not matched:
            errs.append(f"evidence: path_contains={sub!r} 인 팩트 없음")
            continue
        turns = set()
        for f in matched:
            turns.update(f.get("evidence_turns") or [])
        if must_turn is not None and must_turn not in turns:
            errs.append(
                f"evidence: {sub!r} 에 턴 {must_turn} 포함 기대, 실제 turns={sorted(turns)}"
            )
    return errs


def main() -> int:
    manifest_path = ROOT / "golden" / "manifest.json"
    cases = json.loads(manifest_path.read_text(encoding="utf-8"))
    failed = 0
    for case in cases:
        cid = case["id"]
        dpath = ROOT / case["dialogue"]
        mpath = ROOT / case["master"]
        exp_path = ROOT / case["expected_report"]
        ev_path = case.get("expected_evidence")
        bundle = json.loads(dpath.read_text(encoding="utf-8"))
        out = run_pipeline(
            bundle,
            mpath,
            extract_mode="mock",
            use_dummy_if_missing=False,
        )
        report = out["report"]
        val_errs = []
        try:
            validate_report(report)
        except Exception as e:
            val_errs.append(str(e))
        if val_errs:
            print(f"[FAIL] {cid} schema: {val_errs}")
            failed += 1
            continue
        expected = json.loads(exp_path.read_text(encoding="utf-8"))
        nr = normalize_report(report)
        ne = normalize_report(expected)
        if nr != ne:
            print(f"[FAIL] {cid} report mismatch")
            print("--- expected (norm) ---")
            print(json.dumps(ne, ensure_ascii=False, indent=2))
            print("--- actual (norm) ---")
            print(json.dumps(nr, ensure_ascii=False, indent=2))
            failed += 1
            continue
        if ev_path:
            eerrs = check_evidence(out["facts"], ROOT / ev_path)
            if eerrs:
                print(f"[FAIL] {cid} evidence:\n" + "\n".join(eerrs))
                failed += 1
                continue
        print(f"[OK] {cid}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
