"""Enrichment tests (P2-2): verified-beats-extracted reconciliation."""

import json
from pathlib import Path

from app.models.card_info import CardInfo
from app.services.enrich import enrich_card, map_psa_record
from app.services.psa import PSAError

REPO = Path(__file__).resolve().parents[2]

PSA_RECORD = {
    "CertNumber": "26987167",
    "Year": "2007",
    "Brand": "PLAYOFF NATIONAL TREASURES",
    "Subject": "CALVIN JOHNSON",
    "CardNumber": "107",
    "Category": "Football Cards",
    "CardGrade": "9",
    "GradeDescription": "MINT 9",
    "Variety": "AUTOGRAPH-JERSEY",
}


class StubPSA:
    def __init__(self, record=None, error=None, available=True):
        self.record, self.error, self.available = record, error, available
        self.asked = []

    def get_cert(self, cert):
        self.asked.append(cert)
        if self.error:
            raise self.error
        return self.record


def _graded_card(**overrides) -> CardInfo:
    """A PSA-graded card as the extractor might produce it — with OCR slips."""
    record = json.loads((REPO / "shared/examples/graded_relic_example.json").read_text())
    record["graded"].update(
        {"grading_company": "PSA", "cert_number": "26987167", "grade": 8, "grade_label": "NM-MT 8"}
    )
    record["year"] = "2006"  # wrong on purpose: PSA says 2007
    record["player_name"] = "Calvin Jonson"  # OCR typo
    record.update(overrides)
    return CardInfo.model_validate(record)


def test_map_psa_record_paths():
    mapped = map_psa_record(PSA_RECORD)
    assert mapped["player_name"] == "Calvin Johnson"
    assert mapped["sport"] == "football"
    assert mapped["graded.grade"] == 9.0
    assert mapped["graded.cert_number"] == "26987167"
    assert mapped["brand"] == "Playoff National Treasures"


def test_enrich_overrides_and_marks_verified():
    card, outcome = enrich_card(_graded_card(), StubPSA(record=PSA_RECORD))
    assert outcome.attempted and outcome.verified
    assert card.year == "2007"  # corrected
    assert card.player_name == "Calvin Johnson"  # typo fixed
    assert card.graded.grade == 9.0
    assert card.per_field_confidence["player_name"] == 1.0
    assert card.per_field_confidence["graded.grade"] == 1.0
    assert card.raw_output["verification"]["source"] == "psa_public_api"
    assert "year" in outcome.changed_fields and "player_name" in outcome.changed_fields


def test_non_psa_cards_pass_through():
    record = json.loads((REPO / "shared/examples/graded_relic_example.json").read_text())
    bgs_card = CardInfo.model_validate(record)  # BGS in the example
    stub = StubPSA(record=PSA_RECORD)
    card, outcome = enrich_card(bgs_card, stub)
    assert not outcome.attempted and not stub.asked
    assert card == bgs_card


def test_raw_cards_pass_through():
    record = json.loads((REPO / "shared/examples/raw_example.json").read_text())
    card_in = CardInfo.model_validate(record)
    card, outcome = enrich_card(card_in, StubPSA(record=PSA_RECORD))
    assert not outcome.attempted
    assert card == card_in


def test_missing_token_skips_gracefully():
    card, outcome = enrich_card(_graded_card(), StubPSA(available=False))
    assert not outcome.attempted
    assert "token" in outcome.note


def test_psa_error_does_not_break_extraction():
    card_in = _graded_card()
    card, outcome = enrich_card(card_in, StubPSA(error=PSAError("rate limit")))
    assert outcome.attempted and not outcome.verified
    assert card == card_in
    assert "rate limit" in outcome.note


def test_unknown_cert_reported():
    card, outcome = enrich_card(_graded_card(), StubPSA(record=None))
    assert outcome.attempted and not outcome.verified
    assert "no record" in outcome.note
