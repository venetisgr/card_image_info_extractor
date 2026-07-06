"""API-layer tests (P1-1) with the extractor dependency overridden."""

import io
import json
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image

from app.main import app, get_extractor, get_psa_client
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


class StubPSAClient:
    """PSA stub: knows one cert; anything else is unknown."""

    available = True

    def __init__(self, record=None):
        self.record = record

    def get_cert(self, cert):
        return self.record


def _client(stub: StubExtractor, psa: StubPSAClient | None = None) -> TestClient:
    app.dependency_overrides[get_extractor] = lambda: stub
    app.dependency_overrides[get_psa_client] = lambda: psa or StubPSAClient()
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


def test_extract_applies_psa_enrichment():
    stub = StubExtractor()
    # Make the stub card PSA-graded so enrichment kicks in.
    record = stub.card.model_dump(mode="json")
    record["graded"]["grading_company"] = "PSA"
    record["graded"]["cert_number"] = "26987167"
    stub.card = CardInfo.model_validate(record)

    psa = StubPSAClient(
        record={
            "CertNumber": "26987167",
            "Year": "2007",
            "Brand": "PLAYOFF NATIONAL TREASURES",
            "Subject": "CALVIN JOHNSON",
            "CardNumber": "107",
            "Category": "Football Cards",
            "CardGrade": "9",
            "GradeDescription": "MINT 9",
        }
    )
    resp = _client(stub, psa).post(
        "/extract", files={"front": ("f.jpg", _jpeg_bytes(), "image/jpeg")}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["player_name"] == "Calvin Johnson"
    assert body["year"] == "2007"
    assert body["per_field_confidence"]["graded.grade"] == 1.0
    assert body["raw_output"]["verification"]["source"] == "psa_public_api"


def test_extract_enrich_can_be_disabled():
    stub = StubExtractor()
    record = stub.card.model_dump(mode="json")
    record["graded"]["grading_company"] = "PSA"
    record["graded"]["cert_number"] = "26987167"
    stub.card = CardInfo.model_validate(record)

    psa = StubPSAClient(record={"CertNumber": "26987167", "Subject": "CALVIN JOHNSON"})
    resp = _client(stub, psa).post(
        "/extract",
        files={"front": ("f.jpg", _jpeg_bytes(), "image/jpeg")},
        data={"enrich": "false"},
    )
    assert resp.status_code == 200
    assert resp.json()["player_name"] == "LeBron James"  # untouched


def test_verify_endpoint_found_and_missing():
    psa = StubPSAClient(record={"CertNumber": "111", "Subject": "TOM BRADY"})
    client = _client(StubExtractor(), psa)
    assert client.get("/verify/psa/111").json()["Subject"] == "TOM BRADY"

    client_missing = _client(StubExtractor(), StubPSAClient(record=None))
    assert client_missing.get("/verify/psa/999").status_code == 404


def test_response_validates_against_shared_schema():
    from jsonschema import Draft202012Validator

    stub = StubExtractor()
    resp = _client(stub).post(
        "/extract", files={"front": ("f.jpg", _jpeg_bytes(), "image/jpeg")}
    )
    schema = json.loads((REPO / "shared/schema/card_info.schema.json").read_text())
    Draft202012Validator(schema).validate(resp.json())
