# Scratchpad

**Project:** Sports Card Image Information Extractor
A running, informal log: decisions, ideas to try, open questions, and — importantly
— **what didn't work**, so we don't repeat dead ends. Newest notes near the top of
each section. Be honest and specific here; this is the project's memory.

---

## Decisions log
| Date | Decision | Rationale |
|---|---|---|
| 2026-06-03 | **Native Android (Kotlin)** for the on-device app first | Most direct access to CameraX, ML Kit, TFLite + GPU/NNAPI; cleanest path to good on-device ML; matches "Android for starters". iOS via Flutter/KMP later. |
| 2026-06-03 | **Backend proxy** for the Claude engine (FastAPI) | Keep API key server-side; enables prompt caching, schema validation, enrichment, model swapping, cost control. |
| 2026-06-03 | **Support graded + raw from v1** | User wants both; architecture routes per type. |
| 2026-06-03 | **One shared `CardInfo` contract** for both engines | Interchangeability, single eval harness, enables fallback. |
| 2026-06-03 | **Cert lookup is the graded shortcut** | PSA public API gives authoritative fields from the cert # → near-perfect graded extraction. |
| 2026-07-06 | **Schema v2 per detailed field spec** | Renamed `manufacturer`→`brand` (user vocabulary). Added `graded.description`, `autograph.{present,ink_color}`, `memorabilia.pieces[]` (per-piece analysis), `photo.jersey_number_candidates`, `attributes.serial_matches_jersey_number`. |
| 2026-07-06 | **`card_number` ≠ serial numbering** | `card_number` = position within the set; `attributes.serial_number/limit` = the 07/99 print-run copy number. Kept as separate fields + spelled out in all descriptions to avoid model confusion. |
| 2026-07-06 | **Memorabilia is an array of pieces** | A card can embed several pieces (patch + jersey + ball…). Each piece analyzed independently: type, real fabric?, colors + unique count, team-logo part, player-name/team-name letter parts, letters read. |
| 2026-07-06 | **Uncertainty policy for jersey number** | Best guess in `photo.jersey_number`; when unsure return ALL plausible readings in `jersey_number_candidates` (best first) instead of forcing one. May generalize to other fields later. |

### Interpretations to confirm with user (recorded, not blocking)
- "does it contain part of the team logo, player name, player team name" (patch
  context) → modeled as per-piece booleans `contains_team_logo_part`,
  `contains_player_name_part`, `contains_team_name_part` + `letters_visible` for
  the actual characters. Top-level `player_name`/`team` cover the card itself.
- "description (information from graded label)" → `graded.description` = the
  descriptive line(s); `graded.label_text` keeps the full raw label OCR.
- Signature ink: stored as `ink_color` string; "black = standard, other = rare"
  lives in field docs — rarity scoring itself belongs to a later enrichment phase.

---

## Ideas to try
- **Positional priors in prompt + parsers.** Year/brand/set/subset are usually at
  the bottom of the card front and on the graded label — tell Claude to look there
  first, and crop those regions for on-device OCR.
- **Rarity signals as derived enrichment.** Non-black ink, serial==jersey number,
  multi-color patches, logo/letter patches → compute a "rarity notes" summary from
  the extracted fields in the backend (not in the vision model).
- **Slab barcode → instant cert #.** Many slabs have a barcode/QR encoding the cert.
  ML Kit Barcode is trivial and far more reliable than OCR-ing the number. Try first.
- **Claude-as-labeler (distillation).** Use Engine A to auto-label captured images →
  ground truth to train the on-device TFLite models. Cheap data flywheel.
- **Prompt caching** of the (large, static) system prompt + JSON schema + few-shot
  examples. Should cut per-scan cost/latency substantially across many requests.
- **Confidence-gated fallback.** Run on-device first; only escalate to Claude when
  key fields (player/set/number) are low-confidence. Optimize cost vs accuracy.
- **Front + back fusion.** Back of card often has the cleanest card #, set, and
  copyright year. Combine both faces before extraction.
- **De-glare strategies for slabs**: tilt guidance in the capture UI, multi-frame
  best-shot selection, exposure bracketing, or recommend matte/polarized conditions.
- **Two-stage OCR**: detect/crop the label or text zone *first* (DL), then OCR the
  crop — usually far better than OCR on the whole image.
- **Reference-data subset on device** for offline normalization (top sets/players);
  full match happens server-side.
- **Grade-label parsing**: normalize "GEM-MT 10", "PR 1", BGS subgrades, etc., into
  structured fields with a small mapping table.

## Things to evaluate (open comparisons)
- **ML Kit Text Recognition v2 vs PaddleOCR (PP-OCR mobile)** on stylized/foil card
  fonts — accuracy vs app-size vs latency.
