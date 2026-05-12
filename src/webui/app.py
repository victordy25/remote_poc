"""데모용 웹 UI: sample.json → 파이프라인 → output 저장 및 표시."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "output"
SAMPLE_JSON = ROOT / "sample.json"
MASTER_JSON = ROOT / "poc" / "patient_master.example.json"
STATIC_DIR = Path(__file__).resolve().parent / "static"
TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"

app = FastAPI(title="대화→리포트 데모")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


def _ensure_src_path() -> None:
    src = ROOT / "src"
    import sys

    s = str(src)
    if s not in sys.path:
        sys.path.insert(0, s)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "index.html",
        {"request": request},
    )


@app.get("/api/input-preview")
async def input_preview() -> JSONResponse:
    if not SAMPLE_JSON.exists():
        return JSONResponse({"bundle": None, "error": "sample.json 없음"})
    bundle = json.loads(SAMPLE_JSON.read_text(encoding="utf-8"))
    return JSONResponse({"bundle": bundle})


@app.post("/api/run")
async def run_demo() -> JSONResponse:
    _ensure_src_path()
    from pipeline import run_pipeline

    if not SAMPLE_JSON.exists():
        raise HTTPException(400, f"없음: {SAMPLE_JSON}")
    if not MASTER_JSON.exists():
        raise HTTPException(400, f"없음: {MASTER_JSON}")

    bundle = json.loads(SAMPLE_JSON.read_text(encoding="utf-8"))
    try:
        out = run_pipeline(
            bundle,
            MASTER_JSON,
            extract_mode="mock",
            use_dummy_if_missing=False,
        )
    except Exception as e:
        raise HTTPException(500, str(e)) from e

    OUTPUT.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = OUTPUT / f"run_{stamp}"
    run_dir.mkdir(parents=True, exist_ok=True)

    report_path = run_dir / "report.json"
    facts_path = run_dir / "facts.json"
    meta_path = run_dir / "meta.json"
    dialogue_path = run_dir / "input_sample.json"

    report_path.write_text(
        json.dumps(out["report"], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    facts_path.write_text(
        json.dumps(out["facts"], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    meta_path.write_text(
        json.dumps(out["meta"], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    dialogue_path.write_text(
        json.dumps(bundle, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    latest = OUTPUT / "latest"
    latest.mkdir(parents=True, exist_ok=True)
    (latest / "report.json").write_text(
        json.dumps(out["report"], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (latest / "facts.json").write_text(
        json.dumps(out["facts"], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (latest / "meta.json").write_text(
        json.dumps(out["meta"], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (latest / "run_id.txt").write_text(stamp, encoding="utf-8")

    return JSONResponse(
        {
            "ok": True,
            "run_id": stamp,
            "paths": {
                "report": str(report_path.relative_to(ROOT)),
                "facts": str(facts_path.relative_to(ROOT)),
                "meta": str(meta_path.relative_to(ROOT)),
            },
            "report": out["report"],
            "facts": out["facts"],
            "meta": out["meta"],
        }
    )


@app.get("/api/latest")
async def latest_report() -> JSONResponse:
    base = OUTPUT / "latest"
    report_p = base / "report.json"
    if not report_p.exists():
        return JSONResponse({"report": None, "facts": None})
    facts_p = base / "facts.json"
    facts = None
    if facts_p.exists():
        facts = json.loads(facts_p.read_text(encoding="utf-8"))
    return JSONResponse(
        {
            "report": json.loads(report_p.read_text(encoding="utf-8")),
            "facts": facts,
        },
    )
