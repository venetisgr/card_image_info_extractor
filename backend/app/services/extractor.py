"""Claude extraction engine (Engine A) — roadmap P1-3/4/5/6/9.

Design (see architecture_components.md §6):
- Forced tool use: the model must call `record_card_info`, whose input schema is
  the shared CardInfo contract minus server-side fields. (Strict structured
  outputs can't express the `per_field_confidence` open map, so we validate
  server-side instead and correct with one retry.)
- Prompt caching: one cache breakpoint on the (static) system prompt block —
  tools render before system, so the marker caches tools + system together.
- Front + back are sent in one user turn; provenance is stamped server-side.
"""

import base64
import copy
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone

import anthropic
from jsonschema import Draft202012Validator

from app.config import DEFAULT_MODEL, MAX_OUTPUT_TOKENS, VERIFY_CONF_THRESHOLD
from app.models.card_info import CardInfo
from app.services.images import ProcessedImage
from app.services.prompts import (
    TOOL_NAME,
    build_extraction_schema,
    build_system_prompt,
    build_tool_schema,
    load_full_schema,
)


class ExtractionError(RuntimeError):
    """The model failed to produce a schema-valid record (after one retry)."""


@dataclass
class Usage:
    """Token usage accumulated across attempts, for cost/latency logging."""

    model: str = ""
    attempts: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_input_tokens: int = 0
    cache_read_input_tokens: int = 0

    def add(self, usage) -> None:
        self.attempts += 1
        self.input_tokens += usage.input_tokens or 0
        self.output_tokens += usage.output_tokens or 0
        self.cache_creation_input_tokens += getattr(usage, "cache_creation_input_tokens", 0) or 0
        self.cache_read_input_tokens += getattr(usage, "cache_read_input_tokens", 0) or 0

    def as_dict(self) -> dict:
        return {
            "model": self.model,
            "attempts": self.attempts,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cache_creation_input_tokens": self.cache_creation_input_tokens,
            "cache_read_input_tokens": self.cache_read_input_tokens,
        }


@dataclass
class ExtractionResult:
    card: CardInfo
    usage: Usage
    raw_payload: dict = field(repr=False, default_factory=dict)
    verified_fields: list[str] = field(default_factory=list)


# Transcription-critical strings: always worth a second look when present —
# a single misread character changes the identity (RPA-MR vs RPB-MR).
_CRITICAL_PATHS = (
    "card_number",
    "graded.cert_number",
    "attributes.serial_number",
    "attributes.serial_limit",
)


def _get_path(obj, path: str):
    current = obj
    for part in path.split("."):
        if isinstance(current, dict):
            if part not in current:
                return None
            current = current[part]
        elif isinstance(current, list) and part.isdigit() and int(part) < len(current):
            current = current[int(part)]
        else:
            return None
    return current


def _set_path(obj, path: str, value) -> bool:
    parts = path.split(".")
    current = obj
    for part in parts[:-1]:
        if isinstance(current, dict) and part in current:
            current = current[part]
        elif isinstance(current, list) and part.isdigit() and int(part) < len(current):
            current = current[int(part)]
        else:
            return False
    last = parts[-1]
    if isinstance(current, dict):
        current[last] = value
        return True
    if isinstance(current, list) and last.isdigit() and int(last) < len(current):
        current[int(last)] = value
        return True
    return False


def _image_block(image: ProcessedImage) -> dict:
    return {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": image.media_type,
            "data": base64.standard_b64encode(image.data).decode("ascii"),
        },
    }


