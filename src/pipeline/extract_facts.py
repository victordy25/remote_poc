"""대화에서 중간 팩트(JSON) 추출: LLM 또는 PoC 휴리스틱."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from . import policies

ROOT = Path(__file__).resolve().parents[2]
FACTS_SCHEMA_PATH = ROOT / "schemas" / "extracted_facts.schema.json"


def _load_facts_schema() -> dict[str, Any]:
    with FACTS_SCHEMA_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def validate_facts_doc(doc: dict[str, Any]) -> None:
    schema = _load_facts_schema()
    Draft202012Validator(schema).validate(doc)


def _dialogue_texts(dialogue: list[dict[str, Any]]) -> list[tuple[int, str, str]]:
    out: list[tuple[int, str, str]] = []
    for i, turn in enumerate(dialogue):
        sp = str(turn.get("speaker", ""))
        tx = str(turn.get("text", ""))
        out.append((i, sp, tx))
    return out


def extract_facts_mock(dialogue: list[dict[str, Any]]) -> dict[str, Any]:
    """룰+키워드 보조 추출. 테스트·오프라인용."""
    facts: list[dict[str, Any]] = []
    for i, _sp, tx in _dialogue_texts(dialogue):
        m_w = re.search(r"체중.*?(\d+(?:\.\d+)?)\s*kg", tx, re.I)
        if m_w:
            facts.append(
                {
                    "path": "임상정보.체중",
                    "value": {"측정가능여부": True, "수치": float(m_w.group(1))},
                    "source": "stated",
                    "evidence_turns": [i],
                    "confidence": "high",
                }
            )
        m_bp = re.search(r"혈압.*?(\d+)\s*에\s*(\d+)", tx)
        if m_bp:
            facts.append(
                {
                    "path": "임상정보.혈압",
                    "value": f"{m_bp.group(1)}/{m_bp.group(2)}",
                    "source": "stated",
                    "evidence_turns": [i],
                    "confidence": "high",
                }
            )
        m_cc = re.search(r"(\d[\d,]*)\s*cc", tx, re.I)
        if m_cc:
            cc = int(m_cc.group(1).replace(",", ""))
            facts.append(
                {
                    "path": "임상정보.평균_제수량",
                    "value": cc,
                    "source": "stated",
                    "evidence_turns": [i],
                    "confidence": "medium",
                }
            )
            if re.search(r"덜\s*나온|평소보다", tx):
                facts.append(
                    {
                        "path": "투석_도관_및_환자상태.투석액_배액_상태.결과",
                        "value": "제수량 부족",
                        "source": "inferred",
                        "evidence_turns": [i],
                        "confidence": "medium",
                    }
                )
                facts.append(
                    {
                        "path": "투석_도관_및_환자상태.투석액_배액_상태.특이사항",
                        "value": "환자 주관적 호소로 제수량 감소 의심",
                        "source": "inferred",
                        "evidence_turns": [i],
                        "confidence": "low",
                    }
                )
        if re.search(r"막걸리|탁하", tx):
            facts.append(
                {
                    "path": "투석_도관_및_환자상태.투석액_상태.결과",
                    "value": "이상",
                    "source": "inferred",
                    "evidence_turns": [i],
                    "confidence": "medium",
                }
            )
        elif re.search(r"맑아|맑\s|맑\.", tx) or re.search(r"맑은|맑네|맑고", tx):
            facts.append(
                {
                    "path": "투석_도관_및_환자상태.투석액_상태.결과",
                    "value": "양호",
                    "source": "stated",
                    "evidence_turns": [i],
                    "confidence": "high",
                }
            )
        if re.search(r"잠을.*?못|밤새", tx):
            facts.append(
                {
                    "path": "투석_도관_및_환자상태.환자_상태.수면장애",
                    "value": True,
                    "source": "stated",
                    "evidence_turns": [i],
                    "confidence": "high",
                }
            )
        if re.search(r"가려", tx):
            facts.append(
                {
                    "path": "투석_도관_및_환자상태.환자_상태.소양증",
                    "value": True,
                    "source": "stated",
                    "evidence_turns": [i],
                    "confidence": "high",
                }
            )
        if re.search(r"무거운|부종", tx):
            facts.append(
                {
                    "path": "투석_도관_및_환자상태.환자_상태.부종",
                    "value": True,
                    "source": "inferred",
                    "evidence_turns": [i],
                    "confidence": "low",
                }
            )
        if re.search(r"진물", tx) and re.search(r"긁|다리", tx):
            facts.append(
                {
                    "path": "투석_도관_및_환자상태.출구_부위_이상_여부.특이사항",
                    "value": "다리 가려움으로 긁은 후 진물 호소(출구 여부 불명확)",
                    "source": "stated",
                    "evidence_turns": [i],
                    "confidence": "medium",
                }
            )
        if re.search(r"내일.*?병원|병원.*?내일|내원|외래|응급", tx):
            if re.search(r"응급", tx):
                facts.append(
                    {
                        "path": "내원_지시",
                        "value": "응급실",
                        "source": "inferred",
                        "evidence_turns": [i],
                        "confidence": "medium",
                    }
                )
            else:
                facts.append(
                    {
                        "path": "내원_지시",
                        "value": "외래",
                        "source": "stated",
                        "evidence_turns": [i],
                        "confidence": "high",
                    }
                )
        if re.search(r"교수|의사.*?말씀|보고", tx):
            facts.append(
                {
                    "path": "보고_의사",
                    "value": True,
                    "source": "inferred",
                    "evidence_turns": [i],
                    "confidence": "medium",
                }
            )
        if re.search(r"알람|삑삑", tx):
            facts.append(
                {
                    "path": "투석_도관_및_환자상태.투석액_주입_상태.특이사항",
                    "value": "기기 알람 다수 호소",
                    "source": "stated",
                    "evidence_turns": [i],
                    "confidence": "medium",
                }
            )

    doc = {"schema_version": "1", "facts": facts, "narrative_notes": []}
    validate_facts_doc(doc)
    return doc


def _load_prompt(name: str) -> str:
    p = ROOT / "prompts" / name
    return p.read_text(encoding="utf-8")


def extract_facts_llm(dialogue: list[dict[str, Any]], *, model: str | None = None) -> dict[str, Any]:
    """OpenAI Responses API JSON 스키마 모드(가능 시)."""
    try:
        from openai import OpenAI
    except ImportError as e:
        raise RuntimeError("openai 패키지가 필요합니다.") from e

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY 미설정")

    client = OpenAI()
    model = model or os.environ.get("OPENAI_MODEL", "gpt-4.1-mini")
    schema = _load_facts_schema()
    dialogue_json = json.dumps(dialogue, ensure_ascii=False)

    system = _load_prompt("system_extract.txt").strip() + "\n\n" + policies.INFERENCE_POLICY.strip()
    glossary = _load_prompt("glossary.txt")
    user = f"""용어집:\n{glossary}\n\n대화 JSON:\n{dialogue_json}\n\n위 대화에서만 팩트를 추출하세요."""

    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "extracted_facts",
                "schema": schema,
                "strict": False,
            },
        },
    )
    raw = resp.choices[0].message.content
    if not raw:
        raise RuntimeError("빈 LLM 응답")
    doc = json.loads(raw)
    validate_facts_doc(doc)
    return doc


def extract_facts(
    dialogue: list[dict[str, Any]],
    *,
    mode: str = "mock",
    model: str | None = None,
) -> dict[str, Any]:
    if mode == "mock":
        return extract_facts_mock(dialogue)
    if mode == "llm":
        return extract_facts_llm(dialogue, model=model)
    raise ValueError(f"unknown mode: {mode}")
