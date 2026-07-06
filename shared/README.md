# shared/ — the canonical `CardInfo` contract

This directory holds the **single source of truth** for the data both engines
(Claude API and on-device) produce.

```
shared/
├── schema/card_info.schema.json   # SOURCE OF TRUTH (JSON Schema, draft 2020-12)
├── templates/
│   └── card_info_placeholder.json # human/prompt-facing placeholder (every field + allowed values)
├── examples/                      # schema-valid sample records used by tests
│   ├── graded_example.json        # graded slab (PSA)
│   ├── graded_relic_example.json  # graded patch+auto, 2 memorabilia pieces, serial 23/99 (jersey-matched)
│   └── raw_example.json           # raw (ungraded) card, uncertain jersey number
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
**grading company** (PSA / BGS=Beckett / SGC / CGC / TAG), the **cert number** and
**label description**, **sport/year/brand/set/subset**, the **player name**, the
**card number within the set**, **autograph** presence + **ink color** (black is
standard; other colors rarer), the **jersey colors & number in the player's photo**
(`photo`, with `jersey_number_candidates` when unsure), **memorabilia** with one
entry per embedded piece (patch/jersey/ball/floor/shoe: real fabric?, colors +
unique count, team-logo part, name/team letters visible), and **serial numbering**
for limited cards like 07/99 (`serial_number` = 07, `serial_limit` = 99, plus
`serial_matches_jersey_number` for the rarer jersey-matched copies).

A human/prompt-facing **placeholder** showing every field with its allowed values
lives at [`templates/card_info_placeholder.json`](templates/card_info_placeholder.json).
See `architecture_components.md` §4 for the full field table.
