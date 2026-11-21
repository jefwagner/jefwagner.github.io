"""Unit tests for scripts/notes_to_post.py.

Run with:  python3 tests/test_notes_to_post.py
"""

import contextlib
import io
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import notes_to_post as n2p  # noqa: E402

FENCE = "```"


def split_post(post):
    """Return (front_matter_dict, body) for a +++ TOML front-matter post."""
    assert post.startswith("+++\n"), post[:20]
    end = post.index("\n+++\n", 4)
    return tomllib.loads(post[4:end]), post[end + len("\n+++\n"):]


class ConvertInline(unittest.TestCase):

    def test_inline_simple(self):
        self.assertEqual(n2p.convert_math("a $x$ b"), "a `$x$` b")

    def test_inline_punctuation(self):
        self.assertEqual(n2p.convert_math("($U$), $S$."), "(`$U$`), `$S$`.")

    def test_inline_table_cell(self):
        src = "| Entropy | $S$ | $(U,V,\\ldots)$ |"
        self.assertEqual(n2p.convert_math(src),
                         "| Entropy | `$S$` | `$(U,V,\\ldots)$` |")

    def test_inline_spans_line(self):
        self.assertEqual(n2p.convert_math("x $a +\nb$ y"), "x `$a +\nb$` y")

    def test_escaped_dollar(self):
        self.assertEqual(n2p.convert_math("costs \\$5 and $x$"),
                         "costs \\$5 and `$x$`")


class ConvertDisplay(unittest.TestCase):

    def test_display_block(self):
        self.assertEqual(n2p.convert_math("$$\nS = k\n$$"),
                         f"{FENCE}math\nS = k\n{FENCE}")

    def test_display_trailing_spaces(self):
        self.assertEqual(n2p.convert_math("$$  \nx\n$$ "),
                         f"{FENCE}math\nx\n{FENCE}")

    def test_display_one_line(self):
        self.assertEqual(n2p.convert_math("$$ x = 1 $$"),
                         f"{FENCE}math\nx = 1\n{FENCE}")

    def test_display_content_untouched(self):
        content = ("\\left.\\frac{a}{b}\\right|_{x} \\, y \\\\\n"
                   "a &= b \\text{ costs $5}")
        self.assertEqual(n2p.convert_math(f"$$\n{content}\n$$"),
                         f"{FENCE}math\n{content}\n{FENCE}")

    def test_code_untouched(self):
        src = (f"{FENCE}python\nprice = '$5 and $6'\n{FENCE}\n\n"
               "Run `echo $HOME` then $x$.")
        expected = (f"{FENCE}python\nprice = '$5 and $6'\n{FENCE}\n\n"
                    "Run `echo $HOME` then `$x$`.")
        self.assertEqual(n2p.convert_math(src), expected)


class ConvertErrors(unittest.TestCase):

    def test_unclosed_display(self):
        with self.assertRaisesRegex(ValueError, r"line 1\b"):
            n2p.convert_math("$$\nx")

    def test_unclosed_inline(self):
        with self.assertRaisesRegex(ValueError, r"line 1\b"):
            n2p.convert_math("a $x b")


class Title(unittest.TestCase):

    def test_extract_title(self):
        self.assertEqual(n2p.extract_title("# Basics\n\nBody"), ("Basics", "Body"))

    def test_extract_title_missing(self):
        with self.assertRaises(ValueError):
            n2p.extract_title("Body")


class Templating(unittest.TestCase):

    def test_templating_refused(self):
        with self.assertRaises(n2p.TemplatingError) as ctx:
            n2p.check_templating("a\n{{ x }}\nb")
        self.assertEqual(ctx.exception.lines, [2])


class FrontMatter(unittest.TestCase):

    def test_front_matter_escaping(self):
        title = 'A "quoted" \\ title'
        desc = 'Says "hi" \\o/'
        fm = n2p.front_matter(title=title, date="2026-11-21", description=desc,
                              draft=False, math=True)
        data, body = split_post(fm + "body")
        self.assertEqual(data["title"], title)
        self.assertEqual(data["description"], desc)
        self.assertEqual(body, "body")

    def test_notes_to_post_end_to_end(self):
        notes = "# My Title\n\nSome $x$ here.\n\n$$\ny = 2\n$$\n"
        post = n2p.notes_to_post(notes, date="2026-11-21", description="Desc")
        data, body = split_post(post)
        self.assertEqual(data["title"], "My Title")
        self.assertEqual(str(data["date"]), "2026-11-21")
        self.assertEqual(data["description"], "Desc")
        self.assertNotIn("draft", data)
        self.assertEqual(data["extra"], {"math": True})
        self.assertEqual(body, f"Some `$x$` here.\n\n{FENCE}math\ny = 2\n{FENCE}\n")


class Cli(unittest.TestCase):

    def test_cli_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "notes.md"
            dest = Path(tmp) / "post.md"
            src.write_text("# T\n\nBody $x$.\n", encoding="utf-8")
            dest.write_text("existing\n", encoding="utf-8")
            argv = [str(src), str(dest), "--date", "2026-11-21"]
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(n2p.main(argv), 1)
            self.assertEqual(dest.read_text(encoding="utf-8"), "existing\n")
            self.assertEqual(n2p.main(argv + ["--force"]), 0)
            self.assertIn("`$x$`", dest.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
