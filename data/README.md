# data/ — datasets, labels, reference tables

Holds the image dataset, ground-truth labels, and reference/normalization tables.

> Status: **placeholder.** Seed dataset is collected in Phase 0 (`P0-4`).

## Planned layout
```
data/
├── images/          # captured card images (front + back)  [git-ignored: large/binary]
├── labels/          # ground-truth CardInfo JSON per image (see shared/schema)
├── reference/       # normalization tables (manufacturers, sets, aliases)
└── manifest.csv     # index: image id -> sport/type/source/label path
```

## Guidelines
- Capture **front and back**; include hard cases (glare on slabs, angles, foil).
- Cover graded + raw across baseball, basketball, football, hockey, soccer.
- Labels conform to the `CardInfo` schema (`../shared/schema/card_info.schema.json`).
- **Licensing:** prefer self-captured images; confirm terms before redistributing
  third-party catalog data or images. Do not commit large image binaries (see
  `.gitignore`); store them via object storage / a tracked manifest.
