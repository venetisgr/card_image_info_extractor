# Sports Card Image Information Extractor

Extract structured information from photos of **sports cards** — graded (slabbed) or
raw (ungraded) — via two interchangeable engines that emit the same JSON contract:

- **Engine A — Claude API** (cloud, behind a FastAPI backend proxy).
- **Engine B — On-device** (Android: CameraX + ML Kit OCR + TFLite), offline-capable.

Both faces of the card (**front + back**) are used as input.

## What we extract (priority fields)
Captured by the canonical [`CardInfo`](shared/schema/card_info.schema.json) schema:

| Want | Field |
|---|---|
| Was it graded? | `card_type` (`graded` / `raw`) |
| Grading company (PSA, Beckett/BGS, …) | `graded.grading_company` |
| Certificate id | `graded.cert_number` |
| Player name | `player_name` |
| Colors of the jersey in the player's photo | `photo.jersey_colors` |
| Number on the jersey in the photo | `photo.jersey_number` |
| Colors of the embedded real-life jersey swatch | `relic.swatch_colors` |
| Limited card like 5/30 → the card's number (5) | `attributes.serial_number` |
| …and the total population (30) | `attributes.serial_limit` |

Plus optional enrichment fields: `year`, `manufacturer`, `set`, `subset`,
`parallel`, `card_number`, `team`, grade/subgrades, and per-field confidence.

## Repository layout
```
shared/    canonical CardInfo JSON Schema (source of truth) + codegen + examples
backend/   FastAPI service: Claude extraction + enrichment + normalization
android/   on-device Kotlin app (CameraX, ML Kit, TFLite)
ml/        on-device model training & TFLite conversion
data/      datasets, labels, reference tables
eval/      evaluation harness (Claude vs on-device)
```

## Planning docs
- [architecture_components.md](architecture_components.md) — system design & components
- [roadmap.md](roadmap.md) — phased plan (Phase 0 → 6)
- [pending_tasks.md](pending_tasks.md) · [completed_tasks.md](completed_tasks.md)
- [scratchpad.md](scratchpad.md) — ideas, decisions, dead ends
- [resources.md](resources.md) — people, APIs, libraries, data, infra, costs

## Quick start (Phase 0)
```bash
# backend: validate schema <-> examples <-> generated Pydantic model
cd backend
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
python -m pytest

# regenerate Pydantic + Kotlin types after editing the schema
bash ../shared/codegen/generate.sh
```

## Status
**Phase 0 — Foundations.** The `CardInfo` schema, generated Pydantic + Kotlin types,
examples, tests, and repo scaffold are in place. Next: seed dataset + Phase 1 Claude
extraction endpoint. See [roadmap.md](roadmap.md) and [pending_tasks.md](pending_tasks.md).
