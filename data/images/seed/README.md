# Seed images — real card photos

Ground-truth labels for these cards already exist in `../../labels/` (created
2026-07-06 by reading the owner's photos). **The photo files themselves still
need to be added here** so the live extractor can be evaluated against the
labels.

## How to add the photos
Save each photo with its expected filename (see `../../manifest.csv`), commit,
and push:

```
data/images/seed/<card_id>__front.jpg     # and __back.jpg where a back photo exists
```

Expected files:

| card_id | faces photographed |
|---|---|
| 2008-topps-matt-ryan-rpa-mr | back |
| 2007-nt-calvin-johnson-107-jersey-raw | front |
| 2007-nt-calvin-johnson-107-patch-psa9 | front, back |
| 2007-nt-calvin-johnson-auto-raw | front |
| 1996-collectors-choice-intl-jordan-j3-psa5 | front (app screenshot) |
| 2000-upper-deck-brady-254-psa6 | front |
| 2010-contenders-demaryius-thomas-209-psa10 | front, back |
| 2007-leaf-limited-calvin-johnson-308-bgs9 | front, back |
| 2008-sp-rookie-lettermen-tashard-choice-raw | front |
| 2007-threads-gridiron-kings-peterson-cgk11-raw | front, back |
| 2007-gridiron-gear-peterson-216-raw | front, back |

Then evaluate any card with:
```bash
cd backend && python -m app.cli ../data/images/seed/<id>__front.jpg [<id>__back.jpg] --out /tmp/out.json
python ../eval/compare.py /tmp/out.json ../data/labels/<id>.json
```
