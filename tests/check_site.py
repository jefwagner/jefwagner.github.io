"""Build checks for the Zola site.

Run from anywhere with:  python3 tests/check_site.py

Stdlib only. Builds into temporary directories, so the repo's public/ is
never touched, and fixture posts are never written into the repo.
"""

import hashlib
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PLACEHOLDER = "TODO: jef writes this"


def find_zola():
    found = shutil.which("zola")
    if found:
        return found
    fallback = Path.home() / ".cargo" / "bin" / "zola"
    if fallback.exists():
        return str(fallback)
    raise RuntimeError("zola not found on PATH or in ~/.cargo/bin")


ZOLA = find_zola()


def build(site_dir, out_dir):
    """Run `zola build` for site_dir into out_dir; return the CompletedProcess."""
    return subprocess.run(
        [ZOLA, "--root", str(site_dir), "build", "--output-dir", str(out_dir),
         "--force"],
        capture_output=True, text=True,
    )


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return Path(path).read_text(encoding="utf-8")


FIXTURE_OLDER = """+++
title = "Older fixture post"
date = 2026-01-01
description = "Fixture description for older"
+++
Fixture body.
"""

FIXTURE_NEWER = """+++
title = "Newer fixture post"
date = 2026-02-01
+++
Fixture body.
"""

FIXTURE_CODE = """+++
title = "Code fixture post"
date = 2025-12-01

[extra]
hero_image = "img/hero-test.png"
+++
Fixture body.

```rust
fn main() {
    let x: u32 = 42;
    println!("{x}");
}
```
"""

FIXTURE_BAD_LANG = """+++
title = "Bad language fixture"
date = 2026-03-01
+++
```notalang
nothing
```
"""

# --- CSS helpers -----------------------------------------------------------

COLOR_TOKENS = ["--bg", "--bg-raised", "--fg", "--fg-muted", "--accent",
                "--link", "--border", "--code-bg", "--hero-bg", "--hero-fg"]

CONTRAST_PAIRS = [("--fg", "--bg"), ("--fg-muted", "--bg"), ("--link", "--bg"),
                  ("--fg", "--code-bg"), ("--hero-fg", "--hero-bg")]

LIGHT_MEDIA = re.compile(
    r"@media\s*\(\s*prefers-color-scheme\s*:\s*light\s*\)\s*\{\s*:root\s*\{"
    r"(?P<body>[^}]*)\}\s*\}")
ROOT_BLOCK = re.compile(r"(?<![\w-]):root\s*\{(?P<body>[^}]*)\}")


def declarations(body):
    """Parse `--name: value;` / `prop: value;` declarations from a block body."""
    body = re.sub(r"/\*.*?\*/", "", body, flags=re.S)
    out = {}
    for decl in body.split(";"):
        if ":" in decl:
            name, value = decl.split(":", 1)
            out[name.strip()] = value.strip()
    return out


def css_modes(css):
    """Return (dark_decls, light_decls) from style.css.

    dark = the first top-level :root block (outside the light media query);
    light = the :root block inside @media (prefers-color-scheme: light).
    """
    light_match = LIGHT_MEDIA.search(css)
    light = declarations(light_match["body"]) if light_match else {}
    outside = LIGHT_MEDIA.sub("", css)
    root_match = ROOT_BLOCK.search(outside)
    dark = declarations(root_match["body"]) if root_match else {}
    return dark, light


def luminance(hex_color):
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if not re.fullmatch(r"[0-9a-fA-F]{6}", h):
        raise ValueError(f"not a plain hex color: {hex_color!r}")
    channels = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255
        channels.append(c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4)
    r, g, b = channels
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = sorted([luminance(a), luminance(b)], reverse=True)
    return (la + 0.05) / (lb + 0.05)


def make_fixture_site(root, posts):
    """Copy the repo to root/site, add {relative_path: text} under content/posts."""
    site = root / "site"
    shutil.copytree(REPO, site, ignore=shutil.ignore_patterns(".git", "public"))
    for rel, text in posts.items():
        path = site / "content" / "posts" / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return site


