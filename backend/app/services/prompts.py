"""System prompt + tool schema for card extraction (roadmap P1-3/P1-9).

Everything assembled here is STATIC per process: built once from files that are
fixed at deploy time, with no timestamps, request ids, or other per-request
content. That determinism is what makes the prompt-caching breakpoint on the
system block effective (any byte change would invalidate the cache).
"""

import copy
import json

from app.config import EXAMPLE_PATH, PLACEHOLDER_PATH, SCHEMA_PATH

TOOL_NAME = "record_card_info"

# Fields the SERVER fills in, not the model.
_SERVER_SIDE_FIELDS = ("provenance", "raw_output")


def load_full_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text())


def build_extraction_schema() -> dict:
    """The CardInfo JSON Schema minus server-side fields — what the model must produce.

    Used for SERVER-SIDE validation of the tool payload (keeps the top-level
    `allOf` conditional: graded cards must carry the `graded` block).
    """
    schema = copy.deepcopy(load_full_schema())
    for field in _SERVER_SIDE_FIELDS:
        schema["properties"].pop(field, None)
    schema["required"] = [f for f in schema["required"] if f not in _SERVER_SIDE_FIELDS]
    schema.pop("$id", None)
    return schema


def build_tool_schema() -> dict:
    """The extraction schema as accepted by the Claude tools API.

    The Messages API rejects `oneOf`/`allOf`/`anyOf` at the TOP level of a tool
    input_schema, so the graded-requires-`graded` conditional is dropped here;
    it is still stated in the prompt and enforced by server-side validation
    with a corrective retry.
    """
    schema = build_extraction_schema()
    schema.pop("allOf", None)
    return schema


def _worked_example() -> str:
    """The graded-relic example record, minus server-side fields."""
    example = json.loads(EXAMPLE_PATH.read_text())
    for field in _SERVER_SIDE_FIELDS:
        example.pop(field, None)
    return json.dumps(example, indent=2)


def build_system_prompt() -> str:
    placeholder = PLACEHOLDER_PATH.read_text().strip()
    example = _worked_example()
    return f"""\
You are an expert sports-card analyst. You are given photographs of ONE sports \
card — the FRONT and, when available, the BACK — and you extract structured \
information about it by calling the `{TOOL_NAME}` tool exactly once.

## What you are looking at
- The card may be RAW (a loose card) or GRADED: encased in a plastic slab by a \
grading company (PSA, BGS = Beckett, SGC, CGC, TAG, ...). A slab has a printed \
label strip (usually at the top) with a descriptive line, the grade, and a \
certification number, often with a barcode.
- Photos may have glare (slabs are reflective), slight angles, or soft focus. \
Work with what is legible; never invent what you cannot read.

## Field-by-field guidance
- `card_type`: "graded" if the card is in a slab with a grading label, else "raw".
- `graded.*` (graded cards only): read the label. `grading_company` from the \
logo/name; `grade` is the numeric grade (e.g. 9.5) and `grade_label` the printed \
wording (e.g. "GEM MINT 9.5"); `description` is the label's descriptive info \
line(s) (year/brand/set/player/card number as the grader printed them); \
`cert_number` is the certification/serial number printed on the label (often \
near a barcode); `label_text` is the full raw text of the label; `subgrades` \
only when printed (BGS slabs: centering/corners/edges/surface).
- `sport`, `year`, `brand`, `set`, `subset`: the year, brand (Topps, Panini, \
Upper Deck, Fleer, Bowman, ...), set and subset are MOST OFTEN printed at the \
BOTTOM of the card front, and on the grading label if graded. Check those \
places first, then the back (copyright line often has the year/brand).
- `player_name`: the athlete's name as printed.
- `team`: the player's team/franchise if shown.
- `card_number`: the card's number WITHIN the set as printed (e.g. "#78", \
"RC-12"), usually on the back. This is NOT the serial numbering.
- `attributes.serial_number` / `serial_limit`: only for serial-numbered \
(limited) cards like "07/99" stamped on the card: serial_number = "07" (this \
copy), serial_limit = "99" (total print run). Do NOT confuse with card_number.
- `attributes.serial_matches_jersey_number`: true when the copy's serial number \
equals the player's jersey number (e.g. 07/99 and the player wears #7) — such \
copies are rarer. Use the jersey number visible in the photo or well-known for \
the player; null if you cannot tell.
- `attributes.rookie`: true for rookie cards (look for "RC", "Rookie", rookie \
logos, or rookie-year sets).
- `photo.jersey_colors`: the distinct colors of the jersey the player wears IN \
THE PRINTED PICTURE (e.g. ["red","black","white"]).
- `photo.jersey_number`: the number visible on that jersey in the picture, as \
printed. If it is only partially visible or ambiguous, set `jersey_number` to \
your best guess (or null) and list ALL plausible readings in \
`jersey_number_candidates`, best first.
- `autograph.present`: is there a signature on the card? `autograph.ink_color`: \
the ink color (e.g. "black", "blue", "gold", "silver"). Black is the standard; \
any other color is rarer — read the actual ink color carefully.
- `memorabilia`: cards may embed REAL material pieces ("relics"): jersey \
swatches, patches, ball pieces, floor pieces, shoe pieces. There can be MORE \
THAN ONE piece in a card — analyze each piece separately in `pieces[]`:
  - `type`: patch (multi-color jersey patch) | jersey (plain swatch) | ball | \
floor | shoe | other.
  - `is_fabric`: true if it is an actual piece of fabric/material, false if it \
is a printed facsimile of one, null if unclear.
  - `colors` + `unique_color_count`: the distinct colors in the piece (more \
colors usually means a rarer patch).
  - `contains_team_logo_part`: does the piece include part of the team logo?
  - `contains_player_name_part` / `contains_team_name_part`: does it include \
nameplate/team lettering?
  - `letters_visible`: any letters/characters readable in the piece (e.g. "AME").
- `per_field_confidence`: your confidence (0-1) per extracted field, keyed by \
field name or dot-path (e.g. "player_name": 0.97, "autograph.ink_color": 0.8). \
Include entries for every non-null field you extracted.

## Rules
- Use BOTH images: the front usually carries the picture, autograph, \
memorabilia and serial stamp; the back usually carries the card number, set \
details and copyright line. The grading label may appear on both faces.
- Set any field you cannot determine to null (or [] / false per the schema) — \
NEVER guess silently. Express uncertainty through `per_field_confidence` and \
`jersey_number_candidates`.
- Report colors as simple lowercase color names ("wine", "navy", "gold").
- Call the `{TOOL_NAME}` tool exactly once with the completed record. Do not \
reply with prose.

## Output shape (placeholder with allowed values)
{placeholder}

## Worked example (a graded BGS patch-autograph card, serial 23/99)
{example}
"""
