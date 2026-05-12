"""대화 번들 → 검증된 리포트 JSON."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from .extract_facts import extract_facts
from .map_to_report import build_report_tree
from .merge_master import load_master, merge_master
from .preprocess import preprocess_dialogue_bundle
from .validate import validate_report


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def run_pipeline(
    dialogue_bundle: dict[str, Any],
    master_path: Path | None,
    *,
    extract_mode: str = "mock",
    model: str | None = None,
    use_dummy_if_missing: bool = False,
    template_path: Path | None = None,
) -> dict[str, Any]:
    pre = preprocess_dialogue_bundle(dialogue_bundle)
    dialogue = pre.get("dialogue") or []
    facts = extract_facts(dialogue, mode=extract_mode, model=model)
    tree = build_report_tree(facts, dialogue=dialogue)
    master = load_master(master_path)
    merged = merge_master(tree, master, use_dummy_if_missing=use_dummy_if_missing)
    validate_report(merged)
    root = Path(__file__).resolve().parents[2]
    tpl = template_path or (root / "report_template.json")
    meta = {
        "report_template_sha16": _sha256_file(tpl),
        "extract_mode": extract_mode,
    }
    return {"report": merged, "facts": facts, "meta": meta}


def run_pipeline_report_only(*args: Any, **kwargs: Any) -> dict[str, Any]:
    return run_pipeline(*args, **kwargs)["report"]
