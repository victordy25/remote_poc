"""대화 JSON 정규화: 번호·단위·공백."""

from __future__ import annotations

import re
from copy import deepcopy
from typing import Any


def normalize_text(text: str) -> str:
    t = text.strip()
    t = re.sub(r"(\d),(\d)", r"\1\2", t)
    return t


def preprocess_dialogue_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    out = deepcopy(bundle)
    for turn in out.get("dialogue", []) or []:
        if isinstance(turn.get("text"), str):
            turn["text"] = normalize_text(turn["text"])
    return out
