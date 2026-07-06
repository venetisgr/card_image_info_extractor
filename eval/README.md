# eval/ — evaluation harness

Measures and compares both engines (Claude vs on-device) on a labeled test set.

> Status: **placeholder.** Built out in Phase 5; keep a lightweight version running
> from Phase 1 onward so every phase is measured (see `../roadmap.md`).

## Planned contents
- Scorer computing **per-field accuracy**, **latency**, and **cost** against
  ground-truth `CardInfo` labels.
- A/B reports: Claude vs on-device, by card type (graded/raw) and by field.
- Confidence-threshold tuning for the on-device → Claude fallback.
- Regression check wired into CI.

## Metrics of interest
Exact-match and fuzzy-match per field (player, brand, set, card #, grade, cert #,
serial #/limit + jersey-number match, jersey colors/number + candidates, autograph
presence + ink color, memorabilia pieces: type/fabric/colors/logo/letters), plus
end-to-end record accuracy.
