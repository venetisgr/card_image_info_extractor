# ml/ — on-device model training & conversion

Training, evaluation, and TFLite conversion for the on-device models (Phase 4).

> Status: **placeholder.** Populated in Phase 4 (see `../roadmap.md`).

## Planned contents
- Dataset prep + auto-labeling pipeline (Claude-as-labeler + human review).
- Training for:
  - graded-vs-raw classifier (e.g. MobileNetV3),
  - card/slab + region detector (e.g. YOLO-nano / SSD-MobileNet),
  - optional brand/logo + field-mapping models.
- **TFLite** conversion + int8 quantization; on-device latency/size benchmarks.

## Likely stack
PyTorch / Ultralytics YOLO, PaddleOCR (PP-OCR mobile), TFLite converter.
