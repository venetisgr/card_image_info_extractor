# Resources

**Project:** Sports Card Image Information Extractor
**Last updated:** 2026-06-03

Everything we'll need to build both engines: people, accounts/APIs, libraries, data,
hardware, infrastructure, and an estimated cost model. Links are grounded in the
research done on 2026-06-03 (see "Sources").

---

## 1. People / skills
| Role | Why |
|---|---|
| Android / Kotlin developer | CameraX, ML Kit, TFLite, Room — the on-device app. |
| Python / backend developer | FastAPI proxy, Claude integration, enrichment, DB. |
| ML engineer | Train/convert/quantize on-device models; eval harness. |
| Data labeler (part-time) | Ground-truth labels for dataset + eval (can be us + Claude-assisted). |
| (Optional) UX/product | Capture flow, results UI, Play Store listing. |

*A small team — even one full-stack dev + occasional ML help — can do v1; the
phasing in `roadmap.md` lets one person make steady progress.*

---

## 2. Accounts & external APIs
| Service | Use | Notes / limits |
|---|---|---|
| **Anthropic (Claude API)** | Engine A vision extraction | Models: `claude-opus-4-8` (default), `claude-sonnet-5`, `claude-haiku-4-5`. Vision: high-res up to 2576 px long edge. Key lives in `backend/.env` (git-ignored). |
| **PSA Public API** | Graded cert verification | OAuth2 (password grant); **~100 calls/day free**, paid tiers higher. Authoritative graded fields. |
| **TCGAPIs / CardGrade.io** | BGS/CGC/SGC/TAG verify | Third-party cert lookup beyond PSA; small free quotas. |
| **TCDB** | Checklists / catalog | Set/player checklists for raw-card matching. |
| **SportsCardsPro** | Prices + CSV catalog | Price API + CSV downloads per set. |
| **Card Hedge API** | Pricing/market (later) | Real-time prices from eBay/Fanatics/Heritage. |
| **Google Play Console** | Android release | One-time developer registration fee. |
| **Cloud provider** | Backend + DB + storage | Any (Fly.io/Render/AWS/GCP). |

*Security: all keys live **server-side** only. The Android app talks to our backend,
never directly to Anthropic/PSA.*

---

## 3. Libraries & frameworks
**Backend (Python)**
- `fastapi`, `uvicorn` — API + server.
- `anthropic` — Claude SDK (structured output, prompt caching).
- `pydantic` — `CardInfo` models (generated from JSON Schema).
- `Pillow` / `opencv-python` — image pre-processing.
- `httpx` — external API calls (PSA, checklists).
- `psycopg`/SQLAlchemy — Postgres access.

**Android (Kotlin)**
- **CameraX** — capture/preview.
- **ML Kit Text Recognition v2** — on-device OCR (baseline, free, offline).
- **ML Kit Barcode Scanning** — slab cert barcode/QR.
- **TensorFlow Lite** (+ GPU/NNAPI delegates) — on-device models.
- **OpenCV-Android** — quad detection, perspective warp.
- **Room** — local DB; **Retrofit** + OkHttp — backend client.

**Model training / conversion (`/ml`)**
- **PyTorch** + **Ultralytics YOLO** (detector) and/or **PaddleOCR** (OCR/PP-OCR).
- **TFLite converter** + int8 quantization; on-device benchmark tooling.

**Eval (`/eval`)**
- `pandas` for scoring; simple report generation; wired into CI.

**Candidate to evaluate:** **PaddleOCR mobile** vs ML Kit for stylized card fonts.

---

## 4. Data
- **Seed image dataset** (~100–200 to start, growing): graded + raw; baseball,
  basketball, football, hockey, soccer; varied eras, brands, conditions; **front +
  back**. Include hard cases (glare, angles, foil).
- **Ground-truth labels** in `CardInfo` format (for training + eval).
- **Labeling tool**: Label Studio or CVAT (bounding boxes + field values).
- **Reference/checklist data**: imported from TCDB / SportsCardsPro into Postgres;
  a **bundled subset** ships in the app for offline normalization.
- **Licensing note**: confirm terms for third-party catalog data and card images
  before redistribution; for training, prefer self-captured images where possible.

---

## 5. Hardware
- Dev machine (the usual).
- **Training GPU**: a single modern GPU (cloud rental is fine) for Phase 4 models.
- **Android test devices**: at least one low-end, one mid-range, one recent flagship
  to benchmark on-device latency/size realistically.
- **Capture rig**: copy stand + diffuse lighting (and ideally a polarizing filter)
  to produce clean, glare-free dataset images.

---

## 6. Infrastructure
- **Backend host** (containerized) + **Postgres** + **object storage** for images.
- **Secrets manager** (server-side) for Anthropic/PSA keys.
- **CI**: GitHub Actions (lint, test, eval regression).
- **Observability**: request logs, latency/cost metrics, fallback-rate dashboards.

---

## 7. Cost model (rough, for budgeting)
**Claude per scan (Engine A) — now measured live (2026-07-06).** A front+back scan
with our prompt is ~3.8k image/turn tokens + ~8.5k static prefix (schema + field
guide + example; **cached** after the first call) + ~1k output.

| Model | $/1M in / out | Measured / est. cost per front+back scan |
|---|---|---|
| `claude-opus-4-8` | $5.00 / $25.00 | **$0.099 first call → $0.050 on cache hits** (measured) |
| `claude-sonnet-5` | $3.00 / $15.00 | ~$0.03 cached (est.) |
| `claude-haiku-4-5` | $1.00 / $5.00 | ~$0.01 cached (est.) |

Latency measured: ~12–13 s/scan on opus.
**Levers:** prompt caching, model tiering by difficulty, resize to model res, and
**on-device-first with fallback** so only hard scans hit Claude.

**Other costs:** PSA free tier (~100/day) covers dev with caching; backend host +
Postgres + storage are modest; a training GPU is the main Phase-4 expense; Play Store
has a one-time developer fee.

---

## Sources
- PSA Public API — https://www.psacard.com/publicapi/documentation
- PSA cert verification — https://www.psacard.com/cert
- Third-party cert lookup — https://tcgapis.com/psa-checker · https://cardgrade.io/tools/cert-lookup
- Claude models overview — https://platform.claude.com/docs/en/about-claude/models/overview
- Claude vision — https://platform.claude.com/docs/en/build-with-claude/vision
- Claude Opus 4.8 analysis — https://artificialanalysis.ai/models/claude-opus-4-8
- OCR comparison (PaddleOCR/Tesseract/EasyOCR) — https://www.codesota.com/ocr/paddleocr-vs-tesseract
- Open-source OCR overview — https://modal.com/blog/8-top-open-source-ocr-models-compared
- Trading Card Database — https://www.tcdb.com/
- SportsCardsPro API — https://www.sportscardspro.com/api-documentation
- Card Hedge API — https://ai.cardhedger.com/api-services
- Identifying cards with AI (reference) — https://www.ximilar.com/blog/how-to-identify-sports-cards-with-ai/
