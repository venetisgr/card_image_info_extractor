"""Image preprocessing tests (P1-2): orientation, resize, format, metadata strip."""

import io

import pytest
from PIL import Image

from app.config import MAX_IMAGE_LONG_EDGE
from app.services.images import ImageError, preprocess_image


def _png_bytes(size=(100, 60), mode="RGB", color=(200, 30, 30), exif_orientation=None) -> bytes:
    img = Image.new(mode, size, color)
    buf = io.BytesIO()
    if exif_orientation:
        exif = img.getexif()
        exif[0x0112] = exif_orientation
        img.save(buf, format="JPEG", exif=exif)
    else:
        img.save(buf, format="PNG")
    return buf.getvalue()


def test_reencodes_to_jpeg_with_hash():
    out = preprocess_image(_png_bytes())
    assert out.media_type == "image/jpeg"
    assert out.source_ref.startswith("sha256:")
    assert Image.open(io.BytesIO(out.data)).format == "JPEG"


def test_downscales_long_edge():
    out = preprocess_image(_png_bytes(size=(4000, 1000)))
    assert max(out.width, out.height) == MAX_IMAGE_LONG_EDGE
    assert out.height == round(1000 * MAX_IMAGE_LONG_EDGE / 4000)


def test_small_images_not_upscaled():
    out = preprocess_image(_png_bytes(size=(100, 60)))
    assert (out.width, out.height) == (100, 60)


def test_exif_orientation_applied():
    # Orientation 6 = rotate 90° CW on view; pixels must be transposed.
    out = preprocess_image(_png_bytes(size=(100, 60), exif_orientation=6))
    assert (out.width, out.height) == (60, 100)


def test_alpha_converted_to_rgb():
    out = preprocess_image(_png_bytes(mode="RGBA", color=(10, 20, 30, 128)))
    assert Image.open(io.BytesIO(out.data)).mode == "RGB"


def test_garbage_raises_image_error():
    with pytest.raises(ImageError):
        preprocess_image(b"definitely not an image")
