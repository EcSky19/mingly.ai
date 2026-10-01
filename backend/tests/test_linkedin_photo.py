"""
Tests for save_linkedin_photo - see app/services/photo_storage.py for
the full design reasoning (LinkedIn's photo URL is time-limited and
expires about a week after issuance, confirmed against real stored
production URLs, so we download and keep our own permanent copy
instead of storing the URL directly).

These tests avoid depending on real network access to LinkedIn's CDN
(not available in CI/sandboxed environments, and shouldn't be a test
suite dependency regardless) - the fail-open path is tested against a
genuinely unreachable local address, and the core image processing is
tested directly against raw bytes. The real download-from-a-live-URL
path was manually verified against an allowed-domain image during
development (see commit message).
"""
import io
import shutil

import pytest
from PIL import Image

from app.services.photo_storage import save_linkedin_photo, _process_image, LINKEDIN_PHOTOS_DIR


@pytest.fixture(scope="module", autouse=True)
def cleanup_test_files():
    yield
    if LINKEDIN_PHOTOS_DIR.exists():
        shutil.rmtree(LINKEDIN_PHOTOS_DIR)


def _test_image_bytes() -> bytes:
    img = Image.new("RGB", (50, 50), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def test_process_image_handles_valid_bytes():
    image = _process_image(_test_image_bytes())
    assert image.mode == "RGB"


def test_process_image_rejects_invalid_bytes():
    with pytest.raises((Exception,)):
        _process_image(b"this is not an image")


@pytest.mark.asyncio
async def test_save_linkedin_photo_fails_open_on_unreachable_url():
    """A network failure should never raise - login must not break
    just because a photo download hiccupped."""
    result = await save_linkedin_photo("test-user-fail", "http://127.0.0.1:1/unreachable.jpg")
    assert result is None


@pytest.mark.asyncio
async def test_save_linkedin_photo_fails_open_on_invalid_scheme():
    """Same fail-open guarantee for a malformed URL, not just a
    connection failure - both should return None, never raise."""
    result = await save_linkedin_photo("test-user-bad-url", "not-a-valid-url-at-all")
    assert result is None
