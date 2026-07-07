"""Extractor tests (P1-3/4/5/9) with a mocked Anthropic client — no network."""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.config import resolve_model
from app.services.extractor import CardExtractor, ExtractionError
from app.services.images import ProcessedImage
from app.services.prompts import (
    TOOL_NAME,
    build_extraction_schema,
    build_system_prompt,
    build_tool_schema,
)

REPO = Path(__file__).resolve().parents[2]


def _extraction_payload() -> dict:
    """A valid tool payload: the relic example minus server-side fields."""
    data = json.loads((REPO / "shared/examples/graded_relic_example.json").read_text())
    data.pop("provenance")
    data.pop("raw_output")
    return data


def _image(tag: bytes = b"front") -> ProcessedImage:
    import hashlib

    return ProcessedImage(
        data=tag, media_type="image/jpeg", sha256=hashlib.sha256(tag).hexdigest(), width=1, height=1
    )


def _tool_response(payload: dict):
    block = SimpleNamespace(type="tool_use", id="toolu_1", name=TOOL_NAME, input=payload)
    usage = SimpleNamespace(
        input_tokens=1000,
        output_tokens=300,
        cache_creation_input_tokens=500,
        cache_read_input_tokens=0,
    )
    return SimpleNamespace(content=[block], usage=usage, stop_reason="tool_use", model="m")


class FakeClient:
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []
        self.messages = SimpleNamespace(create=self._create)

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        return self._responses.pop(0)


# ---- schema / prompt construction --------------------------------------


def test_extraction_schema_drops_server_side_fields():
    schema = build_extraction_schema()
    assert "provenance" not in schema["properties"]
    assert "raw_output" not in schema["properties"]
    assert "provenance" not in schema["required"]
    # priority fields survive
    for f in ("card_type", "photo", "autograph", "memorabilia", "graded", "attributes"):
        assert f in schema["properties"]
    # server-side validator keeps the graded-requires-graded conditional
    assert "allOf" in schema


def test_tool_schema_has_no_top_level_combinators():
    """The tools API rejects oneOf/allOf/anyOf at the top level of input_schema."""
    tool_schema = build_tool_schema()
    for kw in ("allOf", "oneOf", "anyOf"):
        assert kw not in tool_schema
    assert "card_type" in tool_schema["properties"]


def test_system_prompt_is_static_and_covers_hints():
    p1, p2 = build_system_prompt(), build_system_prompt()
    assert p1 == p2  # deterministic -> cacheable
    for needle in (
        TOOL_NAME,
        "BOTTOM of the card front",
        "NOT the serial numbering",
        "jersey_number_candidates",
        "Black is the standard",
        "MORE THAN ONE piece",
        # real-photo lessons (2026-07-06)
        "one-touch",
        "photographed from the BACK",
        "autograph_grade",
        "OFTEN ON THE BACK",
        "app interface",
    ):
        assert needle in p1


# ---- extraction flow -----------------------------------------------------


def test_happy_path_assembles_cardinfo_with_provenance():
    payload = _extraction_payload()
    client = FakeClient([_tool_response(payload)])
    result = CardExtractor(client=client).extract(
        _image(b"f"), _image(b"b"), model="test-model", verify=False
    )

    assert result.card.card_type.value == "graded"
    assert result.card.player_name == "LeBron James"
    assert result.card.provenance.engine.value == "claude"
    assert result.card.provenance.model_version == "test-model"
    assert len(result.card.provenance.source_images) == 2
    assert result.usage.attempts == 1

    call = client.calls[0]
    assert call["tool_choice"] == {"type": "tool", "name": TOOL_NAME}
    assert call["thinking"] == {"type": "disabled"}
    assert call["system"][0]["cache_control"] == {"type": "ephemeral"}
    # front + back images present in the single user turn
    images = [b for b in call["messages"][0]["content"] if b.get("type") == "image"]
    assert len(images) == 2


def test_front_only_supported():
    client = FakeClient([_tool_response(_extraction_payload())])
    result = CardExtractor(client=client).extract(
        _image(b"f"), None, model="test-model", verify=False
    )
    assert len(result.card.provenance.source_images) == 1


