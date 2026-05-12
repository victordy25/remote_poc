"""report_template.json 으로 산출물 검증."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

ROOT = Path(__file__).resolve().parents[2]
REPORT_SCHEMA_PATH = ROOT / "report_template.json"


def load_report_schema() -> dict[str, Any]:
    with REPORT_SCHEMA_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def validate_report(instance: dict[str, Any]) -> None:
    schema = load_report_schema()
    # format(date 등) 검증은 선택 패키지 의존이 있어 기본 Draft 검증만 수행
    Draft202012Validator(schema).validate(instance)


def validate_report_safe(instance: dict[str, Any]) -> list[str]:
    try:
        validate_report(instance)
        return []
    except ValidationError as e:
        return [str(e.message)]
