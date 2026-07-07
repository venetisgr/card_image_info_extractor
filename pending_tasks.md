# Pending Tasks

**Project:** Sports Card Image Information Extractor
**Last updated:** 2026-07-06
**See also:** `roadmap.md` (phases), `completed_tasks.md` (done), `scratchpad.md`.

## Conventions
- `- [ ]` open · `- [~]` in progress · move to `completed_tasks.md` when done.
- Each task: **what** — *acceptance criteria*.
- IDs are `P<phase>-<n>`. Priority: 🔴 high · 🟡 med · 🟢 low.

---

## 🔜 In progress
- [~] 🟡 **P0-4** Seed dataset — collect 100–200 graded+raw images (front+back) and
  label them. *Needs real card images to proceed.*

---

## Phase 0 — Foundations
- [x] 🔴 **P0-1** Define `CardInfo` **JSON Schema** in `/shared` — *done (now v2);
  covers graded?/company/cert/label-description, sport/year/brand/set/subset,
  player, card # in set, autograph + ink color, photo jersey colors/number (+
  candidates), memorabilia pieces (fabric/colors/logo/letters), serial 07/99 +
  jersey-match flag. → completed_tasks.md*
- [x] 🔴 **P0-2** Codegen from schema → **Pydantic** + **Kotlin** types — *done via
  `shared/codegen/generate.sh`; regenerated for schema v2. → completed_tasks.md*
- [x] 🟡 **P0-9** JSON **placeholder template** for the output shape — *done:
  `shared/templates/card_info_placeholder.json`; kept in sync with the schema by a
  test. → completed_tasks.md*
- [x] 🔴 **P0-3** Scaffold repo dirs + minimal build files + tests — *done; backend
  `pytest` green (schema⇄examples⇄model). → completed_tasks.md*
- [ ] 🟡 **P0-4** **Seed dataset**: collect 100–200 images (graded + raw; baseball,
  basketball, football, hockey, soccer; varied eras/conditions; front+back) —
  *images stored in `/data` with a manifest.*
- [ ] 🟡 **P0-5** Labeling guidelines + label format aligned to `CardInfo` — *a
  labeler can produce ground-truth JSON unambiguously.*
- [ ] 🟡 **P0-6** Label the seed dataset — *ground-truth JSON for every seed image.*
- [ ] 🟢 **P0-7** CI (GitHub Actions): lint + test for backend & android — *CI green.*
- [ ] 🔴 **P0-8** Secrets strategy doc (server-side only; no keys in app) — *written
  and referenced in `resources.md`.*

## Phase 1 — Claude API vertical slice ✅ (done 2026-07-06 → completed_tasks.md)
- [x] 🔴 **P1-1** FastAPI `POST /extract` — *done; multipart front(+back)+model.*
- [x] 🔴 **P1-2** Image pre-processing — *done; EXIF fix/strip, RGB, ≤2576 px, JPEG.*
- [x] 🔴 **P1-3** Claude extraction via forced tool use → `CardInfo` — *done; live
  run extracts all priority fields correctly on a graded patch-auto sample.*
- [x] 🔴 **P1-4** Prompt caching — *done; measured live: 8,496 tokens cached,
  second call read 100% from cache, ~49% cost drop.*
- [x] 🟡 **P1-5** Schema validation + one corrective retry — *done; validated
  server-side incl. the graded-conditional; errored tool_result retry.*
- [x] 🟡 **P1-6** Front+back handling — *done; both images in one user turn.*
- [x] 🟡 **P1-7** Model tiering — *done; opus/sonnet/haiku aliases or any model id.*
- [x] 🟢 **P1-8** CLI wrapper — *done; `python -m app.cli front.jpg back.jpg`.*
- [x] 🔴 **P1-9** Prompt encodes field spec + hints — *done; placeholder template,
  positional priors, card#-vs-serial, jersey candidates, per-piece memorabilia,
  ink color; worked example included.*
- [x] 🟡 **P1-10** Test on **real card photos** — *done 2026-07-06: 11 cards,
  **~91% strict field accuracy**, all priority fields ~perfect (see
  `eval/results/real_seed/SUMMARY.md`). → completed_tasks.md*
