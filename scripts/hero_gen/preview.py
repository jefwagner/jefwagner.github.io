"""Render banners as the site would: cover-cropped per viewport, with the nav
and title drawn on top in each mode's --hero-fg. Fonts are approximations
(Pillow's built-in scalable font, not the visitor's system-ui)."""

from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont

from . import contrast, crop, site


def _font(px: float):
    try:
        return ImageFont.load_default(size=px)
    except TypeError:  # very old Pillow / no FreeType
        return ImageFont.load_default()


def render(img: Image.Image, view_w: int, mode: str, scale: float = 1.0,
           title: str | None = None) -> Image.Image:
    """Banner at one viewport width/mode with text overlaid."""
    view = crop.cover_view(img, view_w, scale=scale).convert("RGB")
    d = ImageDraw.Draw(view)
    fg = contrast.hex_rgb(site.MODES[mode]["fg"])
    nav = site.nav_box(view_w).scaled(scale)
    x = nav.x0
    f = _font(site.NAV_PX * scale)
    for word in ("Home", "Posts", "About"):
        d.text((x, nav.y0 + 4 * scale), word, fill=fg, font=f, stroke_width=0)
        x += d.textlength(word, font=f) + 20 * scale
    t = site.title_box(view_w).scaled(scale)
    d.text((t.x0, t.y0 - 2 * scale), title or site.hero_title(), fill=fg,
           font=_font(site.TITLE_PX * scale), stroke_width=round(0.6 * scale), stroke_fill=fg)
    return view


def sheet(img: Image.Image, modes=("dark", "light"), widths=None, scale: float = 0.5,
          gap: int = 8, with_stats: bool = True) -> tuple[Image.Image, dict]:
    """Contact sheet: one row per (mode, viewport). Returns (image, stats).

    Rows are drawn at `scale` to keep it compact; stats are computed at 1x.
    """
    widths = widths or site.VIEWPORTS
    if not isinstance(widths, dict):
        widths = {str(w): w for w in widths}
    rows, stats = [], {}
    for mode in modes:
        for name, w in widths.items():
            if with_stats:
                stats[(mode, name)] = contrast.text_stats(crop.cover_view(img, w), mode)
            rows.append(render(img, w, mode, scale=scale))
    W = max(r.width for r in rows)
    H = sum(r.height for r in rows) + gap * (len(rows) - 1)
    out = Image.new("RGB", (W, H), (40, 40, 40))
    y = 0
    for r in rows:
        out.paste(r, (0, y))
        y += r.height + gap
    return out, stats


def stats_table(stats: dict) -> str:
    """Plain-text table of sheet() stats."""
    lines = [f"{'mode':5} {'view':8} {'nav p05':>8} {'title p05':>9}  ok"]
    for (mode, name), s in stats.items():
        lines.append(f"{mode:5} {name:8} {s['nav']['p05']:8.2f} {s['title']['p05']:9.2f}  "
                     f"{'yes' if s['ok'] else 'NO'}")
    return "\n".join(lines)


def zones(img: Image.Image) -> Image.Image:
    """Source image annotated with the always-visible region (green) and the
    text zone across viewports (orange)."""
    out = img.convert("RGB").copy()
    d = ImageDraw.Draw(out)
    lw = max(2, img.width // 400)
    av = crop.always_visible(img.width, img.height)
    tz = crop.text_zone(img.width, img.height)
    for w in site.VIEWPORTS.values():  # each viewport's visible region (blue)
        b = crop.cover_box(img.width, img.height, w, site.HERO_HEIGHT)
        d.rectangle((b.x0, b.y0, b.x1, b.y1), outline=(89, 194, 255), width=max(1, lw // 2))
    d.rectangle((av.x0, av.y0, av.x1, av.y1), outline=(80, 220, 120), width=lw)
    d.rectangle((tz.x0, tz.y0, tz.x1, tz.y1), outline=(230, 180, 80), width=lw)
    return out


def compare(images, labels=None, width: int = 1600, gap: int = 6) -> Image.Image:
    """Stack images (PIL or paths) at a common width with small labels."""
    rows = []
    for i, im in enumerate(images):
        if not isinstance(im, Image.Image):
            im = Image.open(im)
        im = im.convert("RGB")
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
        if labels:
            ImageDraw.Draw(im).text((8, 8), str(labels[i]), fill=(255, 0, 255), font=_font(16))
        rows.append(im)
    out = Image.new("RGB", (width, sum(r.height for r in rows) + gap * (len(rows) - 1)),
                    (255, 255, 255))
    y = 0
    for r in rows:
        out.paste(r, (0, y))
        y += r.height + gap
    return out


def worst(stats: dict) -> str:
    """One-line summary of sheet() stats: min nav/title p05 and failing views."""
    nav = min(s["nav"]["p05"] for s in stats.values())
    tit = min(s["title"]["p05"] for s in stats.values())
    bad = [f"{m}/{v}" for (m, v), s in stats.items() if not s["ok"]]
    return f"min nav {nav:.2f}  min title {tit:.2f}  fails: {', '.join(bad) or 'none'}"
