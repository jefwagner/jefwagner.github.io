"""WCAG contrast — same definition as tests/check_site.py.

Relative luminance with the 0.03928 sRGB knee; contrast = (L1+.05)/(L2+.05).
Extended here to images: per-pixel contrast of a text colour against the
pixels behind a text box.
"""

from __future__ import annotations

import numpy as np
from PIL import Image

from . import site


def hex_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _linear(c: np.ndarray) -> np.ndarray:
    c = np.asarray(c, dtype=float) / 255.0
    return np.where(c <= 0.03928, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def luminance(color) -> float | np.ndarray:
    """Relative luminance of a hex string, an (r,g,b) tuple, or an HxWx3 array."""
    if isinstance(color, str):
        color = hex_rgb(color)
    a = _linear(np.asarray(color)[..., :3])
    lum = 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
    return float(lum) if lum.ndim == 0 else lum


def contrast(a, b) -> float | np.ndarray:
    la, lb = luminance(a), luminance(b)
    hi, lo = np.maximum(la, lb), np.minimum(la, lb)
    r = (hi + 0.05) / (lo + 0.05)
    return float(r) if np.ndim(r) == 0 else r


def luminance_limits(fg: str, ratio: float) -> tuple[float, float]:
    """Background luminance ranges that reach `ratio` against fg.

    Returns (max_dark_bg_L, min_light_bg_L); either may be out of [0, 1],
    meaning that side is impossible.
    """
    lf = luminance(fg)
    return (lf + 0.05) / ratio - 0.05, ratio * (lf + 0.05) - 0.05


def region_stats(img: Image.Image, box: site.Box, fg: str, need: float) -> dict:
    """Contrast of `fg` against the pixels inside `box` (image pixel coords).

    Reports the 5th percentile (a robust 'worst case'), median, and the share
    of pixels meeting `need`. A text box passes when p05 >= need.
    """
    arr = np.asarray(img.convert("RGB"))
    x0, y0 = max(0, int(box.x0)), max(0, int(box.y0))
    x1, y1 = min(arr.shape[1], int(np.ceil(box.x1))), min(arr.shape[0], int(np.ceil(box.y1)))
    patch = arr[y0:y1, x0:x1]
    if patch.size == 0:
        raise ValueError("empty region")
    c = contrast(np.array(hex_rgb(fg)), patch)
    p05 = float(np.percentile(c, 5))
    return {
        "p05": round(p05, 2),
        "median": round(float(np.median(c)), 2),
        "pass_share": round(float((c >= need).mean()), 3),
        "need": need,
        "ok": p05 >= need,
    }


def text_stats(img_css: Image.Image, mode: str) -> dict:
    """Contrast for nav (4.5) and title (3.0) on a banner already rendered at
    CSS-pixel scale for one viewport (see crop.cover_view)."""
    fg = site.MODES[mode]["fg"]
    w = img_css.width
    s = img_css.height / site.HERO_HEIGHT  # allow 2x renders
    nav = region_stats(img_css, site.nav_box(w / s).scaled(s), fg, site.AA_NORMAL)
    title = region_stats(img_css, site.title_box(w / s).scaled(s), fg, site.AA_LARGE)
    return {"nav": nav, "title": title, "ok": nav["ok"] and title["ok"]}


def tone_zone(img: Image.Image, mode: str, box: site.Box, *, feather: float = 40,
              target_ratio: float = site.AA_NORMAL, margin: float = 1.08) -> Image.Image:
    """Post-process: darken (dark mode) or lighten (light mode) a feathered zone
    around `box` just enough that the text colour reaches target_ratio.

    Scales luminance multiplicatively (dark) or blends toward white (light), so
    hue is kept. `box` is in the image's pixel coords. Returns a new image.
    """
    fg = site.MODES[mode]["fg"]
    lo_max, hi_min = luminance_limits(fg, target_ratio * margin)
    arr = np.asarray(img.convert("RGB")).astype(float)
    h, w = arr.shape[:2]
    lum = luminance(arr)

    yy, xx = np.mgrid[0:h, 0:w]
    dx = np.maximum(np.maximum(box.x0 - xx, xx - box.x1), 0)
    dy = np.maximum(np.maximum(box.y0 - yy, yy - box.y1), 0)
    d = np.hypot(dx, dy)
    mask = np.clip(1 - d / max(feather, 1e-6), 0, 1)
    mask = mask * mask * (3 - 2 * mask)  # smoothstep

    if mode == "dark":
        # scale linear-light colour so luminance <= lo_max
        k = np.where(lum > lo_max, lo_max / np.maximum(lum, 1e-6), 1.0)
        lin = _linear(arr) * k[..., None]
        out = _encode(lin)
    else:
        # blend toward white until luminance >= hi_min
        t = np.where(lum < hi_min, (hi_min - lum) / np.maximum(1 - lum, 1e-6), 0.0)
        lin = _linear(arr)
        lin = lin + (1 - lin) * t[..., None]
        out = _encode(lin)
    res = arr * (1 - mask[..., None]) + out * mask[..., None]
    return Image.fromarray(np.clip(res, 0, 255).astype(np.uint8))


def _encode(lin: np.ndarray) -> np.ndarray:
    lin = np.clip(lin, 0, 1)
    c = np.where(lin <= 0.0030402, lin * 12.92, 1.055 * lin ** (1 / 2.4) - 0.055)
    return c * 255.0
