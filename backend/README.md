# backend/ — extraction & enrichment service (Python / FastAPI)

The cloud side of the system: the **Claude API engine** (Engine A) plus, in later
phases, shared **enrichment** (PSA cert lookup, checklist matching) and
**normalization**. The Android app also calls this service for enrichment and
Claude fallback.

> Status: **Phase 1 complete.** `POST /extract` performs live Claude extraction
> (front + back → validated `CardInfo`), with prompt caching, model tiering, and
> a corrective validation retry. Enrichment (Phase 2) is next.

## Layout
```
backend/
├── pyproject.toml
├── .env                        # ANTHROPIC_API_KEY=... (git-ignored; create locally)
└── app/
    ├── main.py                 # FastAPI app: POST /extract, GET /healthz
    ├── cli.py                  # python -m app.cli front.jpg [back.jpg]
    ├── config.py               # model tiers, limits, .env loader
    ├── models/card_info.py     # GENERATED from shared/schema (do not hand-edit)
    └── services/
        ├── images.py           # EXIF fix, RGB, resize ≤2576px, JPEG re-encode
        ├── prompts.py          # system prompt + tool schema (static → cacheable)
        └── extractor.py        # forced tool use, validation + 1 corrective retry
└── tests/                      # all mocked; no network needed
```

## Setup
```bash
python -m venv .venv && . .venv/bin/activate
pip install -e ".[api,dev]"
echo 'ANTHROPIC_API_KEY=sk-ant-...' > .env    # never commit this
python -m pytest                              # 34 tests, no network
```

## Run
```bash
# API server
uvicorn app.main:app --reload
curl -F front=@front.jpg -F back=@back.jpg -F model=opus localhost:8000/extract

# CLI
python -m app.cli front.jpg back.jpg --model opus --out card.json
```

## How extraction works (see architecture_components.md §6)
- **Forced tool use**: the model must call `record_card_info`; its input schema is
  the shared `CardInfo` contract minus server-side fields (`provenance`,
  `raw_output`), which the server stamps afterwards.
- **Validation + retry**: the payload is validated against the shared JSON Schema
  (including the graded-requires-`graded` rule); on failure the errors are sent
  back as an errored `tool_result` and the model gets ONE corrective retry.
  (The tools API rejects top-level `allOf`, so that rule lives server-side.)
- **Prompt caching**: the system prompt (field guide + placeholder + worked
  example) is static; a single `cache_control` breakpoint caches tools + system.
  Measured live: 8.5k tokens cached, ~49% cost drop on the second call.
- **Model tiering**: `model=opus|sonnet|haiku` (→ `claude-opus-4-8`,
  `claude-sonnet-5`, `claude-haiku-4-5`) or any full model id. Default: opus.

## Planned (Phase 2+)
- Enrichment: PSA public API (graded cert verification), checklist fuzzy-match
  (raw), brand/set normalization tables; response caching for external APIs.
- Persistence (Postgres) + request logging/metrics.
