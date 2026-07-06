"""API-layer tests (P1-1) with the extractor dependency overridden."""

import io
import json
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image

from app.main import app, get_extractor
from app.models.card_info import CardInfo
from app.services.extractor import ExtractionResult, Usage

REPO = Path(__file__).resolve().parents[2]


def _jpeg_bytes() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (64, 96), (180, 20, 20)).save(buf, format="JPEG")
    return buf.getvalue()


class StubExtractor:
    def __init__(self):
        self.seen_model = None
        self.card = CardInfo.model_validate_json(
            (REPO / "shared/examples/graded_relic_example.json").read_text()
        )

    def extract(self, front, back=None, model="m"):
        self.seen_model = model
        return ExtractionResult(card=self.card, usage=Usage(model=model, attempts=1))


def _client(stub: StubExtractor) -> TestClient:
    app.dependency_overrides[get_extractor] = lambda: stub
    return TestClient(app)


def teardown_function():
    app.dependency_overrides.clear()


def test_healthz():
    assert TestClient(app).get("/healthz").json() == {"status": "ok"}


def test_extract_front_and_back():
    stub = StubExtractor()
    resp = _client(stub).post(
        "/extract",
        files={
            "front": ("front.jpg", _jpeg_bytes(), "image/jpeg"),
            "back": ("back.jpg", _jpeg_bytes(), "image/jpeg"),
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["card_type"] == "graded"
    assert body["graded"]["cert_number"]
    assert stub.seen_model == "claude-opus-4-8"  # default tier


def test_extract_model_tier_form_field():
    stub = StubExtractor()
    resp = _client(stub).post(
        "/extract",
        files={"front": ("f.jpg", _jpeg_bytes(), "image/jpeg")},
        data={"model": "haiku"},
    )
    assert resp.status_code == 200
    assert stub.seen_model == "claude-haiku-4-5"


def test_extract_requires_front():
    resp = _client(StubExtractor()).post("/extract", files={})
    assert resp.status_code == 422


def test_extract_rejects_non_image():
    resp = _client(StubExtractor()).post(
        "/extract", files={"front": ("f.txt", b"not an image", "text/plain")}
    )
    assert resp.status_code == 422


def test_response_validates_against_shared_schema():
    from jsonschema import Draft202012Validator

    stub = StubExtractor()
    resp = _client(stub).post(
        "/extract", files={"front": ("f.jpg", _jpeg_bytes(), "image/jpeg")}
    )
    schema = json.loads((REPO / "shared/schema/card_info.schema.json").read_text())
    Draft202012Validator(schema).validate(resp.json())
