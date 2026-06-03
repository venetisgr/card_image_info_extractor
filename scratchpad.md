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

---

## Ideas to try
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
*(empty — fill this in as we learn. Record the approach, why it failed, and the
evidence, so we don't retry it.)*
- …

## Handy references (to revisit during build)
- PSA public API: `https://www.psacard.com/publicapi/documentation` (OAuth2).
- Claude vision docs: `https://platform.claude.com/docs/en/build-with-claude/vision`.
- ML Kit Text Recognition v2 (Android, on-device, free).
- PaddleOCR (PP-OCR mobile; PaddleOCR-VL released Jan 2026).
- Card data: TCDB, SportsCardsPro, Card Hedge.
