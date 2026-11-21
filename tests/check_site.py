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


def build(site_dir, out_dir, drafts=False):
    """Run `zola build` for site_dir into out_dir; return the CompletedProcess."""
    cmd = [ZOLA, "--root", str(site_dir), "build", "--output-dir", str(out_dir),
           "--force"]
    if drafts:
        cmd.append("--drafts")
    return subprocess.run(cmd, capture_output=True, text=True)


def find_node():
    """Path to node, or None. Checks PATH, then nvm installs."""
    found = shutil.which("node")
    if found:
        return found
    nvm = sorted((Path.home() / ".nvm" / "versions" / "node").glob("*/bin/node"))
    return str(nvm[-1]) if nvm else None


NODE = find_node()
KATEX_CHECK = REPO / "tests" / "katex_check.js"


def katex_js():
    """The vendored katex.min.js (found by glob so the version lives in one place)."""
    found = sorted((REPO / "static" / "vendor").glob("katex-*/katex.min.js"))
    if len(found) != 1:
        raise RuntimeError(f"expected one vendored katex.min.js, found {found}")
    return found[0]


def katex_check(html_files):
    """Run tests/katex_check.js on built HTML files."""
    return subprocess.run(
        [NODE, str(KATEX_CHECK), str(katex_js())] + [str(f) for f in html_files],
        capture_output=True, text=True)


def math_pages(out_dir):
    """Built pages that load katex.min.js (i.e. have [extra] math = true)."""
    return sorted(p for p in Path(out_dir).rglob("index.html")
                  if re.search(r'<script[^>]+src="[^"]*/katex\.min\.js"', read(p)))


FIXTURE_BAD_LATEX = """+++
title = "Bad LaTeX fixture"
date = 2026-03-01

[extra]
math = true
+++
Inline `$\\notacommand$` here.

```math
\\frac{a}{
```
"""


FIXTURE_SLUG = "fixture-math-widgets"
EXTRA_ASSETS = ["katex", "math.js", "plotly", "widgets.js"]


def script_and_link_refs(html):
    """All src/href values of <script> and <link> tags, in document order."""
    return re.findall(r'<(?:script|link)\b[^>]*?(?:src|href)="([^"]+)"', html)


def text_of(fragment):
    """Strip tags and decode the few entities Zola emits."""
    text = re.sub(r"<[^>]+>", "", fragment)
    for ent, ch in [("&lt;", "<"), ("&gt;", ">"), ("&quot;", '"'),
                    ("&#39;", "'"), ("&amp;", "&")]:
        text = text.replace(ent, ch)
    return text


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

    # --- math and widgets ------------------------------------------------

    def test_fixture_excluded(self):
        self.assertFalse((self.out / "posts" / FIXTURE_SLUG).exists(),
                         "draft fixture was published")
        self.assertNotIn(FIXTURE_SLUG, read(self.out / "index.html"))

    def test_no_extras_by_default(self):
        for route in ["index.html", "posts/index.html", "about/index.html"]:
            refs = " ".join(script_and_link_refs(read(self.out / route)))
            for asset in EXTRA_ASSETS:
                self.assertNotIn(asset, refs, f"{route} loads {asset}")

    def test_vendored_pinned(self):
        vendor = REPO / "static" / "vendor"
        katex = [d for d in vendor.glob("katex-*") if d.is_dir()]
        self.assertEqual(len(katex), 1, "expected one vendor/katex-<ver>/ dir")
        self.assertRegex(katex[0].name, r"^katex-\d+\.\d+\.\d+$")
        for name in ["katex.min.js", "katex.min.css"]:
            self.assertTrue((katex[0] / name).is_file(), f"missing {name}")
        self.assertTrue(any((katex[0] / "fonts").glob("*.woff2")),
                        "missing KaTeX fonts")
        plotly = list(vendor.glob("plotly-basic-*.min.js"))
        self.assertEqual(len(plotly), 1, "expected one plotly-basic-<ver>.min.js")
        self.assertRegex(plotly[0].name, r"^plotly-basic-\d+\.\d+\.\d+\.min\.js$")


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


