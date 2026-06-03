# Pending Tasks

**Project:** Sports Card Image Information Extractor
**Last updated:** 2026-06-03
**See also:** `roadmap.md` (phases), `completed_tasks.md` (done), `scratchpad.md`.

## Conventions
- `- [ ]` open · `- [~]` in progress · move to `completed_tasks.md` when done.
- Each task: **what** — *acceptance criteria*.
- IDs are `P<phase>-<n>`. Priority: 🔴 high · 🟡 med · 🟢 low.

---

## 🔜 In progress
- [~] **P0-0** Project bootstrap & docs — *the six planning docs exist and are
  committed* (this is being completed now; see `completed_tasks.md`).

---

## Phase 0 — Foundations
- [ ] 🔴 **P0-1** Define `CardInfo` **JSON Schema** in `/shared` — *schema covers all
  fields in `architecture_components.md` §4 and validates the two examples.*
- [ ] 🔴 **P0-2** Codegen from schema → **Pydantic** + **Kotlin** types — *generated
  types compile in `/backend` and `/android`.*
- [ ] 🔴 **P0-3** Scaffold repo dirs (`backend`, `android`, `shared`, `ml`, `data`,
  `eval`) with minimal build files — *each subproject builds empty.*
- [ ] 🟡 **P0-4** **Seed dataset**: collect 100–200 images (graded + raw; baseball,
  basketball, football, hockey, soccer; varied eras/conditions; front+back) —
  *images stored in `/data` with a manifest.*
- [ ] 🟡 **P0-5** Labeling guidelines + label format aligned to `CardInfo` — *a
  labeler can produce ground-truth JSON unambiguously.*
- [ ] 🟡 **P0-6** Label the seed dataset — *ground-truth JSON for every seed image.*
- [ ] 🟢 **P0-7** CI (GitHub Actions): lint + test for backend & android — *CI green.*
- [ ] 🔴 **P0-8** Secrets strategy doc (server-side only; no keys in app) — *written
  and referenced in `resources.md`.*

## Phase 1 — Claude API vertical slice
- [ ] 🔴 **P1-1** FastAPI skeleton + `POST /extract` (multipart images) — *returns
  200 with a stub `CardInfo`.*
- [ ] 🔴 **P1-2** Image pre-processing: EXIF-strip, resize ≤2576 px long edge —
  *validated on sample images.*
- [ ] 🔴 **P1-3** Claude extraction with **structured output** (tool/JSON-schema) →
  `CardInfo` — *valid output for a clear graded and a clear raw sample.*
- [ ] 🔴 **P1-4** **Prompt caching** of system prompt + schema + few-shot — *cache
  hits observed; cost/latency drop measured.*
- [ ] 🟡 **P1-5** Schema validation + one corrective retry — *malformed output is
  caught and corrected or surfaced.*
- [ ] 🟡 **P1-6** Front+back handling — *both images sent; back fields improve fill.*
- [ ] 🟡 **P1-7** Model-tiering flag (Opus/Sonnet/Haiku) — *switchable per request.*
- [ ] 🟢 **P1-8** CLI/notebook wrapper for local runs — *one command extracts an img.*

## Phase 2 — Enrichment & verification
- [ ] 🔴 **P2-1** PSA **public API** client (OAuth2 + caching) — *cert # → fields.*
- [ ] 🔴 **P2-2** Wire graded path: cert # → lookup → reconcile/override — *graded
  samples become verified.*
- [ ] 🟡 **P2-3** Third-party verifier adapters (BGS/CGC/SGC/TAG) — *at least one
  non-PSA company resolved.*
- [ ] 🔴 **P2-4** Import **checklist DB** (TCDB / SportsCardsPro) into Postgres —
  *queryable by player/year/brand/number.*
- [ ] 🟡 **P2-5** Raw fuzzy-match + fill — *measurable fill-rate improvement on raw
  samples.*
- [ ] 🟡 **P2-6** Manufacturer/set **normalization tables** — *aliases canonicalized.*

## Phase 3 — On-device baseline (Android)
- [ ] 🔴 **P3-1** Android project + **CameraX** capture (front/back) + gallery import.
- [ ] 🔴 **P3-2** OpenCV pre-processing (quad detect, perspective warp, orient).
- [ ] 🔴 **P3-3** **ML Kit Text Recognition v2** integration → OCR text.
- [ ] 🔴 **P3-4** **ML Kit Barcode** → slab cert #.
- [ ] 🔴 **P3-5** Rules-based parser + bundled reference subset → `CardInfo`.
- [ ] 🟡 **P3-6** **Room** storage + scan history UI.
- [ ] 🟡 **P3-7** **Retrofit** client: enrichment + **Claude fallback**.
- [ ] 🟢 **P3-8** On-device vs cloud **mode toggle**.

## Phase 4 — On-device DL models
- [ ] 🟡 **P4-1** Auto-label pipeline (Claude-as-labeler) + human review.
- [ ] 🔴 **P4-2** Train **graded-vs-raw** classifier → TFLite int8.
- [ ] 🔴 **P4-3** Train **card/slab + region detector** → TFLite int8.
- [ ] 🟢 **P4-4** Optional brand/logo + field-mapping models.
- [ ] 🟡 **P4-5** GPU/NNAPI integration + on-device benchmarks (accuracy/latency/size).

## Phase 5 — Eval, reconciliation & fallback
- [ ] 🔴 **P5-1** Eval harness (`/eval`): per-field accuracy, latency, cost.
- [ ] 🟡 **P5-2** A/B Claude vs on-device report + CI regression check.
- [ ] 🟡 **P5-3** Confidence thresholds + tuned on-device→Claude fallback.
- [ ] 🟢 **P5-4** Cross-engine reconciliation policy implemented.

## Phase 6 — Hardening & release
- [ ] 🟡 **P6-1** UX polish, error/offline/retake states.
- [ ] 🟢 **P6-2** Collection management + CSV/JSON export.
- [ ] 🟢 **P6-3** Optional pricing enrichment.
- [ ] 🔴 **P6-4** Privacy/security review + cost controls.
- [ ] 🟡 **P6-5** Backend deploy + monitoring.
- [ ] 🟡 **P6-6** Play Store prep (listing, signing, privacy policy).

---

## Backlog / ideas (unscheduled)
- [ ] 🟢 Multi-frame "best shot" capture for glare reduction.
- [ ] 🟢 Web demo UI for the backend extractor.
- [ ] 🟢 Batch scanning (multiple cards in one session).
- [ ] 🟢 iOS via Flutter/KMP (revisit after Android v1).
