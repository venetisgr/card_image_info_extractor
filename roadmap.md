# Roadmap

**Project:** Sports Card Image Information Extractor
**Last updated:** 2026-06-03
**Companion docs:** `architecture_components.md` (the "what"), `pending_tasks.md`
(the "now"), `scratchpad.md` (the "why / what we tried").

This roadmap is **phased**. Both engines (Claude + on-device) and both card types
(graded + raw) are in scope from v1, but the **build order** front-loads fast value:
get the Claude engine extracting first, add enrichment, then bring the on-device
engine up to parity.

## Phase summary

| Phase | Theme | Primary outcome |
|---|---|---|
| 0 | Foundations | Schema, dataset, scaffolding, CI |
| 1 | Claude vertical slice | `POST /extract` returns valid `CardInfo` |
| 2 | Enrichment & verification | Cert lookup (graded) + checklist match (raw) |
| 3 | On-device baseline | Android app extracts via ML Kit OCR |
| 4 | On-device DL models | TFLite detectors/classifiers; better accuracy |
| 5 | Eval, reconciliation, fallback | Measured accuracy; on-device→cloud fallback |
| 6 | Hardening & release | Offline, UX, deploy, Play Store, cost controls |

---

## Phase 0 — Foundations

**Goal:** A skeleton both engines can build on, plus the shared contract and a seed
dataset.

**Key design**
- Define the **`CardInfo` JSON Schema** in `/shared`; generate Pydantic + Kotlin
  types from it (single source of truth).
- **Seed dataset**: ~100–200 images spanning graded + raw, multiple sports, brands,
  eras, and conditions (incl. glare, angles). Capture front + back.
- **Labeling guidelines** + a label format aligned to `CardInfo`.
- Repo scaffolding (`backend`, `android`, `shared`, `ml`, `data`, `eval`), linting,
  test runners, GitHub Actions CI, secrets strategy (server-side only).

**Components touched:** `/shared`, `/data`, CI.

**Exit criteria:** schema published + codegen working; seed dataset labeled; CI
green on empty projects.

---

## Phase 1 — Claude API vertical slice

**Goal:** Fastest path to real extraction for **both** card types.

**Key design**
- FastAPI `POST /extract` (multipart image[s]) → image pre-resize (≤2576 px long
  edge) → Claude vision with **structured output** (tool/JSON-schema) → validate →
  return `CardInfo`.
- **Prompt caching** of the static system prompt + schema + few-shot examples.
- **Model tiering** flag (Opus/Sonnet/Haiku); default per-difficulty.
- Accept **front + back**; one corrective retry on schema-validation failure.
- A thin **CLI / notebook** wrapper for quick local runs.

**Components touched:** `/backend`, `/shared`.

**Exit criteria:** end-to-end JSON for graded and raw sample images; validates
against schema; basic latency/cost logged.

---

## Phase 2 — Enrichment & verification

**Goal:** Turn extracted text into **verified, normalized** data.

**Key design**
- **Graded:** extract cert # (from Claude output or, later, barcode) → call **PSA
  public API**; map response → `CardInfo`; override low-confidence fields. Add
  third-party verifier adapters (TCGAPIs/CardGrade) for BGS/CGC/SGC/TAG.
- **Raw:** fuzzy-match (player + year + brand + number) against a **checklist DB**
  (TCDB / SportsCardsPro import) to canonicalize set/number and fill gaps.
- **Normalization tables** for manufacturer/set aliases; grade-label normalization.
- **Caching** for all external calls (respect PSA's ~100/day free limit).

**Components touched:** `/backend` (enrichment, reference DB), Postgres.

**Exit criteria:** graded cards verified via cert lookup; raw cards matched to
checklist entries with measurable fill-rate improvement.

---

## Phase 3 — On-device baseline (Android)

**Goal:** A working Android app that extracts on-device with OCR + rules, using the
backend only for enrichment/fallback.

**Key design**
- **CameraX** capture (front/back) + gallery import; capture guidance.
- **Pre-processing** with OpenCV (quad detect, perspective warp, orientation).
- **ML Kit Text Recognition v2** for OCR; **ML Kit Barcode** for slab cert #.
- **Rules-based parser** (Kotlin) + **bundled reference subset** → `CardInfo`.
- **Room** storage; **Retrofit** client for enrichment + **Claude fallback**.
- **Mode toggle** (on-device vs cloud) for side-by-side comparison.

**Components touched:** `/android`, `/backend` (client endpoints).

**Exit criteria:** install-and-scan produces `CardInfo` offline for clear cards;
graded slabs resolved via barcode→cert lookup when online.

---

## Phase 4 — On-device DL models

**Goal:** Replace/augment heuristics with small on-device models for accuracy.

**Key design**
- **Dataset prep & labeling** (use Engine A as auto-labeler + human review).
- Train + convert to **TFLite (int8)**:
  - graded-vs-raw classifier (MobileNetV3),
  - card/slab + region detector (YOLO-nano / SSD-MobileNet) to target OCR,
  - optional brand/logo classifier and field-mapping model.
- Integrate **GPU/NNAPI** delegates; benchmark accuracy ↔ latency ↔ size on a range
  of devices; quantize and prune to fit budget.

**Components touched:** `/ml`, `/android`, `/data`.

**Exit criteria:** detector improves OCR targeting and field accuracy vs Phase 3
baseline; models meet size/latency budget on mid-range hardware.

---

## Phase 5 — Evaluation, reconciliation & fallback

**Goal:** Know exactly how good each engine is, and combine them intelligently.

**Key design**
- **Eval harness** (`/eval`): labeled test set; scorer for **per-field accuracy,
  latency, cost**; A/B Claude vs on-device; regression tracking in CI.
- **Confidence thresholds** per field; tune the **on-device→Claude fallback** to
  hit a target accuracy at minimum cost.
- **Cross-engine reconciliation** policy (verified > Claude > on-device).

**Components touched:** `/eval`, `/backend`, `/android`.

**Exit criteria:** published accuracy numbers per engine and per card type; fallback
policy demonstrably improves accuracy/cost tradeoff.

---

## Phase 6 — Hardening & release

**Goal:** A shippable Android app + a deployed backend.

**Key design**
- UX polish, robust error/empty/offline states, retake flow.
- **Collection management** + CSV/JSON export; optional **pricing enrichment**
  (SportsCardsPro / Card Hedge).
- **Privacy/security review** (image handling, key management, PII), cost controls
  + rate limiting, observability/alerting.
- Backend **deployment** (containerized) + monitoring; **Play Store** prep
  (listing, signing, privacy policy).

**Components touched:** all.

**Exit criteria:** internal/beta release on Play Store; backend deployed with
monitoring and cost guardrails.

---

## Milestones (north stars)

- **M1:** Claude engine returns valid `CardInfo` for graded + raw (end of P1).
- **M2:** Graded cards verified via cert API; raw matched to checklists (end of P2).
- **M3:** Android app extracts on-device (end of P3).
- **M4:** On-device models beat the heuristic baseline (end of P4).
- **M5:** Measured accuracy + working fallback (end of P5).
- **M6:** Beta release (end of P6).

*Effort/sequence note:* Phases 1–2 are the quickest wins. Phases 3–4 are the bulk of
the engineering. Keep the eval harness (P5) running continuously from P1 onward in a
lightweight form so every phase is measured.
