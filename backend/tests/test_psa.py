"""PSA client tests (P2-1): lookups, caching, and error mapping — no network."""

import json

import httpx
import pytest

from app.services.psa import PSAClient, PSAError

CERT = "26987167"
RECORD = {
    "CertNumber": CERT,
    "Year": "2007",
    "Brand": "PLAYOFF NATIONAL TREASURES",
    "Subject": "CALVIN JOHNSON",
    "CardNumber": "107",
    "Category": "Football Cards",
    "CardGrade": "9",
    "GradeDescription": "MINT 9",
    "Variety": "AUTOGRAPH-JERSEY",
}


def _client(tmp_path, handler, token="tok"):
    return PSAClient(
        token=token,
        cache_dir=tmp_path / "psa",
        http=httpx.Client(transport=httpx.MockTransport(handler)),
    )


def test_lookup_parses_and_caches(tmp_path):
    calls = []

    def handler(request):
        calls.append(str(request.url))
        assert request.headers["authorization"] == "bearer tok"
        return httpx.Response(200, json={"PSACert": RECORD})

    client = _client(tmp_path, handler)
    assert client.get_cert(CERT)["Subject"] == "CALVIN JOHNSON"
    assert client.get_cert(CERT)["Year"] == "2007"  # served from cache
    assert len(calls) == 1
    cached = json.loads((tmp_path / "psa" / f"{CERT}.json").read_text())
    assert cached["CertNumber"] == CERT


def test_cert_number_is_sanitized(tmp_path):
    def handler(request):
        assert request.url.path.endswith("/cert/GetByCertNumber/26987167")
        return httpx.Response(200, json={"PSACert": RECORD})

    assert _client(tmp_path, handler).get_cert(" 2698-7167 ") is not None


def test_unknown_cert_returns_none_and_caches(tmp_path):
    calls = []

    def handler(request):
        calls.append(1)
        return httpx.Response(404)

    client = _client(tmp_path, handler)
    assert client.get_cert("999") is None
    assert client.get_cert("999") is None
    assert len(calls) == 1  # negative result cached too


def test_empty_record_treated_as_unknown(tmp_path):
    client = _client(tmp_path, lambda r: httpx.Response(200, json={"PSACert": {"CertNumber": ""}}))
    assert client.get_cert("123") is None


def test_auth_error_raises(tmp_path):
    with pytest.raises(PSAError, match="token"):
        _client(tmp_path, lambda r: httpx.Response(401)).get_cert("123")


def test_rate_limit_raises(tmp_path):
    with pytest.raises(PSAError, match="rate limit"):
        _client(tmp_path, lambda r: httpx.Response(429)).get_cert("123")


def test_no_token_not_available_and_raises(tmp_path, monkeypatch):
    monkeypatch.delenv("PSA_API_TOKEN", raising=False)
    client = PSAClient(token="", cache_dir=tmp_path)
    assert not client.available
    with pytest.raises(PSAError, match="no PSA API token"):
        client.get_cert("123")


def test_garbage_cert_raises(tmp_path):
    with pytest.raises(PSAError, match="not a usable cert"):
        _client(tmp_path, lambda r: httpx.Response(200)).get_cert("---")
