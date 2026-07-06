# Completed Tasks

**Project:** Sports Card Image Information Extractor
**Last updated:** 2026-07-06
**See also:** `pending_tasks.md` (open work).

Newest first. When a task from `pending_tasks.md` is done, move it here with the date
and a short note/links.

| Date | ID | Task | Notes |
|---|---|---|---|
| 2026-07-06 | P2-1, P2-2 | **Phase 2: PSA cert verification wired** | `services/psa.py`: PSA public-API client (bearer token, on-disk cache for the ~100/day free tier, PSAError taxonomy incl. 401/429/404). `services/enrich.py`: verified-beats-extracted reconciliation — PSA record overrides year/brand/set/player/card#/sport/grade, confidence→1.0, audit trail in `raw_output.verification`; never fails an extraction. Wired into `/extract` (default on, `enrich=false` to skip), CLI (`--no-enrich`), and `GET /verify/psa/{cert}`. 52 tests green. Live calls pending a PSA_API_TOKEN. |
| 2026-07-06 | P0-6 (partial) + prompt v2 | **Real-photo ground truth + lessons** | Read the user's 15 real photos (11 distinct cards: PSA/BGS slabs, one-touch raws, letter patch, 3-piece relic, screenshot, rotated back). Wrote schema-valid labels to `data/labels/` + `data/manifest.csv`; added `graded.autograph_grade` (BGS "10 AUTOGRAPH"); prompt v2: one-touch≠graded, slab-back branding, serial-on-back, sticker autos, silver ink on patches, letterman patches, screenshot chrome, rotated text. `eval/compare.py` for per-field scoring. Photo files still needed (P1-10). |
| 2026-07-06 | P1-1..9 | **Phase 1: Claude extraction engine live** | `backend/`: FastAPI `POST /extract` + CLI. Forced tool use with the shared schema (minus server-side fields); server-side validation incl. graded-conditional + 1 corrective retry; EXIF/resize/JPEG preprocessing; front+back in one turn; provenance stamped server-side; model tiers opus/sonnet/haiku (default `claude-opus-4-8`). **Live-verified** on synthetic graded patch-auto card: all priority fields correct (BGS 9.5, cert, 23/99 jersey-matched serial, blue ink, 3-color patch w/ logo part). Prompt caching measured: 8,496 tokens cached, 2nd call 100% cache read, ~49% cheaper (~$0.10 → ~$0.05/scan). 34 tests green (mocked, no network). |
| 2026-07-06 | P0-1v2 | `CardInfo` schema **v2** per detailed field spec | Added: `brand` (renamed from manufacturer), `graded.description`, `autograph.{present,ink_color}` (black=standard), `memorabilia.pieces[]` (type patch/jersey/ball/floor/shoe, `is_fabric`, colors+`unique_color_count`, team-logo/name/team-letter parts, `letters_visible`), `photo.jersey_number_candidates`, `attributes.serial_matches_jersey_number`; card# vs serial disambiguated. Types regenerated (Pydantic+Kotlin); 12 tests green. |
| 2026-07-06 | P0-9 | JSON placeholder template | `shared/templates/card_info_placeholder.json` — every field with allowed values; schema-sync guarded by a test. |
| 2026-06-03 | P0-1 | `CardInfo` JSON Schema | `shared/schema/card_info.schema.json` (draft 2020-12). Priority fields per spec: graded?/company/cert, player, `photo.jersey_colors`+`jersey_number`, `relic.swatch_colors`, serial 5/30. Validated + negative test. |
| 2026-06-03 | P0-2 | Codegen → Pydantic + Kotlin | Generated `backend/app/models/card_info.py` (Pydantic v2) and `android/.../CardInfo.kt` (kotlinx) from the schema via `shared/codegen/generate.sh`. |
| 2026-06-03 | P0-3 | Repo scaffold + tests | Dirs shared/backend/android/ml/data/eval, READMEs, `.gitignore`, root README. Backend `pytest` (10 tests) green: schema⇄examples⇄model in sync. |
| 2026-06-03 | P0-0e | Resources doc | `resources.md`: people, accounts/APIs, libraries, data, hardware, infra, cost model — grounded with source links. |
| 2026-06-03 | P0-0d | Scratchpad created | `scratchpad.md`: decisions log, ideas-to-try, open questions, "what didn't work" template. |
| 2026-06-03 | P0-0c | Task tracking created | `pending_tasks.md` (backlog by phase, P0–P1 detailed) + this `completed_tasks.md`. |
| 2026-06-03 | P0-0b | Roadmap drafted | `roadmap.md`: 7 phases (0–6) with goal/design/exit criteria + milestones. |
| 2026-06-03 | P0-0a | Architecture drafted | `architecture_components.md`: two-engine design, shared `CardInfo` contract, pipeline, components, repo layout. |
| 2026-06-03 | — | Research & decisions | Confirmed PSA public cert API, ML Kit/PaddleOCR on-device OCR, `claude-opus-4-8` vision + pricing, card data sources. Locked: Native Android (Kotlin) · backend proxy (FastAPI) · graded+raw from v1. |

---

## Notes
- The first batch above is the **planning/documentation** deliverable that
  bootstraps the project. Engineering tasks (P0-1 onward) are tracked in
  `pending_tasks.md`.
