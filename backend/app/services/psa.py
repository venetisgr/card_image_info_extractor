"""PSA public API client — graded-card cert verification (roadmap P2-1).

GET {PSA_API_BASE}/cert/GetByCertNumber/{cert} with a bearer token returns the
authoritative record PSA holds for a slab. Responses are cached on disk
because the free tier allows only ~100 calls/day.
"""

import json
import os
import re
from pathlib import Path

import httpx

from app.config import PSA_API_BASE, PSA_CACHE_DIR, PSA_TOKEN_ENV


class PSAError(RuntimeError):
    """The PSA API could not be queried (auth, network, or server error)."""


def _clean_cert(cert_number: str) -> str:
    cleaned = re.sub(r"[^0-9A-Za-z]", "", cert_number or "")
    if not cleaned:
        raise PSAError(f"not a usable cert number: {cert_number!r}")
    return cleaned


class PSAClient:
    """Cert lookups against the PSA public API, with an on-disk cache."""

    def __init__(
        self,
        token: str | None = None,
        cache_dir: Path | None = None,
        http: httpx.Client | None = None,
    ):
        self._token = token if token is not None else os.environ.get(PSA_TOKEN_ENV)
        self._cache_dir = cache_dir or PSA_CACHE_DIR
        self._http = http or httpx.Client(timeout=20.0)

    @property
    def available(self) -> bool:
        """True when a token is configured (enrichment silently skips otherwise)."""
        return bool(self._token)

    def get_cert(self, cert_number: str) -> dict | None:
        """Return PSA's record for a cert (the `PSACert` object), or None if unknown.

        Raises PSAError for auth/network/server problems so callers can
        distinguish "PSA says no such cert" (None) from "couldn't ask PSA".
        """
        cert = _clean_cert(cert_number)

        cached = self._cache_read(cert)
        if cached is not None:
            return cached or None  # {} sentinel caches a definitive "not found"

        if not self.available:
            raise PSAError(f"no PSA API token configured (set {PSA_TOKEN_ENV})")

        try:
            response = self._http.get(
                f"{PSA_API_BASE}/cert/GetByCertNumber/{cert}",
                headers={"authorization": f"bearer {self._token}"},
            )
        except httpx.HTTPError as exc:
            raise PSAError(f"PSA API unreachable: {exc}") from exc

        if response.status_code in (401, 403):
            raise PSAError("PSA API rejected the token (check PSA_API_TOKEN)")
        if response.status_code == 429:
            raise PSAError("PSA API rate limit reached (free tier is ~100 calls/day)")
        if response.status_code == 404:
            self._cache_write(cert, {})
            return None
        if response.status_code != 200:
            raise PSAError(f"PSA API error {response.status_code}")

        payload = response.json()
        record = payload.get("PSACert") if isinstance(payload, dict) else None
        # A cert PSA doesn't know can also come back as 200 with an empty record.
        if not record or not str(record.get("CertNumber") or "").strip():
            self._cache_write(cert, {})
            return None
        self._cache_write(cert, record)
        return record

    # -- cache -------------------------------------------------------------

    def _cache_path(self, cert: str) -> Path:
        return self._cache_dir / f"{cert}.json"

    def _cache_read(self, cert: str) -> dict | None:
        path = self._cache_path(cert)
        if not path.is_file():
            return None
        try:
            return json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            return None

    def _cache_write(self, cert: str, record: dict) -> None:
        try:
            self._cache_dir.mkdir(parents=True, exist_ok=True)
            self._cache_path(cert).write_text(json.dumps(record, indent=2))
        except OSError:
            pass  # cache is best-effort
