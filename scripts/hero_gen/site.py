"""Facts about the site's hero banner, derived from static/style.css.

Geometry (root font 16px, body line-height 1.6):
    padding-top 1rem=16, nav line 17px*1.6=27.2, title margin-top 2.5rem=40,
    title 2.25rem=36px * 1.6 = 57.6 line box, padding-bottom 3rem=48, border 1
    => ~190 CSS px tall. Content column: max-width 42rem=672px, 16px side padding.
"""

from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent  # the site repo root
WORK = REPO / "hero-work"   # gitignored: raw generations, previews, cost log
STATIC = REPO / "static"

ROOT_PX = 16
BODY_PX = 17  # 1.0625rem
LINE_HEIGHT = 1.6
PAD_TOP = 16
PAD_BOTTOM = 48
PAD_SIDE = 16
BORDER = 1
NAV_PX = BODY_PX
NAV_LINE = NAV_PX * LINE_HEIGHT
TITLE_MARGIN = 40
TITLE_PX = 36
TITLE_LINE = TITLE_PX * LINE_HEIGHT
MEASURE = 672

HERO_HEIGHT = round(PAD_TOP + NAV_LINE + TITLE_MARGIN + TITLE_LINE + PAD_BOTTOM + BORDER)

# Hero colors per mode: (fg, fallback bg). Must equal --hero-fg / --hero-bg in
# static/style.css (tests/test_hero_gen.py checks).
MODES = {
    "dark": {"fg": "#E6B450", "bg": "#131721"},
    "light": {"fg": "#8F5000", "bg": "#F3F4F5"},
}

# AA thresholds: nav is normal text (4.5), title is large text (3.0).
AA_NORMAL = 4.5
AA_LARGE = 3.0

# Ayu palette (dark + light accents) for prompt colour guidance.
AYU = {
    "dark_bg": "#0D1017",
    "dark_raised": "#131721",
    "orange": "#E6B450",
    "deep_orange": "#FFAA33",
    "blue": "#59C2FF",
    "fg": "#BFBDB6",
    "muted": "#8A9199",
    "light_bg": "#F3F4F5",
    "dark_orange": "#8F5000",
}

# Viewport widths to preview (CSS px): phone, tablet, laptop, desktop, wide.
VIEWPORTS = {"phone": 390, "tablet": 768, "laptop": 1366, "desktop": 1920, "wide": 2560}


@dataclass(frozen=True)
class Box:
    x0: float
    y0: float
    x1: float
    y1: float

    @property
    def w(self) -> float:
        return self.x1 - self.x0

    @property
    def h(self) -> float:
        return self.y1 - self.y0

    def scaled(self, s: float) -> "Box":
        return Box(self.x0 * s, self.y0 * s, self.x1 * s, self.y1 * s)


def column(viewport_w: float) -> Box:
    """The centered content column (nav + title live here), in CSS px."""
    inner = viewport_w - 2 * PAD_SIDE
    w = min(MEASURE, inner)
    x0 = (viewport_w - w) / 2
    return Box(x0, 0, x0 + w, HERO_HEIGHT)


def nav_box(viewport_w: float, text_w: float = 190) -> Box:
    """Approximate box of the nav links ("Home Posts About", 600 weight)."""
    c = column(viewport_w)
    return Box(c.x0, PAD_TOP, c.x0 + min(text_w, c.w), PAD_TOP + NAV_LINE)


# Average advance of a 36px bold system-ui glyph, as a fraction of the font
# size: "Jef Wagner" measured ~215px (0.6em per character).
TITLE_EM_PER_CHAR = 0.6


def title_box(viewport_w: float, text_w: float | None = None) -> Box:
    """Approximate box of the hero title glyphs (36px bold); width estimated
    from the configured hero title unless given."""
    if text_w is None:
        text_w = len(hero_title()) * TITLE_EM_PER_CHAR * TITLE_PX
    c = column(viewport_w)
    y0 = PAD_TOP + NAV_LINE + TITLE_MARGIN
    # glyphs occupy roughly the middle of the 57.6px line box
    pad = (TITLE_LINE - TITLE_PX * 1.1) / 2
    return Box(c.x0, y0 + pad, c.x0 + min(text_w, c.w), y0 + TITLE_LINE - pad)


def hero_title() -> str:
    """The hero title as displayed: config [extra] hero_title (else title),
    with inline-markdown emphasis markers removed."""
    config = tomllib.loads((REPO / "config.toml").read_text(encoding="utf-8"))
    title = config.get("extra", {}).get("hero_title") or config.get("title", "")
    return re.sub(r"[*_]", "", title)


def read_front_matter(path: str | Path) -> dict:
    """Parse a Zola post's TOML front matter (between +++ fences). Read-only."""
    text = Path(path).read_text(encoding="utf-8")
    if not text.startswith("+++"):
        raise ValueError(f"no TOML front matter in {path}")
    _, fm, _ = text.split("+++", 2)
    return tomllib.loads(fm)


def list_posts() -> dict[str, Path]:
    """Map post slug -> index.md / .md path under content/posts."""
    posts = {}
    base = REPO / "content" / "posts"
    for p in sorted(base.rglob("*.md")):
        if p.name == "_index.md":
            continue
        slug = p.parent.name if p.name == "index.md" else p.stem
        posts[slug] = p
    return posts