class CardExtractor:
    """Extracts a CardInfo record from front(+back) photos via the Claude API."""

    def __init__(self, client: anthropic.Anthropic | None = None):
        self._client = client or anthropic.Anthropic()
        self._extraction_validator = Draft202012Validator(build_extraction_schema())
        self._full_validator = Draft202012Validator(load_full_schema())
        self._system = [
            {
                "type": "text",
                "text": build_system_prompt(),
                # Static prefix (tools + system) -> cached across requests.
                "cache_control": {"type": "ephemeral"},
            }
        ]
        self._tools = [
            {
                "name": TOOL_NAME,
                "description": (
                    "Record the structured information extracted from the sports card "
                    "photographs. Must be called exactly once with the completed record."
                ),
                "input_schema": build_tool_schema(),
            }
        ]

    def extract(
        self,
        front: ProcessedImage,
        back: ProcessedImage | None = None,
        model: str = DEFAULT_MODEL,
        verify: bool = True,
    ) -> ExtractionResult:
        content: list[dict] = [
            {"type": "text", "text": "FRONT of the card:"},
            _image_block(front),
        ]
        if back is not None:
            content += [{"type": "text", "text": "BACK of the same card:"}, _image_block(back)]
        else:
            content.append(
                {
                    "type": "text",
                    "text": "(Only one image was provided — it may show either face of the card.)",
                }
            )
        content.append(
            {
                "type": "text",
                "text": f"Extract the card information and record it via the `{TOOL_NAME}` tool.",
            }
        )
        messages: list[dict] = [{"role": "user", "content": content}]

        usage = Usage(model=model)
        payload, errors = self._attempt(messages, model, usage)
        if errors:
            # One corrective retry: feed the validation errors back as an
            # errored tool_result and ask the (still forced) tool to be
            # called again with corrected data.
            payload, errors = self._attempt(messages, model, usage)
            if errors:
                raise ExtractionError(
                    "model output failed schema validation after retry: " + "; ".join(errors)
                )

        verified_fields: list[str] = []
        if verify:
            payload, verified_fields = self._verify_pass(messages, model, usage, payload)

        record = dict(payload)
        record["provenance"] = {
            "engine": "claude",
            "model_version": model,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source_images": [img.source_ref for img in (front, back) if img is not None],
        }
        record.setdefault("raw_output", None)

        final_errors = self._validation_errors(self._full_validator, record)
        if final_errors:
            raise ExtractionError("assembled record failed validation: " + "; ".join(final_errors))
        return ExtractionResult(
            card=CardInfo.model_validate(record),
            usage=usage,
            raw_payload=payload,
            verified_fields=verified_fields,
        )

    # -- self-verification pass (P1-12) -------------------------------------

    def _fields_to_verify(self, payload: dict) -> list[str]:
        confidences = payload.get("per_field_confidence") or {}
        flagged = {
            path
            for path, conf in confidences.items()
            if isinstance(conf, (int, float)) and conf < VERIFY_CONF_THRESHOLD
        }
        for path in _CRITICAL_PATHS:
            if _get_path(payload, path) not in (None, "", []):
                flagged.add(path)
        return sorted(flagged)

    def _verify_pass(
        self, messages: list[dict], model: str, usage: Usage, payload: dict
    ) -> tuple[dict, list[str]]:
        """Re-examine low-confidence + transcription-critical fields once.

        Only the flagged paths are merged back from the second reading, so a
        stray change to an already-confident field cannot regress the record.
        Any failure in the verification turn falls back to the first reading.
        """
        flagged = self._fields_to_verify(payload)
        if not flagged:
            return payload, []

        last_tool_use_id = self._last_tool_use_id(messages)
        current = {path: _get_path(payload, path) for path in flagged}
        messages.append(
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": last_tool_use_id,
                        "content": (
                            "Recorded. Before finalizing, RE-EXAMINE the photographs and "
                            "verify these fields (current readings shown):\n"
                            + json.dumps(current, indent=2)
                            + "\nRead small print character-by-character — card numbers, "
                            "cert numbers and serial stamps are often tiny, rotated, or "
                            "behind glare, and a single wrong character changes the card's "
                            "identity. For memorabilia pieces, recheck each piece's colors "
                            "and whether visible lettering belongs to the player's name or "
                            "the team's name. Then call `" + TOOL_NAME + "` once more with "
                            "the COMPLETE record: corrected where needed, unchanged elsewhere."
                        ),
                    }
                ],
            }
        )
        try:
            second, errors = self._attempt(messages, model, usage)
        except ExtractionError:
            return payload, []
        if errors:
            return payload, []

        merged = copy.deepcopy(payload)
        applied: list[str] = []
        first_conf = payload.get("per_field_confidence") or {}
        second_conf = second.get("per_field_confidence") or {}
        for path in flagged:
            new_value = _get_path(second, path)
            if new_value is None:
                continue
            # A second opinion only replaces the first when it is at least as
            # confident (critical transcription strings always take the
            # closer character-level look).
            if path not in _CRITICAL_PATHS:
                c1, c2 = first_conf.get(path), second_conf.get(path)
                if (
                    isinstance(c1, (int, float))
                    and isinstance(c2, (int, float))
                    and c2 < c1
                ):
                    continue
            if _set_path(merged, path, new_value):
                applied.append(path)
                confidence = second_conf.get(path)
                if isinstance(confidence, (int, float)):
                    merged.setdefault("per_field_confidence", {})[path] = confidence
        if self._validation_errors(self._extraction_validator, merged):
            return payload, []  # merged form went invalid -> keep first reading
        return merged, applied

    @staticmethod
    def _last_tool_use_id(messages: list[dict]) -> str:
        for message in reversed(messages):
            if message.get("role") != "assistant":
                continue
            for block in reversed(message.get("content") or []):
                block_type = block.type if hasattr(block, "type") else block.get("type")
                if block_type == "tool_use":
                    return block.id if hasattr(block, "id") else block["id"]
        raise ExtractionError("no prior tool_use turn to verify against")

    # -- internals ---------------------------------------------------------

    def _attempt(self, messages: list[dict], model: str, usage: Usage):
        """One model call; on invalid output, appends the corrective turn.

        Returns (payload, errors); errors is empty on success.
        """
        response = self._client.messages.create(
            model=model,
            max_tokens=MAX_OUTPUT_TOKENS,
            # Forced tool choice is incompatible with thinking; disable it
            # explicitly (on some models omitting `thinking` enables adaptive).
            thinking={"type": "disabled"},
            system=self._system,
            tools=self._tools,
            tool_choice={"type": "tool", "name": TOOL_NAME},
            messages=messages,
        )
        usage.add(response.usage)

        if response.stop_reason == "refusal":
            raise ExtractionError("the model declined to process these images (refusal)")

        tool_use = next((b for b in response.content if b.type == "tool_use"), None)
        if tool_use is None:
            raise ExtractionError(
                f"model returned no tool call (stop_reason={response.stop_reason})"
            )

        payload = tool_use.input
        # Keep the assistant turn in history: both the corrective retry and the
        # verification pass continue this same conversation.
        messages.append({"role": "assistant", "content": response.content})
        errors = self._validation_errors(self._extraction_validator, payload)
        if errors:
            messages.append(
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_use.id,
                            "is_error": True,
                            "content": (
                                "The recorded data failed schema validation:\n- "
                                + "\n- ".join(errors)
                                + f"\nCall `{TOOL_NAME}` again with a corrected, complete record."
                            ),
                        }
                    ],
                }
            )
        return payload, errors

    @staticmethod
    def _validation_errors(validator: Draft202012Validator, instance) -> list[str]:
        errors = sorted(validator.iter_errors(instance), key=lambda e: list(e.absolute_path))
        return [
            f"{'/'.join(str(p) for p in e.absolute_path) or '<root>'}: {e.message}"
            for e in errors[:10]
        ]
