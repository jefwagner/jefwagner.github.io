"""`background-size: cover; background-position: center` maths."""

from __future__ import annotations

from PIL import Image

from . import site


def cover_box(img_w: int, img_h: int, view_w: float, view_h: float) -> site.Box:
    """Region of the source image (image px) visible in a view_w x view_h box
    under `cover` + centered positioning."""
    s = max(view_w / img_w, view_h / img_h)  # scale image so it covers the box
    vis_w, vis_h = view_w / s, view_h / s
    x0 = (img_w - vis_w) / 2
    y0 = (img_h - vis_h) / 2
    return site.Box(x0, y0, x0 + vis_w, y0 + vis_h)


def cover_view(img: Image.Image, view_w: int, view_h: int = site.HERO_HEIGHT,
               scale: float = 1.0) -> Image.Image:
    """Render what the browser shows at a viewport width (optionally at 2x)."""
    b = cover_box(img.width, img.height, view_w, view_h)
    out = (round(view_w * scale), round(view_h * scale))
    box = (max(0.0, b.x0), max(0.0, b.y0), min(img.width, b.x1), min(img.height, b.y1))
    return img.resize(out, Image.LANCZOS, box=box)


def always_visible(img_w: int, img_h: int, widths=None) -> site.Box:
    """Intersection of the visible regions across viewport widths: the part of
    the image every visitor sees."""
    widths = widths or list(site.VIEWPORTS.values())
    boxes = [cover_box(img_w, img_h, w, site.HERO_HEIGHT) for w in widths]
    return site.Box(max(b.x0 for b in boxes), max(b.y0 for b in boxes),
                    min(b.x1 for b in boxes), min(b.y1 for b in boxes))


def center_crop(img: Image.Image, aspect: float, *, y_center: float = 0.5) -> Image.Image:
    """Crop to width/height == aspect. y_center (0..1) picks the vertical band
    when cropping height, e.g. 0.4 keeps more sky."""
    w, h = img.size
    if w / h > aspect:  # too wide: trim sides
        nw = round(h * aspect)
        x0 = (w - nw) // 2
        return img.crop((x0, 0, x0 + nw, h))
    nh = round(w / aspect)
    y0 = round((h - nh) * y_center)
    y0 = min(max(y0, 0), h - nh)
    return img.crop((0, y0, w, y0 + nh))


def fit_width(img: Image.Image, width: int) -> Image.Image:
    """Resize to `width`, keeping aspect (never upsamples)."""
    if img.width <= width:
        return img.copy()
    h = round(img.height * width / img.width)
    return img.resize((width, h), Image.LANCZOS)


def text_zone(img_w: int, img_h: int, widths=None, pad: float = 24) -> site.Box:
    """Union, in source-image px, of where the nav + title land across the
    viewport widths — the zone that must stay calm/readable."""
    widths = widths or list(site.VIEWPORTS.values())
    xs0, ys0, xs1, ys1 = [], [], [], []
    for w in widths:
        vb = cover_box(img_w, img_h, w, site.HERO_HEIGHT)
        s = vb.w / w  # image px per CSS px
        for tb in (site.nav_box(w), site.title_box(w)):
            xs0.append(vb.x0 + (tb.x0 - pad) * s)
            ys0.append(vb.y0 + (tb.y0 - pad / 2) * s)
            xs1.append(vb.x0 + (tb.x1 + pad) * s)
            ys1.append(vb.y0 + (tb.y1 + pad / 2) * s)
    return site.Box(max(0, min(xs0)), max(0, min(ys0)),
                    min(img_w, max(xs1)), min(img_h, max(ys1)))