class DraftsSite(unittest.TestCase):
    """The real repo built with --drafts, which includes the fixture post."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls.tmp.name) / "public"
        cls.result = build(REPO, cls.out, drafts=True)
        page = cls.out / "posts" / FIXTURE_SLUG / "index.html"
        cls.html = read(page) if page.is_file() else ""

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_drafts_build_succeeds(self):
        self.assertEqual(self.result.returncode, 0, self.result.stderr)
        self.assertTrue(self.html, "fixture page not built with --drafts")

    def test_math_assets_loaded(self):
        refs = script_and_link_refs(self.html)
        self.assertTrue(any(re.search(r"katex[^/]*/katex\.min\.css$", r) for r in refs))
        self.assertTrue(any(re.search(r"katex[^/]*/katex\.min\.js$", r) for r in refs))
        self.assertTrue(any(r.endswith("/math.js") for r in refs))

    def test_display_math_preserved(self):
        blocks = re.findall(r'<pre[^>]*>\s*<code[^>]*data-lang="math"[^>]*>(.*?)</code>',
                            self.html, flags=re.S)
        self.assertTrue(blocks, "no math code block found")
        text = text_of("".join(blocks))
        for exact in [r"\right|_{U_{\text{res}}", r"\,", r"\\"]:
            self.assertIn(exact, text, f"{exact!r} not preserved")

    def test_inline_math_preserved(self):
        self.assertIn(r"<code>$U_{\text{tot}}$</code>", self.html)

    def test_plotly_before_widgets(self):
        refs = script_and_link_refs(self.html)
        plotly = [i for i, r in enumerate(refs) if "plotly" in r]
        widgets = [i for i, r in enumerate(refs) if r.endswith("/widgets.js")]
        self.assertTrue(plotly, "plotly not loaded")
        self.assertTrue(widgets, "widgets.js not loaded")
        self.assertLess(plotly[0], widgets[0])

    def test_widget_markup(self):
        self.assertRegex(
            self.html,
            r'<div class="widget" data-src="sine\.js" style="height:\s*\d+px;?"')
        self.assertTrue((self.out / "posts" / FIXTURE_SLUG / "sine.js").is_file())

    def test_widget_contract(self):
        src = read(self.out / "posts" / FIXTURE_SLUG / "sine.js")
        self.assertIn("export default function", src)


@unittest.skipUnless(NODE, "node not installed; KaTeX render check skipped")
class KatexRender(unittest.TestCase):
    """Run every built post's math through the vendored KaTeX (throwOnError)."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls.tmp.name) / "public"
        result = build(REPO, cls.out, drafts=True)
        if result.returncode != 0:
            raise RuntimeError("drafts build failed:\n" + result.stderr)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_math_pages_detected(self):
        pages = [p.relative_to(self.out).as_posix() for p in math_pages(self.out)]
        self.assertIn(f"posts/{FIXTURE_SLUG}/index.html", pages)
        for route in ["index.html", "posts/index.html", "about/index.html"]:
            self.assertNotIn(route, pages)

    def test_all_math_pages_render(self):
        pages = math_pages(self.out)
        result = katex_check(pages)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        oks = [l for l in result.stdout.splitlines() if l.startswith("ok ")]
        self.assertEqual(len(oks), len(pages), result.stdout)

    def test_bad_latex_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            site = make_fixture_site(root, {"bad-latex.md": FIXTURE_BAD_LATEX})
            built = build(site, root / "public")
            self.assertEqual(built.returncode, 0, built.stderr)
            page = root / "public" / "posts" / "bad-latex" / "index.html"
            result = katex_check([page])
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        fails = [l for l in result.stdout.splitlines() if l.startswith("FAIL ")]
        self.assertEqual(len(fails), 2, result.stdout)
        self.assertTrue(any(": display: " in l for l in fails), fails)
        self.assertTrue(any(": inline: " in l for l in fails), fails)

    def test_no_math_is_usage_error(self):
        result = katex_check([self.out / "about" / "index.html"])
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)


class TeraBracesSite(unittest.TestCase):
    """Zola 0.23 templates post content: a literal `{{` breaks the build."""

    MATH = "\\frac{1}{{a+b}}"

    def build_post(self, body):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            post = f'+++\ntitle = "braces"\ndate = 2026-01-01\n+++\n{body}\n'
            site = make_fixture_site(root, {"braces.md": post})
            return build(site, root / "public")

    def test_tera_braces_in_math_need_raw(self):
        bare = self.build_post(f"```math\n{self.MATH}\n```")
        self.assertNotEqual(bare.returncode, 0,
                            "`{{` in content should fail the build")
        raw = self.build_post(f"{{% raw %}}\n```math\n{self.MATH}\n```\n{{% endraw %}}")
        self.assertEqual(raw.returncode, 0, raw.stderr)


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
