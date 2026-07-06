# Real-photo eval — 2026-07-06 (P1-10)

11 real cards (owner's collection), live extraction with `claude-opus-4-8`,
scored per field against `data/labels/` with `eval/compare.py` (strict exact
match after case/whitespace normalization).

## Headline
- **265 / 291 scored fields exact-match ≈ 91%** · 2 cards at 100%
- **All 11 first-attempt valid** (validation retry never needed)
- Avg **~10.2 s** and **~$0.049** per card (prompt cache: 9,035 tokens read
  per call after the first)

| Card | Accuracy | Notes |
|---|---|---|
| Gridiron Gear AP #216 (3-piece relic) | **100%** (42/42) | incl. all 3 pieces + 40/50 |
| NT Calvin Johnson auto (raw) | **100%** (16/16) | one-touch correctly = raw |
| Contenders Demaryius #209 PSA 10 | 96% | only label-text word order |
| Brady UD #254 PSA 6 | 95.5% | only label-text word order |
| NT CJ #107 jersey (raw) | 95.7% | card # not printed on front (GT knowledge) |
| Threads Gridiron Kings AP CGK-11 | 94.1% | set-name canonicalization only |
| NT CJ #107 patch PSA 9 | 93.5% | label-text spacing/order only |
| Leaf Limited CJ #308 BGS 9 | 90.6% | "MINT 9" vs "9 MINT" + label order; subgrades + autograph_grade 10 ✓ |
| Jordan CC Int'l #J3 PSA 5 (screenshot) | 90.5% | subset naming + label order |
| Matt Ryan Topps (BGS, back-only, rotated) | 68.8% | model left card-level facts null that aren't visible on the back (GT encoded card knowledge) |
| SP Rookie Lettermen Choice (raw) | 69.0% | hardest card — see below |

## Priority-field scorecard (across all 11)
- **graded vs raw: 11/11** — every one-touch holder correctly classified raw; both slab types correct (incl. BGS shot from the back)
- **Grading company 5/5 · cert numbers 5/5 · grades 5/5** (+ BGS subgrades 9/8.5/9/9 and the separate **autograph grade 10** captured)
- **Player name 11/11 · sport 11/11**
- **Serial numbering 5/5** (05/99, 1/1, 4/4, 16/25, 40/50 — all read from backs)
- **Autograph presence + ink 10/10 fronts** — incl. **blue** (Demaryius) and **silver on the letter patch** (Choice)
- **Memorabilia pieces**: 3-piece card perfect; letter patch caught as fabric patch (missed the "part of team name" flag)
- **Jersey number in photo**: 6/7 visible ones correct; 1 null (Choice, partially hidden)

## Mismatch taxonomy (26 total)
1. **Free-text transcription order (~10)** — `label_text`/`description` word order
   differs from GT while both are faithful readings → eval artifact; score these
   fuzzy (token-set), not exact.
2. **Name canonicalization (~8)** — "Threads" vs "Donruss Threads", "Gridiron
   Kings" vs "College Gridiron Kings", "gold" vs "yellow", "blue" vs "navy",
   "Georgia Tech" vs "Georgia Tech Yellow Jackets"… → exactly what the (on-hold)
   checklist/normalization phase (P2-4/P2-5) fixes.
3. **Conservative nulls on back-only input (~5)** — Matt Ryan card: model
   declined to infer autograph/subset from "RPA-MR"; GT encoded card-level
   knowledge not visible in the image. Arguably correct model behavior; GT
   convention needs a decision (image-visible truth vs card truth).
4. **Genuine misses (~3)** — Choice: jersey number not attempted (no
   candidates given), letter-patch `contains_team_name_part` false, team read
   as college (nameplate says YELLOW JACKETS) instead of the pictured Cowboys.

## Actions suggested by the data
- Make `label_text`/`description` fuzzy-scored in `eval/compare.py`.
- Decide the GT convention for facts not visible in the provided image(s).
- The canonicalization bucket strengthens the case for resuming P2-4/P2-5
  (user has it on hold — reminder task open).
- Prompt nudge: when a jersey number is partially occluded, propose candidates
  instead of null; for lettermen cards, prefer the pictured pro team for `team`.
