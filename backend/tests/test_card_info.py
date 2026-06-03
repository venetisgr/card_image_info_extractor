"""Keep the schema, example records, and generated Pydantic types in sync.

These tests validate every example in ``shared/examples`` against both the JSON
Schema (the source of truth) and the generated Pydantic model, and check the
conditional rule that a graded card must carry its ``graded`` block.
"""

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from app.models.card_info import CardInfo

REPO = Path(__file__).resolve().parents[2]
SCHEMA = json.loads((REPO / "shared/schema/card_info.schema.json").read_text())
EXAMPLES = sorted((REPO / "shared/examples").glob("*.json"))


def test_schema_is_valid_draft_2020_12():
    Draft202012Validator.check_schema(SCHEMA)


def test_examples_exist():
    assert EXAMPLES, "no example records found under shared/examples"


@pytest.mark.parametrize("path", EXAMPLES, ids=lambda p: p.name)
def test_example_matches_schema(path):
    Draft202012Validator(SCHEMA).validate(json.loads(path.read_text()))


@pytest.mark.parametrize("path", EXAMPLES, ids=lambda p: p.name)
def test_example_roundtrips_through_pydantic(path):
    obj = CardInfo.model_validate_json(path.read_text())
    assert CardInfo.model_validate_json(obj.model_dump_json()) == obj


def test_priority_fields_present_on_relic_example():
    """The relic example must populate the user's priority fields."""
    obj = CardInfo.model_validate_json(
        (REPO / "shared/examples/graded_relic_example.json").read_text()
    )
    assert obj.card_type.value == "graded"
    assert obj.graded and obj.graded.grading_company is not None
    assert obj.graded.cert_number
    assert obj.player_name
    assert obj.photo and obj.photo.jersey_colors and obj.photo.jersey_number
    assert obj.relic and obj.relic.swatch_colors
    assert obj.attributes.serial_number == "5"
    assert obj.attributes.serial_limit == "30"


def test_graded_card_requires_graded_block():
    data = json.loads((REPO / "shared/examples/graded_example.json").read_text())
    del data["graded"]
    with pytest.raises(Exception):
        Draft202012Validator(SCHEMA).validate(data)
