"""Web export: crop to the banner shape, resize, compress, report sizes."""

from __future__ import annotations

import io
from pathlib import Path

from PIL import Image

from . import crop
from .site import STATIC

EXPORT = STATIC / "img"

# Default banner file shape, from the first exploration: 8:1 at 2880px wide
# (360px tall, enough for 2x screens at the ~190 CSS px hero). Matches the
# native 8:1 output of the Gemini image models; desktop crops little, a phone
# shows the centre ~quarter (the bottom activity strip carries it). Use 6:1
# for 4:1 / 3:1 sources to keep more of their height.
DEFAULT_ASPECT = 8.0
DEFAULT_WIDTH = 2880


def encode(img: Image.Image, fmt: str, **opts) -> bytes:
    buf = io.BytesIO()
    img = img.convert("RGB")
    if fmt == "webp":
        img.save(buf, "WEBP", quality=opts.get("quality", 80), method=6)
    elif fmt == "jpeg":
        img.save(buf, "JPEG", quality=opts.get("quality", 82), optimize=True,
                 progressive=True)
    elif fmt == "png":
        colors = opts.get("colors")  # quantize: flat ligne-claire art compresses well
        if colors:
            img = img.quantize(colors=colors, method=Image.Quantize.MEDIANCUT,
                               dither=Image.Dither.NONE)
        img.save(buf, "PNG", optimize=True)
    else:
        raise ValueError(fmt)
    return buf.getvalue()


def prepare(img: Image.Image, aspect: float = DEFAULT_ASPECT, width: int = DEFAULT_WIDTH,
            y_center: float = 0.5) -> Image.Image:
    return crop.fit_width(crop.center_crop(img, aspect, y_center=y_center), width)


def compare_formats(img: Image.Image) -> list[dict]:
    """Sizes of common encodings for an already-prepared banner."""
    trials = [("webp", {"quality": 75}), ("webp", {"quality": 85}),
              ("jpeg", {"quality": 80}), ("png", {}), ("png", {"colors": 64}),
              ("png", {"colors": 128})]
    out = []
    for fmt, o in trials:
        out.append({"format": fmt, **o, "kb": round(len(encode(img, fmt, **o)) / 1024, 1)})
    return out


def save(img: Image.Image, name: str, fmt: str = "webp", *, overwrite: bool = False,
         directory: Path | None = None, **opts) -> tuple[Path, str]:
    """Write static/img/<name>.<ext>; return (path, front-matter line).

    Never overwrites unless asked: an existing name gets -2, -3, ... appended.
    """
    ext = {"jpeg": "jpg"}.get(fmt, fmt)
    directory = directory or EXPORT
    directory.mkdir(parents=True, exist_ok=True)
    p = directory / f"{name}.{ext}"
    i = 2
    while p.exists() and not overwrite:
        p = directory / f"{name}-{i}.{ext}"
        i += 1
    p.write_bytes(encode(img, fmt, **opts))
    line = f'hero_image = "img/{p.name}"'
    return p, line
