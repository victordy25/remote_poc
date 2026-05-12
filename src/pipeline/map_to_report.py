"""팩트 배열 → C_점검사항 중첩 dict. 보수적 기본값은 policies에서."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from .policies import CONSERVATIVE_DEFAULTS, SERVICE_TAGS_FROM_KEYWORDS


def _ensure_branch(c: dict[str, Any], *keys: str) -> dict[str, Any]:
    cur: Any = c
    for k in keys:
        if k not in cur or not isinstance(cur[k], dict):
            cur[k] = {}
        cur = cur[k]
    assert isinstance(cur, dict)
    return cur


def facts_to_c_section(
    facts_doc: dict[str, Any],
    *,
    dialogue_extra_text: str = "",
) -> dict[str, Any]:
    facts: list[dict[str, Any]] = list(facts_doc.get("facts") or [])
    c: dict[str, Any] = deepcopy(CONSERVATIVE_DEFAULTS)

    patient_symptoms: set[str] = set()
    service: set[str] = set()

    for f in facts:
        path = str(f.get("path", ""))
        val = f.get("value")
        if not path:
            continue

        if path.startswith("임상정보."):
            sub = path.removeprefix("임상정보.")
            if sub == "체중" and isinstance(val, dict):
                br = _ensure_branch(c, "임상정보")
                br["체중"] = val
            elif sub == "혈압":
                br = _ensure_branch(c, "임상정보")
                br["혈압"] = str(val)
            elif sub == "평균_제수량":
                br = _ensure_branch(c, "임상정보")
                br["평균_제수량"] = val

        elif path.startswith("투석_도관_및_환자상태."):
            rel = path.removeprefix("투석_도관_및_환자상태.")
            br = _ensure_branch(c, "투석_도관_및_환자상태")
            if rel.startswith("환자_상태."):
                sym = rel.removeprefix("환자_상태.")
                if val is True and sym:
                    patient_symptoms.add(sym)
            elif "." in rel:
                a, b = rel.split(".", 1)
                if a not in br or not isinstance(br[a], dict):
                    br[a] = {}
                br[a][b] = val
            else:
                br[rel] = val

        elif path == "내원_지시":
            c["내원_지시"] = val
        elif path == "보고_의사":
            c["보고_의사"] = bool(val)

    if patient_symptoms:
        br = _ensure_branch(c, "투석_도관_및_환자상태")
        br["환자_상태"] = sorted(patient_symptoms)

    flat_text = dialogue_extra_text + " " + " ".join(str(f.get("value", "")) for f in facts)
    for kw, tag in SERVICE_TAGS_FROM_KEYWORDS:
        if kw in flat_text:
            service.add(tag)
    if service:
        c["서비스_제공내용"] = sorted(service)

    td = c.get("투석_도관_및_환자상태") or {}
    chu = td.get("출구_부위_이상_여부")
    if isinstance(chu, dict) and "증상" not in chu:
        if chu.get("특이사항"):
            chu["증상"] = ["양호"]
        else:
            chu["증상"] = ["양호"]

    return c


def build_report_tree(
    facts_doc: dict[str, Any],
    *,
    b_section: dict[str, Any] | None = None,
    dialogue: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """A 제외 대화 기반 트리. A는 merge_master에서 주입."""
    extra = ""
    if dialogue:
        extra = " ".join(str(t.get("text", "")) for t in dialogue)
    out: dict[str, Any] = {}
    if b_section:
        out["B_복막투석_유형"] = b_section
    out["C_점검사항"] = facts_to_c_section(facts_doc, dialogue_extra_text=extra)
    return out
