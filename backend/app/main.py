"""FastAPI service exposing the Claude extraction engine (roadmap P1-1).

Run locally:
    uvicorn app.main:app --reload      (from backend/, with .env in place)
"""

import logging

import anthropic
from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from app.config import MAX_UPLOAD_BYTES, load_dotenv, resolve_model
from app.services.enrich import enrich_card
from app.services.extractor import CardExtractor, ExtractionError
from app.services.images import ImageError, preprocess_image
from app.services.normalize import normalize_card
from app.services.psa import PSAClient, PSAError

logger = logging.getLogger("card_extractor")

load_dotenv()
app = FastAPI(
    title="Sports Card Info Extractor",
    description="Extracts structured CardInfo from card photos (front + back) via the Claude API.",
    version="0.1.0",
)

_extractor: CardExtractor | None = None
_psa_client: PSAClient | None = None


def get_extractor() -> CardExtractor:
    global _extractor
    if _extractor is None:
        _extractor = CardExtractor()
    return _extractor


def get_psa_client() -> PSAClient:
    global _psa_client
    if _psa_client is None:
        _psa_client = PSAClient()
    return _psa_client


async def _read_image(upload: UploadFile, name: str):
    raw = await upload.read()
    if len(raw) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, f"{name} image exceeds {MAX_UPLOAD_BYTES // (1024 * 1024)} MB")
    try:
        return preprocess_image(raw)
    except ImageError as exc:
        raise HTTPException(422, f"{name} image: {exc}") from exc


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok"}


@app.post("/extract")
async def extract(
    front: UploadFile = File(..., description="Photo of the card front (required)"),
    back: UploadFile | None = File(None, description="Photo of the card back (optional)"),
    model: str | None = Form(None, description="Model tier alias (opus/sonnet/haiku) or model id"),
    enrich: bool = Form(True, description="Verify graded PSA cards via the PSA public API"),
    extractor: CardExtractor = Depends(get_extractor),
    psa_client: PSAClient = Depends(get_psa_client),
) -> JSONResponse:
    front_img = await _read_image(front, "front")
    back_img = await _read_image(back, "back") if back is not None else None
    model_id = resolve_model(model)

    try:
        result = extractor.extract(front_img, back_img, model=model_id)
    except anthropic.AuthenticationError as exc:
        raise HTTPException(502, f"Claude API authentication failed: {exc.message}") from exc
    except anthropic.RateLimitError as exc:
        raise HTTPException(429, "Claude API rate limit hit; retry later") from exc
    except anthropic.APIStatusError as exc:
        raise HTTPException(502, f"Claude API error ({exc.status_code})") from exc
    except anthropic.APIConnectionError as exc:
        raise HTTPException(502, "could not reach the Claude API") from exc
    except ExtractionError as exc:
        raise HTTPException(502, f"extraction failed: {exc}") from exc

    card = result.card
    if enrich:
        card, outcome = enrich_card(card, psa_client)
        if outcome.attempted:
            logger.info("psa enrichment: %s (changed=%s)", outcome.note, outcome.changed_fields)
    card, normalized = normalize_card(card)
    if normalized:
        logger.info("normalized fields: %s", normalized)

    logger.info("extracted card_type=%s usage=%s", card.card_type, result.usage.as_dict())
    return JSONResponse(card.model_dump(mode="json"))


@app.get("/verify/psa/{cert_number}")
def verify_psa(cert_number: str, psa_client: PSAClient = Depends(get_psa_client)) -> JSONResponse:
    """Standalone cert lookup: returns PSA's record for a slab."""
    if not psa_client.available:
        raise HTTPException(503, "PSA_API_TOKEN not configured on the server")
    try:
        record = psa_client.get_cert(cert_number)
    except PSAError as exc:
        raise HTTPException(502, str(exc)) from exc
    if record is None:
        raise HTTPException(404, f"PSA has no record for cert {cert_number}")
    return JSONResponse(record)
