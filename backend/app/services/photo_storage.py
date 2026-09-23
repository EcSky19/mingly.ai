"""
Handles saving uploaded profile photos to local disk: validates the
file is a genuine decodable image, resizes it down to a reasonable max
dimension, strips EXIF metadata (privacy - phone photos often embed
GPS coordinates), and re-saves as JPEG for consistent storage.

Files live under UPLOADS_DIR, which is inside the backend/ directory -
this is bind-mounted to the host via the existing ./backend:/app Docker
volume (see root docker-compose.yml), so uploaded files survive
container rebuilds without needing a separate Docker volume.
"""
import io
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError

UPLOADS_DIR = Path(__file__).resolve().parent.parent.parent / "uploads" / "photos"
MAX_FILE_SIZE_BYTES = 8 * 1024 * 1024  # 8MB - generous for phone photos
MAX_DIMENSION = 1600  # longest side, px - keeps storage/bandwidth reasonable
JPEG_QUALITY = 85


async def save_uploaded_photo(user_id: str, file: UploadFile) -> str:
    """Validates, processes, and saves an uploaded photo. Returns the
    relative file path (relative to UPLOADS_DIR's parent) to store in
    the database. Raises HTTPException on any validation failure."""
    raw_bytes = await file.read()

    if len(raw_bytes) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=400, detail="Photo is too large (max 8MB)")
    if len(raw_bytes) == 0:
        raise HTTPException(status_code=400, detail="Empty file")

    try:
        image = Image.open(io.BytesIO(raw_bytes))
        image.verify()  # confirms it's a genuinely decodable image, not just a renamed file
        # verify() leaves the image unusable for further processing, so re-open
        image = Image.open(io.BytesIO(raw_bytes))
    except (UnidentifiedImageError, OSError):
        raise HTTPException(status_code=400, detail="File is not a valid image")

    # Convert to RGB (handles PNG transparency, CMYK, etc.) before saving as JPEG
    if image.mode != "RGB":
        image = image.convert("RGB")

    # Resize down if larger than MAX_DIMENSION on the longest side - never upscale
    if max(image.size) > MAX_DIMENSION:
        image.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.LANCZOS)

    user_dir = UPLOADS_DIR / user_id
    user_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid.uuid4()}.jpg"
    file_path = user_dir / filename

    # PIL's save() with a fresh Image object (no exif= kwarg passed) does
    # not carry over the original EXIF block, which strips GPS/location
    # metadata some phones embed - a real privacy benefit, not just a
    # storage optimization.
    image.save(file_path, format="JPEG", quality=JPEG_QUALITY)

    return f"photos/{user_id}/{filename}"


def delete_photo_file(relative_path: str) -> None:
    """Removes a photo file from disk. Safe to call even if the file is
    already gone (e.g. manual cleanup happened) - fails open rather than
    raising, since a missing file shouldn't block deleting the DB row."""
    full_path = UPLOADS_DIR.parent / relative_path
    try:
        full_path.unlink(missing_ok=True)
    except OSError:
        pass
