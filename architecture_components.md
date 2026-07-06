# Architecture & Components

**Project:** Sports Card Image Information Extractor
**Last updated:** 2026-07-06
**Status:** Design / pre-implementation

---

## 1. Purpose

Extract **structured information** from photographs of **sports cards** — both
**graded** (encased/slabbed by PSA, BGS, SGC, CGC, TAG, …) and **raw** (loose,
ungraded) — and return a clean, machine-readable record.

We build **two interchangeable engines**:

- **Engine A — Claude API**: a cloud vision pipeline using the Claude API behind a
  backend proxy. Optimized for accuracy and breadth.
- **Engine B — On-device**: a phone-native pipeline (Android first) using
  traditional OCR + on-device deep learning. Optimized for offline use, privacy,
  latency, and zero per-scan cost.

### Goals
- Same structured output from either engine (one shared contract).
- Handle graded **and** raw cards from v1.
- Engine B runs fully offline on a mid-range Android phone.
- Engine A is the accuracy ceiling and the data source that bootstraps Engine B.

### Non-goals (for now)
- iOS app (keep the design portable; revisit Flutter/KMP later).
- Full marketplace/pricing & collection-valuation features (later phase).
- Non-sports TCG (Pokémon/MTG/Yu-Gi-Oh) — possible future extension.

---

## 2. Guiding principles / key decisions

1. **One shared contract.** Both engines emit the same `CardInfo` JSON. This makes
   them swappable, lets a single eval harness score both, and enables fallback.
2. **Backend proxy for Claude.** Clients never hold the Anthropic key. The backend
   centralizes prompt caching, schema validation, retries, and enrichment.
3. **Detect-then-extract.** Classify graded vs raw early and branch; the two card
   types need different region logic.
