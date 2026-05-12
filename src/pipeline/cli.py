from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> None:
    p = argparse.ArgumentParser(description="대화 JSON → 리포트(JSON Schema)")
    p.add_argument("dialogue", type=Path, help="dialogue 번들 JSON 경로")
    p.add_argument(
        "-m",
        "--master",
        type=Path,
        default=None,
        help="patient_master JSON (A/B/C 기본값)",
    )
    p.add_argument(
        "--dummy",
        action="store_true",
        help="마스터 없을 때 A_대상자_정보 PoC 더미 주입",
    )
    p.add_argument(
        "--extract",
        choices=("mock", "llm"),
        default="mock",
        help="팩트 추출 방식",
    )
    p.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="리포트 JSON 저장 경로(미지정 시 stdout)",
    )
    p.add_argument("--facts-out", type=Path, default=None, help="중간 팩트 JSON 저장")
    p.add_argument("--meta-out", type=Path, default=None, help="메타 JSON 저장")
    args = p.parse_args()

    from pipeline import run_pipeline

    with args.dialogue.open(encoding="utf-8") as f:
        bundle = json.load(f)
    out = run_pipeline(
        bundle,
        args.master,
        extract_mode=args.extract,
        use_dummy_if_missing=args.dummy,
    )
    report = out["report"]
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
    else:
        json.dump(report, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
    if args.facts_out:
        args.facts_out.parent.mkdir(parents=True, exist_ok=True)
        with args.facts_out.open("w", encoding="utf-8") as f:
            json.dump(out["facts"], f, ensure_ascii=False, indent=2)
    if args.meta_out:
        args.meta_out.parent.mkdir(parents=True, exist_ok=True)
        with args.meta_out.open("w", encoding="utf-8") as f:
            json.dump(out["meta"], f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
