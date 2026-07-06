"""Image preprocessing (roadmap P1-2).

Normalizes any uploaded card photo into what the Claude vision API wants:
EXIF orientation applied, RGB, long edge capped at the model's native
resolution, re-encoded as JPEG (which also strips EXIF/GPS metadata).
"""

import hashlib
import io
from dataclasses import dataclass

from PIL import Image, ImageOps

from app.config import JPEG_QUALITY, MAX_IMAGE_LONG_EDGE


class ImageError(ValueError):
    """Raised when an upload cannot be decoded as an image."""


@dataclass(frozen=True)
class ProcessedImage:
    data: bytes
    media_type: str
    sha256: str
    width: int
    height: int

    @property
    def source_ref(self) -> str:
        """Reference stored in CardInfo.provenance.source_images."""
        return f"sha256:{self.sha256}"


def preprocess_image(raw: bytes) -> ProcessedImage:
    """Decode, orient, downscale and re-encode an uploaded image as JPEG."""
    try:
        img = Image.open(io.BytesIO(raw))
        img.load()
    except Exception as exc:
        raise ImageError(f"could not decode image: {exc}") from exc

    # Apply the EXIF orientation tag so the pixels match how the photo was shot.
    img = ImageOps.exif_transpose(img)

    if img.mode != "RGB":
        img = img.convert("RGB")

    long_edge = max(img.size)
    if long_edge > MAX_IMAGE_LONG_EDGE:
        scale = MAX_IMAGE_LONG_EDGE / long_edge
        new_size = (max(1, round(img.width * scale)), max(1, round(img.height * scale)))
        img = img.resize(new_size, Image.LANCZOS)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=JPEG_QUALITY, optimize=True)
    data = buf.getvalue()
    return ProcessedImage(
        data=data,
        media_type="image/jpeg",
        sha256=hashlib.sha256(data).hexdigest(),
        width=img.width,
        height=img.height,
    )