def test_invalid_payload_triggers_one_corrective_retry():
    bad = _extraction_payload()
    bad["card_type"] = "slabbed"  # not in the enum
    client = FakeClient([_tool_response(bad), _tool_response(_extraction_payload())])
    result = CardExtractor(client=client).extract(_image(), model="test-model", verify=False)

    assert result.usage.attempts == 2
    # corrective turn carries the errored tool_result back to the model
    retry_messages = client.calls[1]["messages"]
    assert retry_messages[2]["content"][0]["type"] == "tool_result"
    assert retry_messages[2]["content"][0]["is_error"] is True
    assert result.card.card_type.value == "graded"


def test_still_invalid_after_retry_raises():
    bad = _extraction_payload()
    bad["card_type"] = "slabbed"
    client = FakeClient([_tool_response(bad), _tool_response(bad)])
    with pytest.raises(ExtractionError):
        CardExtractor(client=client).extract(_image(), model="test-model", verify=False)


def test_graded_without_graded_block_is_rejected_then_corrected():
    bad = _extraction_payload()
    del bad["graded"]  # violates the if/then rule for graded cards
    client = FakeClient([_tool_response(bad), _tool_response(_extraction_payload())])
    result = CardExtractor(client=client).extract(_image(), model="test-model", verify=False)
    assert result.usage.attempts == 2
    assert result.card.graded is not None


# ---- self-verification pass (P1-12) ---------------------------------------


def test_verify_pass_merges_only_flagged_fields():
    first = _extraction_payload()
    first["card_number"] = "RPB-MR"  # transcription-critical -> always re-checked
    second = _extraction_payload()
    second["card_number"] = "RPA-MR"  # corrected on the second look
    second["player_name"] = "Wrong Person"  # unflagged (conf 0.99) -> must NOT merge
    client = FakeClient([_tool_response(first), _tool_response(second)])

    result = CardExtractor(client=client).extract(_image(), model="test-model", verify=True)

    assert result.usage.attempts == 2
    assert result.card.card_number == "RPA-MR"
    assert result.card.player_name == "LeBron James"  # first reading kept
    assert "card_number" in result.verified_fields
    # verification turn carries the current readings back as a tool_result
    verify_turn = client.calls[1]["messages"][2]
    assert verify_turn["content"][0]["type"] == "tool_result"
    assert "RE-EXAMINE" in verify_turn["content"][0]["content"]


def test_verify_pass_skipped_when_everything_is_confident():
    payload = _extraction_payload()
    # No critical strings present and all confidences >= threshold.
    payload["card_number"] = None
    payload["attributes"]["serial_number"] = None
    payload["attributes"]["serial_limit"] = None
    payload["graded"]["cert_number"] = None
    payload["per_field_confidence"] = {"player_name": 0.99, "graded.grade": 1.0}
    client = FakeClient([_tool_response(payload)])

    result = CardExtractor(client=client).extract(_image(), model="test-model", verify=True)

    assert result.usage.attempts == 1
    assert result.verified_fields == []


def test_verify_pass_falls_back_to_first_reading_on_bad_second_output():
    first = _extraction_payload()
    bad_second = _extraction_payload()
    bad_second["card_type"] = "slabbed"  # invalid -> verification discarded
    client = FakeClient([_tool_response(first), _tool_response(bad_second)])

    result = CardExtractor(client=client).extract(_image(), model="test-model", verify=True)

    assert result.usage.attempts == 2
    assert result.verified_fields == []
    assert result.card.card_number == first["card_number"]


def test_no_tool_use_block_raises():
    resp = SimpleNamespace(
        content=[SimpleNamespace(type="text", text="hi")],
        usage=SimpleNamespace(
            input_tokens=1, output_tokens=1, cache_creation_input_tokens=0, cache_read_input_tokens=0
        ),
        stop_reason="end_turn",
        model="m",
    )
    with pytest.raises(ExtractionError):
        CardExtractor(client=FakeClient([resp])).extract(_image(), model="test-model")


# ---- model tiering -------------------------------------------------------


def test_model_alias_resolution():
    assert resolve_model(None) == "claude-opus-4-8"
    assert resolve_model("opus") == "claude-opus-4-8"
    assert resolve_model("Sonnet") == "claude-sonnet-5"
    assert resolve_model("haiku") == "claude-haiku-4-5"
    assert resolve_model("claude-custom-model") == "claude-custom-model"
