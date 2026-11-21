"""Build checks for the Zola site.

Run from anywhere with:  python3 tests/check_site.py

Stdlib only. Builds into temporary directories, so the repo's public/ is
never touched, and fixture posts are never written into the repo.
"""

import hashlib
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


class FixtureSite(unittest.TestCase):
    """A temp copy of the site with two fixture posts added."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        root = Path(cls.tmp.name)
        cls.site = root / "site"
        shutil.copytree(REPO, cls.site,
                        ignore=shutil.ignore_patterns(".git", "public"))
        posts = cls.site / "content" / "posts"
        (posts / "older.md").write_text(FIXTURE_OLDER, encoding="utf-8")
        bundle = posts / "newer"
        bundle.mkdir()
        (bundle / "index.md").write_text(FIXTURE_NEWER, encoding="utf-8")
        (bundle / "asset.txt").write_text("asset\n", encoding="utf-8")
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


if __name__ == "__main__":
    unittest.main(verbosity=2)