- **Detector**: YOLO-nano vs SSD-MobileNet for card/slab/region detection on device.
- **int8 quantization** accuracy hit vs size/latency win; per-device benchmarking.
- **Opus vs Sonnet vs Haiku** accuracy/cost per card difficulty tier.

## Open questions
- Within "both card types", which **sport** do we prioritize for the seed dataset?
  (baseball has the deepest catalogs; basketball is high-value.)
- **Offline reference-data budget**: how big can the bundled subset be?
- **Multi-frame capture** worth the UX cost for glare, or is single-shot enough?
- **Pricing scope**: include market value in v1 or defer to Phase 6?
- **Data licensing**: terms for TCDB/SportsCardsPro/Card Hedge data and card images.
- PSA free tier is **~100 calls/day** — is that enough for dev, or do we need a paid
  plan early? (Mitigate with aggressive caching.)

## What didn't work / dead ends
*(Record the approach, why it failed, and the evidence, so we don't retry it.)*
- **2026-07-06 — top-level `allOf` in a tool `input_schema`.** The Messages API
  rejects `oneOf`/`allOf`/`anyOf` at the top level of a tool input schema
  (400: `input_schema does not support oneOf, allOf, or anyOf at the top
  level`). Our graded-requires-`graded` conditional had to move out of the
  tool schema; it stays in the shared schema and is enforced server-side with
  a corrective retry. Nested `anyOf` (nullable fields) is fine.
- **2026-07-06 — strict structured outputs for CardInfo.** Not usable directly:
  `per_field_confidence` is an open map (`additionalProperties: {number}`),
  which strict structured outputs / strict tool use don't support
  (`additionalProperties` must be `false`). Forced tool use + server-side
  jsonschema validation + one corrective retry works well instead.

## Real-photo lessons (2026-07-06, from the owner's 15 card photos)
Folded into prompt v2 + schema; ground truth in `data/labels/` (11 cards):
- **One-touch magnetic holders ≠ graded.** Several cards sit in clear screw/
  magnetic cases with no grading label → must classify as raw. Added to prompt.
- **Slab backs show branding only.** A BGS slab photographed from behind gives
  company but no grade/cert → graded w/ nulls. Added to prompt.
- **BGS labels can carry a separate AUTOGRAPH grade** ("BECKETT 10 AUTOGRAPH")
  → new schema field `graded.autograph_grade`.
- **Serial stamps usually live on the BACK** (05/99, 16/25, 40/50, 4/4, 1/1 all
  on backs) → reinforced front+back capture; added to prompt.
- **Letterman patches exist**: an entire letter cut from a nameplate
  ("YELLOW JACKETS"), signed in SILVER ink on the patch → per-piece letter
  flags + non-black ink both exercised by real data.
- **Multi-piece relics are real**: one card embeds jersey + football + jersey
  (3 pieces) — the pieces[] array design earns its keep.
- **Same card number, different physical cards**: two NT #107 CJ copies (plain
  jersey vs 3-color patch; one raw, one later PSA-graded) — card_number alone
  is not identity.
- **Inputs include app screenshots** (UI chrome) and rotated photos → prompt
  now says to ignore chrome and read rotated text.

## Live results log
- **2026-07-06 — REAL-PHOTO EVAL (11 cards): ~91% strict field accuracy.**
  Details in `eval/results/real_seed/SUMMARY.md`. Highlights: one-touch→raw
  classification 11/11 (the trap we prompted for), certs/grades/serials/players
  essentially perfect, silver-ink + blue-ink autos detected, 3-piece relic card
  scored 100%. Mismatches dominated by label-text word order (eval artifact)
  and set-name canonicalization (evidence FOR resuming P2-4/P2-5). One genuinely
  hard card (letterman patch: college-vs-pro team ambiguity, occluded jersey #).
- **2026-07-06 — Phase 1 smoke test (synthetic graded patch-auto card, opus).**
  All priority fields extracted correctly, incl. `serial_matches_jersey_number`
  (23/99 + jersey 23), blue ink, 3-color patch with team-logo part, cert #,
  label description, brand/set/subset from the bottom-of-front line + label.
  Latency ~12-13s/scan. Cache: run 1 wrote 8,496 prefix tokens; run 2 read all
  8,496 from cache → cost ~$0.099 → ~$0.050 (-49%). Validation retry never
  triggered (attempts=1). Caveat: synthetic render, not a real photo — real-photo
  validation is P1-10.

## Handy references (to revisit during build)
- PSA public API: `https://www.psacard.com/publicapi/documentation` (OAuth2).
- Claude vision docs: `https://platform.claude.com/docs/en/build-with-claude/vision`.
- ML Kit Text Recognition v2 (Android, on-device, free).
- PaddleOCR (PP-OCR mobile; PaddleOCR-VL released Jan 2026).
- Card data: TCDB, SportsCardsPro, Card Hedge.
