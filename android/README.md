# android/ — on-device engine (Kotlin)

Engine B: the phone app that extracts card info **on-device** (CameraX + ML Kit OCR
+ TFLite), calling the backend only for enrichment and Claude fallback.

> Status: **Phase 0 scaffold.** Only the generated `CardInfo` Kotlin model is in
> place. The full Gradle/Android Studio project is initialized in Phase 3 (`P3-1`).

## In place now
```
android/app/src/main/java/com/cardextractor/model/CardInfo.kt   # GENERATED (do not hand-edit)
```
The model uses **kotlinx.serialization**. When the Gradle project is created, add:
- `org.jetbrains.kotlin.plugin.serialization`
- `org.jetbrains.kotlinx:kotlinx-serialization-json`

## Regenerating the model
```bash
bash ../shared/codegen/generate.sh   # regenerates from shared/schema (source of truth)
```

## Planned project (Phase 3+, see ../roadmap.md)
- **CameraX** capture (front + back) + gallery import.
- **OpenCV-Android**: card/slab quadrilateral detection + perspective warp.
- **ML Kit Text Recognition v2** (OCR) + **ML Kit Barcode** (slab cert #).
- **TFLite** models (graded-vs-raw, region detector) with GPU/NNAPI delegates.
- **Room** local store; **Retrofit** client to the backend (enrichment + fallback).
- On-device vs cloud **mode toggle**.
