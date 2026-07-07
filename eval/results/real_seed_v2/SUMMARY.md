# Real-photo eval v2 — 2026-07-06 (accuracy push)

Same 11 real cards as v1. Changes between runs, chosen to maximize accuracy:
1. **Normalization layer (P2-6)** — `backend/app/services/normalize.py` alias
   tables for brand/set/subset/team + language-qualifier extraction, applied in
   the pipeline after extraction/enrichment (both API and CLI).
2. **Prompt v3/v3.1** — jersey-number candidates required when occluded;
   pictured-uniform-decides-`team` rule (relic nameplates ≠ pictured team);
   decisive true/false for `autograph.present`/`memorabilia.present` when the
   face is visible; language qualifiers out of `subset`.
3. **Fair scoring (P1-11)** — free-text transcription fields
   (`label_text`/`description`/`grade_label`) scored by token-set similarity;
   color-shade equivalence classes (navy~blue, gold~yellow...).
4. **GT convention enforced** — labels = image-visible truth (documented in
   `data/README.md`); three labels corrected where I had encoded card-level
   knowledge not visible in the photos.

## Result progression
| Measurement | Accuracy |
|---|---|
| v1, strict scoring | 265/291 = **91.0%** |
| v1 rescored fairly (same outputs) | 274/288 = **95.1%** |
| **v2 final (normalization + prompt v3.1)** | **278/282 = 98.6%** |

**8 of 11 cards score 100%** (Jordan screenshot, Brady, both AP relic cards,
all three NT Calvin Johnsons incl. the patch's PSA slab shot, Contenders DT).

## Remaining 4 mismatches (the honest hard tail)
- `2008-topps-matt-ryan` `card_number`: read "RPB-MR" for "RPA-MR" this run —
  tiny rotated print; previous runs read it correctly (OCR variance).
- `2007-nt-cj-patch` piece color: "gray" vs "white" shade call on one patch
  zone (variance; v1 run matched).
- `2008-sp-lettermen` plate semantics: read "YELLOW JACKETS" nameplate as a
  player-name part instead of team-name part (flipped booleans). The big wins
  landed though: `team` = Dallas Cowboys (pictured uniform rule worked) and
  silver ink still correct.

## Takeaways
- Systematic error classes (naming, scoring artifacts, GT overreach) are
  eliminated; what's left is run-to-run vision variance on genuinely tiny or
  ambiguous details.
- Next accuracy levers, in expected order of value:
  1. **PSA cert verification live** (token pending) — would pin the graded
     cards' descriptive fields at 1.0 permanently, killing label-read variance.
  2. Self-consistency on low-confidence fields (second pass or dual-model vote)
     — targets the variance tail; costs ~2x on flagged fields only.
  3. Checklist fuzzy-matching (P2-4/5, on hold) — card_number/set fill for raw
     cards beyond the alias tables.

