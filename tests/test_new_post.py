"""Unit tests for scripts/new_post.py.

Run with:  python3 tests/test_new_post.py   (needs Python 3.11+ for tomllib)

Git tests build a throwaway origin (bare) + clone in a temp dir; nothing
touches this repo.
"""

import contextlib
import datetime
import io
import os
import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import new_post as np  # noqa: E402

# Keep fixture commits independent of the user's git config.
GIT_ENV = {
    "GIT_AUTHOR_NAME": "test", "GIT_AUTHOR_EMAIL": "test@example.invalid",
    "GIT_COMMITTER_NAME": "test", "GIT_COMMITTER_EMAIL": "test@example.invalid",
    "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1",
}


def git(cwd, *args):
    result = subprocess.run(["git", *args], cwd=cwd, capture_output=True,
                            text=True, env={**os.environ, **GIT_ENV})
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed:\n{result.stderr}")
    return result.stdout.strip()


def split_post(post):
    """Return (front_matter_dict, body) for a +++ TOML front-matter post."""
    assert post.startswith("+++\n"), post[:20]
    end = post.index("\n+++\n", 4)
    return tomllib.loads(post[4:end]), post[end + len("\n+++\n"):]


class Slug(unittest.TestCase):

    def test_slug_valid(self):
        for slug in ["heat-engines", "post2", "a"]:
            np.validate_slug(slug)

    def test_slug_invalid(self):
        for slug in ["Heat", "heat_engines", "-x", "x-", "a--b", "a/b", ""]:
            with self.subTest(slug=slug), self.assertRaises(ValueError):
                np.validate_slug(slug)


class Render(unittest.TestCase):

    def test_render_parses(self):
        fm, body = split_post(np.render_post(np.DEFAULT_TITLE, "2026-11-21"))
        self.assertEqual(fm["title"], np.DEFAULT_TITLE)
        self.assertEqual(fm["date"], datetime.date(2026, 11, 21))
        self.assertIs(fm["draft"], True)
        self.assertEqual(fm["extra"], {})
        self.assertIn(np.PLACEHOLDER, body)

    def test_render_custom_title(self):
        title = 'Heat "engines" \\ C:\\path'
        fm, _ = split_post(np.render_post(title, "2026-11-21"))
        self.assertEqual(fm["title"], title)

    def test_render_no_tera(self):
        post = np.render_post(np.DEFAULT_TITLE, "2026-11-21")
        self.assertNotIn("{{", post)
        self.assertNotIn("{%", post)


class Scaffold(unittest.TestCase):
    """main() against a temp origin + clone."""

    BASE = "origin/main"

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.origin = root / "origin.git"
        self.repo = root / "clone"
        git(root, "init", "-q", "--bare", "-b", "main", str(self.origin))
        git(root, "clone", "-q", str(self.origin), str(self.repo))
        git(self.repo, "switch", "-q", "-c", "main")
        posts = self.repo / "content" / "posts"
        (posts / "old-post").mkdir(parents=True)
        (posts / "old-post" / "index.md").write_text("old\n")
        (posts / "flat-post.md").write_text("flat\n")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "base")
        git(self.repo, "push", "-q", "-u", "origin", "main")

    def tearDown(self):
        self.tmp.cleanup()

    def run_main(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = np.main([*args], repo=self.repo)
        return code, out.getvalue(), err.getvalue()

    def branch(self):
        return git(self.repo, "branch", "--show-current")

    def assert_refused(self, code, err, needle=None):
        self.assertEqual(code, 1)
        self.assertEqual(self.branch(), "main")
        self.assertFalse((self.repo / "content" / "posts" / "new-one").exists())
        if needle:
            self.assertIn(needle, err)

    def test_happy_path(self):
        head = git(self.repo, "rev-parse", self.BASE)
        code, out, err = self.run_main("new-one", "--no-fetch")
        self.assertEqual(code, 0, err)
        self.assertEqual(self.branch(), "post/new-one")
        self.assertEqual(git(self.repo, "rev-parse", "HEAD"), head)
        upstream = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "@{upstream}"],
            cwd=self.repo, capture_output=True, text=True)
        self.assertNotEqual(upstream.returncode, 0, "branch should have no upstream")
        post = self.repo / "content" / "posts" / "new-one" / "index.md"
        today = datetime.date.today().isoformat()
        self.assertEqual(post.read_text(), np.render_post(np.DEFAULT_TITLE, today))
        status = git(self.repo, "status", "--porcelain", "--untracked-files=all")
        self.assertEqual(status, "?? content/posts/new-one/index.md")
        self.assertIn("zola serve --drafts", out)
        self.assertIn("ssh -L", out)

    def test_dirty_tree_refused(self):
        (self.repo / "content" / "posts" / "flat-post.md").write_text("edited\n")
        code, _, err = self.run_main("new-one", "--no-fetch")
        self.assert_refused(code, err)

    def test_untracked_file_refused(self):
        (self.repo / "stray.txt").write_text("stray\n")
        code, _, err = self.run_main("new-one", "--no-fetch")
        self.assert_refused(code, err, "stray.txt")

    def test_existing_bundle_refused(self):
        code, _, err = self.run_main("old-post", "--no-fetch")
        self.assertEqual(code, 1)
        self.assertEqual(self.branch(), "main")
        self.assertIn("content/posts/old-post", err)

    def test_existing_flat_post_refused(self):
        code, _, err = self.run_main("flat-post", "--no-fetch")
        self.assertEqual(code, 1)
        self.assertEqual(self.branch(), "main")
        self.assertIn("content/posts/flat-post.md", err)

    def test_local_branch_exists_refused(self):
        git(self.repo, "branch", "post/new-one")
        code, _, err = self.run_main("new-one", "--no-fetch")
        self.assert_refused(code, err, "post/new-one")

    def test_remote_branch_exists_refused(self):
        git(self.repo, "push", "-q", "origin", "main:post/new-one")
        git(self.repo, "fetch", "-q", "origin")
        code, _, err = self.run_main("new-one", "--no-fetch")
        self.assert_refused(code, err, "origin/post/new-one")

    def test_missing_base_refused(self):
        code, _, err = self.run_main("new-one", "--no-fetch", "--base", "origin/nope")
        self.assert_refused(code, err, "origin/nope")

    def test_fetch_sees_new_base(self):
        other = Path(self.tmp.name) / "other"
        git(Path(self.tmp.name), "clone", "-q", str(self.origin), str(other))
        (other / "README").write_text("new\n")
        git(other, "add", "README")
        git(other, "commit", "-q", "-m", "upstream change")
        git(other, "push", "-q", "origin", "main")
        new_head = git(other, "rev-parse", "HEAD")
        code, _, err = self.run_main("new-one")
        self.assertEqual(code, 0, err)
        self.assertEqual(git(self.repo, "rev-parse", "HEAD"), new_head)

    def test_invalid_slug_exits_1(self):
        before = git(self.repo, "status", "--porcelain")
        code, _, err = self.run_main("Bad_Slug", "--no-fetch")
        self.assert_refused(code, err, "Bad_Slug")
        self.assertEqual(git(self.repo, "status", "--porcelain"), before)


if __name__ == "__main__":
    unittest.main(verbosity=2)