- [x] 🟢 **P1-11** Eval follow-ups — *done 2026-07-06: fuzzy scoring for
  transcription fields + color equivalences in compare.py; image-visible GT
  convention documented + 4 labels corrected; prompt v3/v3.1 nudges. Result:
  **98.6% (278/282), 8/11 cards perfect** — `eval/results/real_seed_v2/SUMMARY.md`.
  → completed_tasks.md*
- [ ] 🟢 **P1-12** Variance tail — *consider self-consistency (second pass /
  dual-model vote) on low-confidence fields; strongest fix is live PSA
  verification (token pending).*

## Phase 2 — Enrichment & verification
- [x] 🔴 **P2-1** PSA **public API** client — *done: bearer-token client with
  on-disk response cache (free tier ~100/day), clean error taxonomy.*
- [x] 🔴 **P2-2** Wire graded path: cert # → lookup → reconcile/override — *done:
  verified-beats-extracted policy, confidence 1.0 on verified fields, PSA record
  kept in `raw_output.verification`; auto-runs in `/extract` (opt-out) + CLI +
  standalone `GET /verify/psa/{cert}`. Mock-tested (18 tests).*
- [~] 🔴 **P2-2b** LIVE PSA verification — *blocked on a token: generate at
  psacard.com/publicapi and add `PSA_API_TOKEN=...` to `backend/.env`; then the
  owner's real certs (26987167, 111281730, 111281750, 20505941) are test cases.*
- [ ] 🟡 **P2-3** Third-party verifier adapters (BGS/CGC/SGC/TAG) — *at least one
  non-PSA company resolved.*
- [ ] ⏸️ **P2-4** Import **checklist DB** (TCDB / SportsCardsPro) — *ON HOLD per
  user (2026-07-06) — REMIND USER LATER before starting.*
- [ ] ⏸️ **P2-5** Raw fuzzy-match + fill — *ON HOLD per user (2026-07-06),
  together with P2-4 — REMIND USER LATER.*
- [x] 🟡 **P2-6** Brand/set **normalization tables** — *done 2026-07-06:
  `services/normalize.py` (brand/set/subset/team aliases + language-qualifier
  extraction), wired post-enrichment in API + CLI; Android reference aligned.
  → completed_tasks.md*

## Phase 3 — On-device baseline (Android)
- [x] 🔴 **P3-1** Android project + capture (front/back) + gallery — *done via the
  system camera (permission-free) + gallery picker; Gradle project with SDK-
  conditional `:app` and pure-JVM `:core`. → completed_tasks.md*
- [ ] 🟢 **P3-1b** In-app **CameraX** preview with card-framing guidance —
  *follow-up; deps already in the version catalog.*
- [ ] 🟡 **P3-2** OpenCV pre-processing (quad detect, perspective warp, orient) —
  *deferred; ML Kit tolerates moderate skew.*
- [x] 🔴 **P3-3** **ML Kit Text Recognition v2** → OCR text — *done (`vision/OcrEngine`).*
- [x] 🔴 **P3-4** **ML Kit Barcode** → slab cert # — *done (`vision/BarcodeEngine`;
  barcode payload outranks OCR digits for cert).*
- [x] 🔴 **P3-5** Rules parser + bundled reference subset → `CardInfo` — *done and
  **unit-tested on real-card fixtures (7 tests green)**: graded/raw, grades +
  subgrades + autograph grade, cert, serial w/ COA-date rejection, year/brand/
  set (set→brand precedence), card #, player + team heuristics.*
- [x] 🟡 **P3-6** **Room** storage + scan history UI — *done.*
- [x] 🟡 **P3-7** **Retrofit** client → backend `/extract` (Claude + PSA) — *done
  as the cloud mode; confidence-driven AUTO-fallback remains P5-3.*
- [x] 🟢 **P3-8** On-device vs cloud **mode toggle** — *done (segmented control).*
- [ ] 🔴 **P3-9** Build `:app` in Android Studio + run on a device; fix whatever
  the first real build/run surfaces — *this container has no Android SDK, so the
  app module compiles unverified.*

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
