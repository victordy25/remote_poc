# remote_poc — 대화 → 모니터링 리포트 (JSON Schema)

복막투석 재택 전화상담 등 **자연어 대화 JSON**을 입력으로 받아, **환자 모니터링 리포트** 인스턴스(`report_template.json` JSON Schema 준수)를 생성하는 PoC입니다.  
생활어·다화자(간호사/환자) 대화에는 단순 룰만으로 한계가 있어, **중간 팩트 추출 → 스키마 매핑 → 마스터 병합 → 기계 검증** 구조로 두었습니다.

## 아키텍처

```
dialogue 번들 JSON          patient_master JSON (EMR/등록)
        │                              │
        ▼                              │
   preprocess                          │
        ▼                              │
 extract_facts (mock | OpenAI LLM)     │
        ▼                              │
   build_report_tree (C 위주)         │
        └──────────────┬───────────────┘
                       ▼
                merge_master
                       ▼
               validate_report
                       ▼
            report + facts + meta
```

- **`A_대상자_정보`**(성명·주민번호·등록일 등)는 대화에서 추론하지 않고 **`patient_master` JSON**에서만 채웁니다.
- **`mock`**: 정규식·키워드 기반 추출(기본값, API 불필요).
- **`llm`**: OpenAI Chat Completions + 구조화 출력으로 팩트 추출(`OPENAI_API_KEY` 필요).

## 디렉터리 개요

| 경로 | 설명 |
|------|------|
| `src/pipeline/` | 전처리, 추출, 매핑, 병합, 검증, CLI |
| `src/webui/` | 로컬 데모용 FastAPI UI |
| `schemas/extracted_facts.schema.json` | 중간 팩트 JSON 스키마 |
| `report_template.json` | 최종 리포트 JSON Schema |
| `sample.json` | 데모용 대화 번들 |
| `poc/patient_master.example.json` | 예시 마스터(A/B/C 기본값) |
| `docs/` | GitHub Pages 정적 사이트(`index.html` + CI 생성 JSON) |
| `golden/` | 회귀 테스트용 골든 케이스 |
| `scripts/build_docs.py` | Pages 배포 전 `docs/*.json` 생성 |
| `scripts/eval.py` | 골든 세트 평가 |

## 요구 사항

- Python **3.11+**

## 설치

```bash
cd remote_poc
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate   # Linux / macOS

pip install -e .
# 선택: 로컬 웹 UI
pip install -e ".[ui]"
# 선택: 테스트
pip install -e ".[dev]"
```

## CLI — 대화 파일 → 리포트 JSON

```bash
python -m pipeline.cli dialogue_sample.json -m poc/patient_master.example.json -o report.json --facts-out facts.json
```

- 마스터 없이 PoC만 돌릴 때: **`--dummy`** (`A_대상자_정보` 더미 주입).
- LLM 사용: **`--extract llm`** + 환경 변수  
  - `OPENAI_API_KEY` (필수)  
  - `OPENAI_MODEL` (선택, 기본 `gpt-4.1-mini`)

## 로컬 웹 UI

```bash
pip install -e ".[ui]"
uvicorn webui.app:app --host 127.0.0.1 --port 8765
# 또는: remote-poc-demo
```

브라우저에서 `http://127.0.0.1:8765` — `sample.json` 기준으로 파이프라인 실행 후 **`output/`**에 저장하고 화면에 표시합니다.

## GitHub Pages

1. 저장소 **Settings → Pages → Source: GitHub Actions** 로 설정합니다.
2. `main`(또는 `master`)에 푸시하면 `.github/workflows/pages.yml`이 `scripts/build_docs.py`로 `docs/`에 JSON을 생성한 뒤 사이트를 배포합니다.
3. 로컬에서 정적 페이지만 미리보려면:

```bash
python scripts/build_docs.py
# 브라우저로 docs/index.html 열기
```

`docs/report.json` 등은 `.gitignore`에 두어 저장소에는 올리지 않고, **CI 산출물**로 Pages에만 포함됩니다.

## 테스트 · 평가

```bash
python -m pytest tests/ -v
python scripts/eval.py
```

## 라이선스

명시 없음 — 내부 PoC용으로 사용하세요.

## 원격 저장소

기본 원격: `https://github.com/victordy25/remote_poc.git`