4. **Cert lookup is the graded accuracy shortcut.** Read the cert number (OCR or the
   slab's barcode) → call the PSA public API / third-party verifier → authoritative
   fields. This makes graded extraction near-perfect.
5. **Confidence-driven fallback.** Engine B runs first on-device; if per-field
   confidence is low, optionally escalate that scan to Engine A. Saves cost/latency.
6. **Offline-first on device.** Bundle a reference-data subset; the network is an
   enhancement, not a requirement, for Engine B.
7. **Claude-as-labeler.** Use Engine A to auto-label captured images, producing the
   ground-truth dataset that trains Engine B's on-device models (distillation).

---

## 3. High-level architecture

```
                         ┌──────────────────────────────┐
                         │           CAPTURE             │
                         │  camera / gallery (front+back)│
                         └───────────────┬──────────────┘
                                         │ image(s)
                         ┌───────────────▼──────────────┐
                         │        PRE-PROCESSING         │
                         │ de-glare · perspective crop · │
                         │ orientation · resize/enhance  │
                         └───────────────┬──────────────┘
                                         │
                         ┌───────────────▼──────────────┐
                         │   ROUTER: graded vs raw       │
                         └───────┬───────────────┬───────┘
                  graded slab    │               │   raw card
                ┌────────────────▼───┐     ┌─────▼─────────────────┐
                │ label + barcode/   │     │ card text zones:      │
                │ cert region        │     │ name/team/number/logo │
                └─────────┬──────────┘     └─────────┬─────────────┘
                          │                          │
        ┌─────────────────▼──────────────────────────▼─────────────────┐
        │                       EXTRACTION                              │
        │   Engine A: Claude vision (backend)   OR                      │
        │   Engine B: ML Kit OCR + TFLite models (on device)           │
        └─────────────────────────────┬───────────────────────────────┘
                                       │ raw fields + confidence
                         ┌─────────────▼─────────────┐
                         │   VERIFY / ENRICH         │
                         │ graded → PSA cert API     │
                         │ raw → checklist match     │
                         │       (TCDB/SportsCardsPro)│
                         └─────────────┬─────────────┘
                                       │
                         ┌─────────────▼─────────────┐
                         │  NORMALIZE & RECONCILE    │
                         │ canonical brand/set names │
                         │ cross-engine merge        │
                         └─────────────┬─────────────┘
                                       │  CardInfo
                         ┌─────────────▼─────────────┐
                         │  OUTPUT / STORE / EXPORT  │
                         │ Room (device) · DB (server)│
                         └───────────────────────────┘
```

---

## 4. The shared contract: `CardInfo`

The single source of truth lives in `/shared` as a **JSON Schema**, from which we
generate **Pydantic** models (backend) and **Kotlin** data classes (Android).

### Fields

| Field | Type | Notes |
|---|---|---|
| `card_type` | enum | `graded` \| `raw` |
| `sport` | enum? | baseball, basketball, football, hockey, soccer, other |
| `player_name` | string? | subject / athlete |
| `year` | string? | e.g. `2003` or `2003-04` |
| `brand` | string? | Topps, Panini, Upper Deck, Bowman, Fleer, … (normalized) |
| `set` | string? | product/set name (normalized) |
| `subset` | string? | insert / subset name |
| `parallel` | string? | parallel / variation (e.g. "Silver Prizm") |
| `card_number` | string? | the card's number **within the set** (e.g. `#250`) — NOT the 5/30 serial |
| `team` | string? | team / franchise |
| `language` | string? | ISO code if detectable |
| `attributes.rookie` | bool | RC flag |
| `attributes.serial_number` | string? | limited card `07/99` → this copy's number (`07`) |
| `attributes.serial_limit` | string? | limited card `07/99` → total print run (`99`) |
| `attributes.serial_matches_jersey_number` | bool? | serial == player's jersey number (e.g. `07/99`, player wears #7) → rarer |
| `photo.jersey_colors` | array? | colors of the jersey in the player's picture |
| `photo.jersey_number` | string? | best-guess number on the jersey in the picture (e.g. `23`) |
| `photo.jersey_number_candidates` | array? | when unsure: all plausible jersey numbers, best first |
| `autograph.present` | bool? | autograph yes/no |
| `autograph.ink_color` | string? | signature ink color — black is standard, non-black is rarer |
| `memorabilia.present` | bool? | embedded memorabilia yes/no |
| `memorabilia.pieces[]` | array | one entry per embedded piece — can be more than one |
| `pieces[].type` | enum? | patch, jersey, ball, floor, shoe, other |
| `pieces[].is_fabric` | bool? | actual piece of fabric/material vs printed facsimile |
| `pieces[].colors` / `unique_color_count` | array? / int? | distinct colors in the piece (more colors ≈ rarer patch) |
| `pieces[].contains_team_logo_part` | bool? | piece includes part of the team logo |
| `pieces[].contains_player_name_part` / `contains_team_name_part` | bool? | piece includes nameplate/team lettering |
| `pieces[].letters_visible` | string? | any letters readable in the piece (e.g. `AME`) |
| `graded.grading_company` | enum? | PSA, BGS (Beckett), SGC, CGC, TAG, … |
| `graded.grade` | number? | numeric grade (e.g. `10`, `9.5`) |
| `graded.grade_label` | string? | e.g. `GEM-MT 10` |
| `graded.description` | string? | the descriptive info line(s) printed on the label |
| `graded.subgrades` | object? | `{centering, corners, edges, surface}` (BGS) |
| `graded.autograph_grade` | number? | separate autograph grade on some labels (e.g. BGS "10 AUTOGRAPH") |
| `graded.cert_number` | string? | slab cert / serial |
| `graded.label_text` | string? | full raw OCR of the label |
| `per_field_confidence` | object | 0–1 per field |
| `provenance.engine` | enum | `claude` \| `on_device` |
| `provenance.model_version` | string | model id / app build |
| `provenance.timestamp` | string | ISO-8601 |
| `provenance.source_images` | array | refs/hashes of input images |
| `raw_output` | object | raw OCR text or model JSON (debug) |

### Extraction hints (encoded into prompts/parsers)
- **Year, brand, set and subset** are most often printed at the **bottom of the
  card front**, and on the **label** if graded — prioritize those regions.
- **Front + back are always both provided**; the back often carries the card
  number, set details, and stats.
- Don't confuse `card_number` (position within the set) with the serial numbering
  (`attributes.serial_number`/`serial_limit`, the "07/99" print run).
- If the jersey number in the photo is uncertain, return every plausible reading in
  `photo.jersey_number_candidates` rather than guessing one.

### Example — graded relic/auto showcase (exercises the priority fields)
```json
{
  "card_type": "graded",
  "sport": "basketball",
  "player_name": "LeBron James",
  "year": "2003-04",
  "brand": "Upper Deck",
  "set": "Exquisite Collection",
  "subset": "Rookie Patch Autograph",
  "card_number": "78",
  "attributes": { "rookie": true, "serial_number": "23", "serial_limit": "99",
                  "serial_matches_jersey_number": true },
  "photo": { "jersey_colors": ["wine", "gold", "white"], "jersey_number": "23",
             "jersey_number_candidates": null },
  "autograph": { "present": true, "ink_color": "blue" },
  "memorabilia": {
    "present": true,
    "pieces": [
      { "type": "patch", "is_fabric": true, "colors": ["wine", "white", "gold"],
        "unique_color_count": 3, "contains_team_logo_part": true,
        "contains_player_name_part": false, "contains_team_name_part": false,
        "letters_visible": null },
      { "type": "jersey", "is_fabric": true, "colors": ["white"],
        "unique_color_count": 1, "contains_team_logo_part": false,
        "contains_player_name_part": true, "contains_team_name_part": false,
        "letters_visible": "AME" }
    ]
  },
  "graded": { "grading_company": "BGS", "grade": 9.5, "grade_label": "GEM MINT 9.5",
              "description": "2003-04 EXQUISITE COLLECTION #78 LEBRON JAMES ROOKIE PATCH AUTOGRAPH 23/99",
              "cert_number": "0012345678" }
}
```

> Full, schema-valid records (graded, graded-relic, raw) live in
> [`shared/examples/`](shared/examples/); a human/prompt-facing **placeholder
> template** showing every field lives at
> [`shared/templates/card_info_placeholder.json`](shared/templates/card_info_placeholder.json);
> the binding contract is
> [`shared/schema/card_info.schema.json`](shared/schema/card_info.schema.json).

---

## 5. Shared processing pipeline

1. **Capture / ingest** — camera or gallery; support **front + back** (back often
   holds card #, set, stats); optionally multiple frames for best-shot selection.
2. **Pre-processing**
   - **De-glare**: slabs are highly reflective → exposure/highlight handling,
     multi-frame or polarized capture guidance.
   - **Detect & rectify**: find the card/slab quadrilateral, perspective-correct.
   - **Orientation**: auto-rotate; handle portrait/landscape cards.
   - **Resize/enhance**: downscale to model resolution; contrast/denoise for OCR.
3. **Router** — graded-vs-raw classifier. Graded slabs have a distinct label strip;
   raw cards do not. Also detect the **label region** (graded) vs **text zones**.
4. **Region detection**
   - Graded: isolate the **label** (company, grade, descriptive line, cert #) and
     the **barcode/QR** if present.
   - Raw: locate name, team, number, brand/logo zones (front) + copyright/number
     block (back).
5. **Extraction** — Engine A or B (see §6/§7) → raw fields + per-field confidence.
6. **Verify / enrich**
   - Graded: cert # → **PSA public API** (or TCGAPIs/CardGrade for BGS/CGC/SGC) →
     authoritative fields; reconcile and override low-confidence OCR.
   - Raw: fuzzy-match against **checklist DB** (TCDB / SportsCardsPro) to normalize
     names and fill gaps (e.g., resolve set + card #).
7. **Normalize & reconcile** — canonicalize brand/set strings via lookup
   tables; normalize grade labels; if both engines ran, merge by confidence.
8. **Confidence & fallback** — if Engine B confidence < threshold, optionally
   escalate to Engine A (backend). Record both for eval.
9. **Output / store / export** — return `CardInfo`; persist (Room on device,
   Postgres on server); optional CSV/JSON export; optional pricing enrichment.

---

## 6. Engine A — Claude API (cloud, behind backend proxy)

**Topology:** `client/CLI → FastAPI backend → Claude API`. The key never leaves the
server.

**Components**
- **API gateway** (FastAPI): auth, rate limiting, request/response logging.
- **Image service**: validate, EXIF-strip, resize to model resolution
  (≤2576 px long edge), optional pre-crop; store original + processed.
- **Claude extraction service** (Anthropic SDK):
  - **Structured output** via tool use / JSON-schema-constrained response → returns
    `CardInfo` directly.
  - **Prompt caching** on the (large, static) system prompt + schema + few-shot
    examples → big cost/latency savings across requests.
  - **Model tiering**: `claude-opus-4-8` for hard/ambiguous cards;
    `claude-sonnet-4-6` / `claude-haiku-4-5` for easy/cheap scans.
  - **Validation + retry**: validate against JSON Schema; one corrective re-ask on
    failure.
  - Send **front + back** together when available.
- **Enrichment service**: PSA cert API; checklist match (see §8).
- **Persistence**: Postgres (records), object storage (images).

**Why backend (not direct from app):** key security, prompt caching, central
enrichment + normalization, model swapping, and cost controls/observability.

---

## 7. Engine B — On-device (Android / Kotlin)

**Components**
- **Capture**: CameraX preview + capture; gallery import; front/back flow; capture
  guidance (fill frame, reduce glare).
- **Pre-processing**: OpenCV-Android — quadrilateral detection, perspective warp,
  grayscale/threshold for OCR; orientation fix.
- **OCR**: **ML Kit Text Recognition v2** (free, offline) as the baseline; evaluate
  **PaddleOCR (PP-OCR mobile)** for higher accuracy on stylized card fonts.
- **Barcode/cert**: **ML Kit Barcode Scanning** to read slab barcodes/QR → cert #.
- **On-device DL (TFLite)** with GPU/NNAPI delegate:
  - **Graded-vs-raw classifier** (lightweight CNN, e.g. MobileNetV3).
  - **Card/slab + region detector** (e.g. YOLO-nano / SSD-MobileNet) to crop label
    and text zones before OCR.
  - **(Optional) brand/logo classifier** and **layout/field model** to map OCR
    tokens → fields.
- **Field parser/normalizer** (Kotlin): rules + fuzzy matching over OCR tokens and
  a **bundled reference subset** (top sets/players) for offline normalization.
- **Local store**: **Room** DB for scans/collection; image cache.
- **Backend client** (Retrofit): enrichment lookups + **Claude fallback** when
  confidence is low or the user opts in.
- **Mode toggle**: "On-device" vs "Cloud (Claude)" so users/devs can compare.

**Constraints to respect:** model size (app + assets budget), inference latency on
mid-range devices, battery, and memory. Quantize models (int8) and benchmark.

---

## 8. Shared & cross-cutting components

- **Canonical schema** (`/shared`): JSON Schema → Pydantic + Kotlin codegen.
- **Enrichment / verification**
  - PSA **public API** (OAuth2; ~100 free calls/day) for graded cert lookup.
  - Third-party verifiers (TCGAPIs, CardGrade.io) for BGS/CGC/SGC/TAG.
  - Checklist/catalog: TCDB, SportsCardsPro, Card Hedge (also pricing later).
  - **Caching layer** in front of all external APIs (respect rate limits).
- **Reference DB** (Postgres): brands, sets, normalization aliases, cached
  cert/checklist results.
- **Evaluation harness** (`/eval`): labeled dataset + scorer computing **per-field
  accuracy, latency, cost** for both engines; A/B + regression tracking.
- **Telemetry**: accuracy, latency, cost-per-scan, fallback rate.
- **Config & secrets**: server-side secret manager; no secrets in the app.

---

## 9. Graded vs raw handling (summary)

| Aspect | Graded (slab) | Raw (loose) |
|---|---|---|
| Distinctive cue | label strip + (often) barcode/cert | none — read the card itself |
| Easiest signal | **cert # → authoritative API lookup** | OCR of name/number + checklist match |
| Main challenge | glare/reflection off the case | layout variety, stylized fonts, foil |
| Confidence | very high (verified) | medium → boosted by checklist match |
| Strategy | OCR/scan label → verify → done | detect zones → OCR → match → normalize |

---

## 10. Confidence, reconciliation & fallback

- Every field carries a confidence (0–1). Engine B sets thresholds per field.
- **Fallback**: if key fields (player, set, number) fall below threshold on device,
  optionally send the image to Engine A.
- **Reconciliation**: when both engines (or an engine + an API lookup) produce a
  field, prefer **verified API > Claude > on-device**, weighted by confidence; keep
  all sources in `raw_output` for audit.

---

## 11. Proposed repo structure

```
card_image_info_extractor/
├── shared/        # CardInfo JSON Schema + codegen (Pydantic, Kotlin)
├── backend/       # FastAPI: Claude extraction, enrichment, normalization, eval API
├── android/       # Kotlin app: CameraX, ML Kit, TFLite, Room, Retrofit
├── ml/            # training/conversion for on-device TFLite models
├── data/          # sample images, labels, reference tables (licensing-aware)
├── eval/          # eval harness, datasets, metrics, reports
└── docs/          # architecture_components.md, roadmap.md, … (these docs)
```
*(Docs currently live at repo root to match the initial naming; can move to `docs/`.)*

---

## 12. Tech stack summary

| Layer | Choice |
|---|---|
| Cloud extraction | Claude API (`claude-opus-4-8` / Sonnet / Haiku) via Anthropic SDK |
| Backend | Python + FastAPI + Pydantic + httpx; Postgres; object storage |
| Android app | Kotlin, CameraX, ML Kit (Text v2 + Barcode), TFLite, Room, Retrofit, OpenCV |
| On-device OCR | ML Kit Text Recognition v2 (baseline); PaddleOCR mobile (candidate) |
| Model training | PyTorch / Ultralytics YOLO, PaddleOCR; TFLite converter + int8 quant |
| Enrichment | PSA public API; TCDB / SportsCardsPro (+ TCGAPIs/CardGrade) |
| Eval | Python (pandas) harness in `/eval` |

---

## 13. Open architectural questions

Tracked in `scratchpad.md` — includes: which sports to prioritize within "both",
offline reference-data size budget, multi-frame capture, and pricing scope.