class RealSite(unittest.TestCase):
    """The site exactly as committed (no posts yet)."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls.tmp.name) / "public"
        cls.result = build(REPO, cls.out)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_build_succeeds(self):
        self.assertEqual(self.result.returncode, 0, self.result.stderr)

    def test_routes_exist(self):
        for route in ["index.html", "posts/index.html", "about/index.html"]:
            self.assertTrue((self.out / route).is_file(), f"missing {route}")

    def test_as_you_like_it_identical(self):
        src = REPO / "static" / "as-you-like-it"
        files = [p for p in src.rglob("*")
                 if p.is_file() and not p.name.startswith(".")]
        self.assertTrue(files, "no as-you-like-it files found in static/")
        for f in files:
            rel = f.relative_to(REPO / "static")
            built = self.out / rel
            self.assertTrue(built.is_file(), f"missing {rel}")
            self.assertEqual(sha256(f), sha256(built), f"{rel} differs")

    def test_placeholders_only(self):
        for route in ["index.html", "about/index.html"]:
            self.assertIn(PLACEHOLDER, read(self.out / route), route)

    # --- theme ---------------------------------------------------------

    def css(self):
        return read(self.out / "style.css")

    def test_stylesheet_linked(self):
        self.assertTrue((self.out / "style.css").is_file(), "missing style.css")
        for route in ["index.html", "posts/index.html", "about/index.html"]:
            html = read(self.out / route)
            self.assertRegex(html, r'<link[^>]+href="[^"]*/style\.css"', route)

    def test_dark_is_default(self):
        dark, light = css_modes(self.css())
        self.assertEqual(dark.get("color-scheme"), "dark")
        self.assertEqual(light.get("color-scheme"), "light")

    def test_tokens_defined_both_modes(self):
        dark, light = css_modes(self.css())
        for token in COLOR_TOKENS:
            self.assertIn(token, dark, f"{token} missing from :root")
            self.assertIn(token, light, f"{token} not overridden for light")

    def test_contrast_aa(self):
        dark, light = css_modes(self.css())
        for mode, decls in [("dark", dark), ("light", light)]:
            for fg, bg in CONTRAST_PAIRS:
                ratio = contrast(decls[fg], decls[bg])
                self.assertGreaterEqual(
                    ratio, 4.5,
                    f"{mode}: {fg} {decls[fg]} on {bg} {decls[bg]} = {ratio:.2f}")

    def test_system_fonts_only(self):
        sources = [self.css()] + [read(p) for p in (REPO / "templates").rglob("*.html")]
        for text in sources:
            self.assertNotIn("@font-face", text)
            self.assertNotRegex(text, r"fonts\.(googleapis|gstatic)\.com")

    def test_hero_default_solid(self):
        html = read(self.out / "index.html")
        hero = re.search(r'<header class="hero"[^>]*>', html)
        self.assertIsNotNone(hero, "landing has no hero header")
        self.assertNotIn("background-image", hero.group(0))


class FixtureSite(unittest.TestCase):
    """A temp copy of the site with two fixture posts added."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        root = Path(cls.tmp.name)
        cls.site = make_fixture_site(root, {
            "older.md": FIXTURE_OLDER,
            "newer/index.md": FIXTURE_NEWER,
            "newer/asset.txt": "asset\n",
            "code.md": FIXTURE_CODE,
        })
        cls.out = root / "public"
        cls.result = build(cls.site, cls.out)
        if cls.result.returncode != 0:
            raise RuntimeError("fixture build failed:\n" + cls.result.stderr)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_post_urls(self):
        for slug in ["older", "newer"]:
            self.assertTrue((self.out / "posts" / slug / "index.html").is_file(),
                            f"missing /posts/{slug}/")

    def test_bundle_asset_copied(self):
        self.assertTrue((self.out / "posts" / "newer" / "asset.txt").is_file())

    def test_landing_lists_posts_newest_first(self):
        html = read(self.out / "index.html")
        newer = html.find("/posts/newer/")
        older = html.find("/posts/older/")
        self.assertNotEqual(newer, -1, "landing does not link newer")
        self.assertNotEqual(older, -1, "landing does not link older")
        self.assertLess(newer, older, "posts not listed newest first")

    def test_posts_section_lists_posts(self):
        html = read(self.out / "posts" / "index.html")
        self.assertIn("/posts/newer/", html)
        self.assertIn("/posts/older/", html)

    def test_description_shown(self):
        self.assertIn("Fixture description for older",
                      read(self.out / "index.html"))

    def test_about_not_listed_as_post(self):
        html = read(self.out / "posts" / "index.html")
        self.assertNotIn("/about/", html.split("<main", 1)[-1]
                         if "<main" in html else html)

    def test_code_highlighted_dual(self):
        html = read(self.out / "posts" / "code" / "index.html")
        self.assertRegex(html, r'<pre[^>]*class="[^"]*giallo')
        self.assertIn("light-dark(", html)

    def test_hero_page_override(self):
        code = read(self.out / "posts" / "code" / "index.html")
        hero = re.search(r'<header class="hero"[^>]*>', code)
        self.assertIsNotNone(hero, "code post has no hero header")
        self.assertRegex(hero.group(0), r"background-image:[^\"]*hero-test\.png")
        newer = read(self.out / "posts" / "newer" / "index.html")
        hero = re.search(r'<header class="hero"[^>]*>', newer)
        self.assertIsNotNone(hero, "newer post has no hero header")
        self.assertNotIn("background-image", hero.group(0))


class BadLanguageSite(unittest.TestCase):
    """A separate temp copy whose only post uses an unknown code language."""

    def test_missing_language_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            site = make_fixture_site(root, {"bad.md": FIXTURE_BAD_LANG})
            result = build(site, root / "public")
            self.assertNotEqual(result.returncode, 0,
                                "build with unknown language should fail")


if __name__ == "__main__":
    unittest.main(verbosity=2)
