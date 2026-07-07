# Real-photo eval v3 — 2026-07-06 (self-verification pass, P1-12)

Same 11 cards. New: the extractor's **self-verification pass** — after the
first reading, fields with self-reported confidence < 0.9 plus the
transcription-critical strings (card #, cert #, serial) are re-examined in a
second turn of the same conversation ("read character-by-character..."), and
only those flagged paths merge back. Default ON (`verify=false` / `--no-verify`
to skip). A second opinion only replaces the first when at least as confident
(critical strings always take the closer look).

## Results
| Run | Accuracy | Cards at 100% | avg cost/scan |
|---|---|---|---|
| v2 (prompt v3.1 + normalization) | 278/282 = 98.6% | 8/11 | ~$0.05 |
| **v3 (+ verification pass)** | **278/282 = 98.6%** | **9/11** | ~$0.10 |

Headline unchanged, composition better: **the verification pass fixed the
exact class it targets** — the Matt Ryan `RPA-MR` misread (tiny rotated print)
was caught and corrected on the second look, making that card perfect.

## Remaining 4 mismatches (2 cards)
- **NT CJ patch (PSA slab)**: one piece judged `jersey` vs `patch` and one
  color zone `gray` vs `white` — the second look re-judged the piece slightly
  differently. (The merge now carries a confidence guard: a less-confident
  second opinion no longer replaces the first; added after this run.)
- **SP Lettermen**: the "YELLOW JACKETS" plate is still attributed to the
  player's name rather than the team's name (booleans flipped). `team` itself
  is now correctly Dallas Cowboys.

Both residuals are semantic vision judgments — borderline even for a human at
this photo quality — and exactly what the remaining levers address:
**live PSA verification** (pins graded-card identity fields at 1.0),
**checklist matching** (raw-card identity), and **Phase 4 vision models**
(dedicated patch/piece analysis).

## Cost/latency
Verification doubles calls when triggered (~17s, ~$0.10/scan on opus).
`verify=false` restores single-pass (~9s, ~$0.05). The prompt cache holds
across both passes (18.7k tokens read on pass 2).
