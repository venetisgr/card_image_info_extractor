# backend/ — extraction & enrichment service (Python / FastAPI)

The cloud side of the system: the **Claude API engine** (Engine A) plus shared
**enrichment** (PSA cert lookup, checklist matching) and **normalization**. The
Android app also calls this service for enrichment and Claude fallback.

> Status: **Phase 0 scaffold.** Only the generated data models + tests exist so far.
> The FastAPI app and Claude integration land in Phase 1 (see `../roadmap.md`).

## Layout
```
backend/
├── pyproject.toml
└── app/
    └── models/
        ├── __init__.py
        └── card_info.py        # GENERATED from shared/schema (do not hand-edit)
└── tests/
    └── test_card_info.py        # schema <-> examples <-> model in sync
```

## Setup
```bash
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"      # add ".[api]" once Phase 1 starts
python -m pytest             # runs the model/schema sync tests
```

## Regenerating models
The Pydantic models are generated from `../shared/schema/card_info.schema.json`:
```bash
bash ../shared/codegen/generate.sh
```

## Planned (Phase 1+)
- `POST /extract` — multipart image(s) → Claude vision (structured output) → `CardInfo`.
- Prompt caching of the system prompt + schema; model tiering (Opus/Sonnet/Haiku).
- Enrichment: PSA public API (graded), checklist fuzzy-match (raw).
- Secrets server-side only (no keys in the app).
