"""Merge EMR/master fields into the report. LLM must never invent A_대상자_정보."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any


def load_master(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def default_dummy_master() -> dict[str, Any]:
    """PoC-only placeholder. 운영에서는 실제 EMR/마스터만 사용."""
    return {
        "A_대상자_정보": {
            "성명": "POC_미식별",
            "주민등록번호": "000000-0000000",
            "등록일자": "2000-01-01",
        },
        "C_점검사항_defaults": {
            "관리자정보": {
                "직종": "간호사",
                "성명": "POC_관리자",
                "면허번호": "",
                "자격번호": "",
            },
            "관리방법": ["전화"],
            "관리횟수": "1회",
            "관리제공_대상": "환자",
        },
    }


def merge_master(
    dialogue_derived: dict[str, Any],
    master: dict[str, Any],
    *,
    use_dummy_if_missing: bool = False,
) -> dict[str, Any]:
    """
    dialogue_derived: 스키마 부분 트리 (보통 B, C 중 대화에서 온 값).
    master: patient_master JSON — A_대상자_정보, C_점검사항_defaults 등.
    """
    m = deepcopy(master)
    if not m.get("A_대상자_정보") and use_dummy_if_missing:
        m = {**default_dummy_master(), **m}

    out: dict[str, Any] = deepcopy(dialogue_derived)

    if "A_대상자_정보" in m:
        out["A_대상자_정보"] = deepcopy(m["A_대상자_정보"])
    if "B_복막투석_유형" in m:
        out["B_복막투석_유형"] = deepcopy(m["B_복막투석_유형"])

    defaults = m.get("C_점검사항_defaults") or {}
    c = out.get("C_점검사항")
    if defaults:

        def deep_merge(base: dict, over: dict) -> dict:
            r = deepcopy(base)
            for k, v in over.items():
                if k in r and isinstance(r[k], dict) and isinstance(v, dict):
                    r[k] = deep_merge(r[k], v)
                else:
                    r[k] = deepcopy(v)
            return r

        if isinstance(c, dict):
            out["C_점검사항"] = deep_merge(defaults, c)
        else:
            out["C_점검사항"] = deepcopy(defaults)

    return out
