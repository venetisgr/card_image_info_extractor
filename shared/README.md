# shared/ — the canonical `CardInfo` contract

This directory holds the **single source of truth** for the data both engines
(Claude API and on-device) produce.

```
shared/
├── schema/card_info.schema.json   # SOURCE OF TRUTH (JSON Schema, draft 2020-12)
├── examples/                      # sample records used by tests
│   ├── graded_example.json        # graded slab (PSA)
│   ├── graded_relic_example.json  # graded relic + autograph, serial #5/30, jersey swatch
│   └── raw_example.json           # raw (ungraded) card
└── codegen/generate.sh            # regenerates the Pydantic + Kotlin types
```

## Generated types (do not hand-edit)
- **Python / Pydantic v2** → `backend/app/models/card_info.py`
- **Kotlin / kotlinx.serialization** → `android/app/src/main/java/com/cardextractor/model/CardInfo.kt`

## Regenerating
After editing `schema/card_info.schema.json`, regenerate both type sets:

```bash
# Python tool (in a venv): pip install "datamodel-code-generator[http]" pydantic
# Kotlin tool: Node.js (npx quicktype, fetched on demand)
bash shared/codegen/generate.sh
```

Then run the backend tests to confirm the schema, examples, and generated types
stay in sync:

```bash
cd backend && python -m pytest
```

## What the schema captures
The priority fields (per project requirements): whether the card is **graded**, the
**grading company** (PSA / BGS=Beckett / SGC / CGC / TAG), the **cert number**, the
**player name**, the **jersey colors & number in the player's photo** (`photo`), the
**colors of an embedded relic swatch** (`relic.swatch_colors`), and **serial
numbering** for limited cards like 5/30 (`attributes.serial_number` = 5,
`attributes.serial_limit` = 30). Additional descriptive fields (year, set, team,
parallel, etc.) are optional enrichment. See `architecture_components.md` §4.
