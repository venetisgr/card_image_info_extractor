# Sports Card Image Information Extractor

Extract structured information from photos of **sports cards** — graded (slabbed) or
raw (ungraded) — via two interchangeable engines that emit the same JSON contract:

- **Engine A — Claude API** (cloud, behind a FastAPI backend proxy).
- **Engine B — On-device** (Android: CameraX + ML Kit OCR + TFLite), offline-capable.

Both faces of the card (**front + back**) are used as input.

## What we extract (priority fields)
Captured by the canonical [`CardInfo`](shared/schema/card_info.schema.json) schema
(see also the human-readable
[placeholder template](shared/templates/card_info_placeholder.json)):

| Want | Field |
|---|---|
| Was it graded? | `card_type` (`graded` / `raw`) |
| Grading company (PSA, Beckett/BGS, …) | `graded.grading_company` |
| Certificate id | `graded.cert_number` |
| Description printed on the graded label | `graded.description` |
| Sport / year / brand / set / subset | `sport`, `year`, `brand`, `set`, `subset` |
| Player name | `player_name` |
| Card number within the set | `card_number` |
| Autograph yes/no + ink color (black standard, other = rarer) | `autograph.present`, `autograph.ink_color` |
| Colors of the jersey in the player's photo | `photo.jersey_colors` |
| Number on the jersey in the photo (+ candidates when unsure) | `photo.jersey_number`, `photo.jersey_number_candidates` |
| Memorabilia yes/no (patch/ball/floor/jersey/shoe; can be several) | `memorabilia.present`, `memorabilia.pieces[]` |
| Per piece: real fabric? colors + unique count, team-logo part, name/team letters | `pieces[].is_fabric`, `colors`, `unique_color_count`, `contains_*`, `letters_visible` |
| Limited card 07/99 → this copy's number (07) and print run (99) | `attributes.serial_number`, `attributes.serial_limit` |
| Serial matches the player's jersey number (rarer) | `attributes.serial_matches_jersey_number` |

Plus `parallel`, `team`, grade/subgrades, and per-field confidence. Extraction
hint baked into prompts: year/brand/set/subset are usually at the **bottom of the
card front** and on the **graded label**; front + back are always both provided.

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
