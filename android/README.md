# android/ — on-device engine (Engine B)

The phone app: capture front/back → **ML Kit OCR + barcode** → **rules parser**
→ the same canonical `CardInfo` as the cloud engine. Offline by default, with a
cloud (Claude) mode that calls our backend.

> Status: **Phase 3 baseline implemented.** The pure-Kotlin parsing core is
> **built and unit-tested** (7 tests green, run in CI-like conditions with only
> a JDK). The `:app` module is complete but needs the Android SDK to compile —
> open `android/` in Android Studio and it activates automatically.

## Modules
```
android/
├── core/   PURE JVM — builds anywhere with JDK 17+:
│   ├── model/CardInfo.kt        GENERATED from shared/schema (do not hand-edit)
│   └── parser/                  OcrCardParser: OCR text + barcodes -> CardInfo
│       └── Reference.kt         bundled offline subset: brands/sets/set→brand,
│                                grading companies, team nicknames, sports
└── app/    Android app (needs SDK; auto-skipped without one):
    ├── vision/                  ML Kit Text Recognition v2 + Barcode scanning
    ├── extract/                 OnDeviceExtractor · CloudExtractor · mode enum
    ├── net/BackendApi.kt        Retrofit -> our FastAPI backend (/extract)
    ├── db/Scans.kt              Room: scan history (CardInfo stored as JSON)
    ├── ui/                      Compose: Capture · Result · History
    └── MainActivity/ViewModel   tabbed shell + state
```

## Build & test
```bash
cd android
gradle :core:test        # parser unit tests — works WITHOUT the Android SDK
# Full app: open android/ in Android Studio (creates local.properties),
# then run the :app configuration on a device/emulator.
```

## How the on-device engine works (baseline)
1. Photos come from the system camera or gallery (no runtime permissions).
2. ML Kit reads text from both faces + any barcode (slab labels carry the cert).
3. `OcrCardParser` applies rules + the bundled reference subset:
   grading company tokens → graded/raw; grade vocab ("GEM MT 10", "9 MINT");
   subgrades + separate autograph grade; cert (barcode beats OCR digits);
   serial `NN/NNN` with COA-date rejection; year/brand/set (set→brand mapping
   outranks token scan); card number (`#254`, `CARD NO.`, `RPA-MR`);
   player-name and team-line heuristics; rookie/auto/memorabilia flags.
4. Result validates as canonical `CardInfo`, saved to Room; per-field
   confidences included.

**Known limits (by design, until Phase 4):** visual-only fields — jersey
colors/number in the photo, memorabilia piece analysis (colors/fabric/letters),
ink color — stay null on-device; the cloud mode fills them. That's the Phase 4
TFLite work (detector + classifiers) and/or the confidence-based fallback.

## Cloud mode / backend
`BuildConfig.BACKEND_BASE_URL` defaults to `http://10.0.2.2:8000/` (host
machine from the emulator). Run the backend with `uvicorn app.main:app` and
switch the in-app toggle to "Cloud (Claude)".

## Follow-ups
- **P3-1b**: in-app CameraX preview with card-framing guidance (deps already
  in the version catalog).
- **P3-2**: OpenCV quad detection + perspective warp before OCR.
- Confidence-driven auto-fallback (on-device first, cloud when weak) — P5.
