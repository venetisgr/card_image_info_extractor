"""FastAPI service exposing the Claude extraction engine (roadmap P1-1).

Run locally:
    uvicorn app.main:app --reload      (from backend/, with .env in place)
"""

import logging

import anthropic
from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from app.config import MAX_UPLOAD_BYTES, load_dotenv, resolve_model
from app.services.extractor import CardExtractor, ExtractionError
from app.services.images import ImageError, preprocess_image

logger = logging.getLogger("card_extractor")

load_dotenv()
app = FastAPI(
    title="Sports Card Info Extractor",
    description="Extracts structured CardInfo from card photos (front + back) via the Claude API.",
    version="0.1.0",
)

_extractor: CardExtractor | None = None


def get_extractor() -> CardExtractor:
    global _extractor
    if _extractor is None:
        _extractor = CardExtractor()
    return _extractor


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
    extractor: CardExtractor = Depends(get_extractor),
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

    logger.info("extracted card_type=%s usage=%s", result.card.card_type, result.usage.as_dict())
    return JSONResponse(result.card.model_dump(mode="json"))
