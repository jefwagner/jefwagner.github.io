"""Prompt building: a site-style preamble + a subject + composition rules.

STATUS: every prompt text in this module is a DRAFT awaiting jef's approval.
Style traits are described rather than naming any specific comic/show.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from . import site

DRAFT = "draft — awaiting jef's approval"

STYLE = (
    "Wide panoramic illustration in a ligne-claire comic style: clean, even-weight "
    "dark outlines, flat colour fills, minimal shading, no gradients or photographic "
    "texture. Gentle storybook / Scandinavian-folk feel. A clearly staged, "
    "diorama-like scene full of tiny characters going about their day, small "
    "vignettes of activity everywhere, like a busy picture book."
)

# v1: busy at the far edges, calm centre. Round 1 showed phones then see only
# empty sky, and tablet/laptop text columns reach into the busy edges.
COMPOSITION_V1 = (
    "Composition: extremely wide landscape banner. Put all the busy detail along "
    "the bottom third and towards the far left and right ends. Keep the upper and "
    "central area calm and simple: open sky with very little detail, so text can "
    "be laid over the middle. Horizon low in the frame. No text, letters, logos, "
    "signs with writing, borders or frames."
)

# v2: the strip below the title is free at every viewport width, so run a
# thin band of activity along the very bottom across the whole width; keep the
# dense clusters in the outer fifths; keep the middle 60% of the upper
# three-quarters plain.
COMPOSITION = (
    "Composition: extremely wide, flat landscape banner seen from the side. "
    "A low horizon near the bottom: a thin, continuous strip of tiny characters "
    "and small vehicles runs along the very bottom edge across the entire width, "
    "including the middle. Taller, denser clusters of buildings only in the "
    "outer fifth at each end. Everything above that bottom strip in the middle "
    "three-fifths of the image is plain, empty sky with no objects at all, so "
    "text can be laid over it. No text, letters, logos, signs with writing, "
    "borders or frames."
)

PALETTE = {
    "night": (
        "Night-time palette: deep blue-black sky (#0D1017 to #131721), muted slate "
        "blues, warm amber and orange window lights (#E6B450, #FFAA33) and a few "
        "soft cyan accents (#59C2FF). The sky behind the centre must stay very "
        "dark and plain."
    ),
    "day": (
        "Daytime palette: very pale, airy sky (near-white #F3F4F5 to pale cream), "
        "soft pastel greens and blues, warm ochre and orange accents. The sky behind "
        "the centre must stay very light and plain."
    ),
}

THEMES = {
    "moonbase": (
        "A cheerful moonbase on a grey lunar plain: domes, greenhouse modules, "
        "little rovers, astronauts tending hydroponic gardens, a landing pad with a "
        "small rocket, kids bouncing in low gravity, cargo bots, Earth small in the sky."
    ),
    "solarpunk": (
        "A solarpunk hillside town: terraced gardens, timber-and-glass houses with "
        "solar roofs, wind turbines, a small tram, bicycles, market stalls, people "
        "repairing things, kites, greenery on every roof, a river with small boats."
    ),
    # Layered depth, after the mkdocs-material hero (foreground silhouettes,
    # small detailed city in the middle distance, fading hills behind).
    "solarpunk-valley": (
        "A distant solarpunk city in a wide valley, seen from a hillside: staged, "
        "diorama-like, full of tiny people, trams, gardens and wind turbines. "
        "Layered depth like a theatre set: dark silhouetted foliage and ferns frame "
        "the far left and right foreground, the detailed little city sits low and "
        "small in the middle distance along the bottom, mesas and hills fade behind it."
    ),
}


@dataclass
class Prompt:
    subject: str
    palette: str = "night"
    style: str = STYLE
    composition: str = COMPOSITION
    extra: list[str] = field(default_factory=list)
    status: str = DRAFT

    def text(self) -> str:
        parts = [self.style, "Scene: " + self.subject, self.composition,
                 PALETTE.get(self.palette, self.palette), *self.extra]
        return "\n\n".join(p.strip() for p in parts if p)


def theme(name: str, palette: str = "night", **kw) -> Prompt:
    return Prompt(THEMES[name], palette=palette, **kw)


def from_post(path_or_slug, palette: str = "night", setting: str | None = None) -> Prompt:
    """Subject from a post's title + description (read-only), placed in a
    themed setting so banners stay on-style across posts."""
    posts = site.list_posts()
    path = posts.get(str(path_or_slug), path_or_slug)
    fm = site.read_front_matter(path)
    title = fm.get("title", "")
    desc = fm.get("description", "")
    subj = (f"An illustration evoking the blog post '{title}'"
            + (f" — {desc}" if desc else "") + ". Express the topic through the "
            "objects and activities in the scene, not through any text.")
    if setting:
        subj += " Setting: " + THEMES.get(setting, setting)
    return Prompt(subj, palette=palette)


def night_edit(palette: str = "night") -> str:
    """Edit instruction to turn a day banner into its night twin (same scene)."""
    return (
        "Redraw this exact same illustration at night. Keep the composition, "
        "buildings, characters and line style identical; only change the lighting "
        "and colours. " + PALETTE[palette] + " No text."
    )


def day_edit() -> str:
    return (
        "Redraw this exact same illustration in bright daytime. Keep the "
        "composition, buildings, characters and line style identical; only change "
        "the lighting and colours. " + PALETTE["day"] + " No text."
    )
