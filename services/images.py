import io

from PIL import Image, ImageOps, UnidentifiedImageError

AVATAR_SIZE = 400
MAX_PIXELS = 40_000_000  # guards against decompression bombs


class InvalidImage(Exception):
    pass


def make_avatar(data):
    """Center-crop and resize an uploaded image to a square WebP. Returns bytes."""
    Image.MAX_IMAGE_PIXELS = MAX_PIXELS
    try:
        with Image.open(io.BytesIO(data)) as img:
            img = ImageOps.exif_transpose(img)
            img = img.convert("RGBA" if img.mode in ("RGBA", "LA", "P") else "RGB")
            img = ImageOps.fit(img, (AVATAR_SIZE, AVATAR_SIZE), Image.Resampling.LANCZOS)
            out = io.BytesIO()
            img.save(out, format="WEBP", quality=85, method=4)
            return out.getvalue()
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError, ValueError) as exc:
        raise InvalidImage("Upload a JPG, PNG, WebP or GIF image.") from exc
