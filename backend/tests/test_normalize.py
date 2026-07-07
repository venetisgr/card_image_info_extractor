"""Normalization tests (P2-6)."""

import json
from pathlib import Path

from app.models.card_info import CardInfo
from app.services.normalize import normalize_card

REPO = Path(__file__).resolve().parents[2]


def _card(**overrides) -> CardInfo:
    record = json.loads((REPO / "shared/examples/raw_example.json").read_text())
    record.update(overrides)
    return CardInfo.model_validate(record)


def test_set_and_brand_aliases():
    card, changed = normalize_card(_card(set="Threads", brand="donruss"))
    assert card.set == "Donruss Threads"
    assert card.brand == "Donruss"
    assert "set" in changed and "brand" in changed


def test_language_qualifier_moves_to_language_field():
    card, changed = normalize_card(_card(subset="Spanish Jordan's Journal", language=None))
    assert card.subset == "Jordan's Journal"
    assert card.language == "es"
    assert "language" in changed


def test_subset_and_team_aliases():
    card, _ = normalize_card(_card(subset="Gridiron Kings", team="Georgia Tech"))
    assert card.subset == "College Gridiron Kings"
    assert card.team == "Georgia Tech Yellow Jackets"


def test_unknown_values_pass_through_unchanged():
    original = _card(set="Some Future Set 2031", team="Mars Rovers")
    card, changed = normalize_card(original)
    assert card.set == "Some Future Set 2031"
    assert card.team == "Mars Rovers"
    assert changed == []
    assert card == original


def test_idempotent():
    once, _ = normalize_card(_card(set="Threads", subset="Gridiron Kings"))
    twice, changed = normalize_card(once)
    assert twice == once
    assert changed == []
