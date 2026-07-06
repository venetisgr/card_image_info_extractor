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
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone

import anthropic
from jsonschema import Draft202012Validator

from app.config import DEFAULT_MODEL, MAX_OUTPUT_TOKENS
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
    ) -> ExtractionResult:
        content: list[dict] = [
            {"type": "text", "text": "FRONT of the card:"},
            _image_block(front),
        ]
        if back is not None:
            content += [{"type": "text", "text": "BACK of the same card:"}, _image_block(back)]
        else:
            content.append(
                {"type": "text", "text": "(No back image was provided for this card.)"}
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
            card=CardInfo.model_validate(record), usage=usage, raw_payload=payload
        )

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
        errors = self._validation_errors(self._extraction_validator, payload)
        if errors:
            messages.append({"role": "assistant", "content": response.content})
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
