"""Convert a markdown notes file into a Zola post for this site.

    python3 scripts/notes_to_post.py SRC DEST --date YYYY-MM-DD \
        [--description TEXT] [--draft] [--no-math] [--force]

The prose is copied unchanged. Only two things are rewritten:

- math delimiters, because Zola's markdown mangles raw LaTeX: `$$...$$`
  display blocks become ```math fences and `$...$` inline math becomes
  `` `$...$` `` inline code (see notes/post-conventions.md);
- the leading `# Title` line, which moves into the front-matter title.

It refuses to write a post containing `{{` or `{%`, which Zola 0.23 would
treat as Tera template syntax.

Stdlib only; runs on Python 3.10+.
"""

import argparse
import datetime
import re
import sys
from pathlib import Path

FENCE_OPEN = re.compile(r"^ {0,3}(`{3,}|~{3,})")


class TemplatingError(ValueError):
    """Output would contain `{{` or `{%` (Zola 0.23 templates post content)."""

    def __init__(self, lines):
        self.lines = lines
        super().__init__(
            "Tera template syntax ({{ or {%) on line(s) "
            + ", ".join(map(str, lines))
            + "; wrap it in {% raw %}...{% endraw %} or rewrite it")


# --- math --------------------------------------------------------------------

def _convert_inline(para):
    """Convert `$...$` in one paragraph, given as [(lineno, line), ...]."""
    first_line = para[0][0]
    text = "\n".join(line for _, line in para)

    def lineno(pos):
        return first_line + text.count("\n", 0, pos)

    out = []
    k, n = 0, len(text)
    while k < n:
        c = text[k]
        if c == "\\" and k + 1 < n:
            out.append(text[k:k + 2])          # escapes (incl. \$) pass through
            k += 2
            continue
        if c == "`":                           # inline code span: copy verbatim
            run = re.match(r"`+", text[k:]).end()
            close = re.compile(r"(?<!`)" + "`" * run + r"(?!`)")
            m = close.search(text, k + run)
            end = m.end() if m else k + run
            out.append(text[k:end])
            k = end
            continue
        if c == "$":
            if text.startswith("$$", k):
                raise ValueError(
                    f"line {lineno(k)}: $$ inside a paragraph; "
                    "put display math on its own lines")
            j = k + 1
            while j < n and text[j] != "$":
                j += 2 if text[j] == "\\" else 1
            if j >= n:
                raise ValueError(f"line {lineno(k)}: unclosed inline $")
            inner = text[k + 1:j]
            if not inner.strip():
                raise ValueError(f"line {lineno(k)}: empty inline math $$")
            if "`" in inner:
                raise ValueError(f"line {lineno(k)}: backtick inside inline math")
            out.append(f"`${inner}$`")
            k = j + 1
            continue
        out.append(c)
        k += 1
    return "".join(out).split("\n")


def convert_math(text):
    """$$...$$ display blocks -> ```math fences; $...$ inline -> `$...$`.

    Fenced code blocks, inline code spans and escaped dollars are untouched.
    Raises ValueError (naming the line) on unclosed math.
    """
    lines = text.split("\n")
    out, para = [], []
    fence = None

    def flush():
        if para:
            out.extend(_convert_inline(para))
            para.clear()

    i = 0
    while i < len(lines):
        line, ln = lines[i], i + 1
        stripped = line.strip()

        if fence:                                  # inside a code fence
            out.append(line)
            if re.match(rf"^ {{0,3}}{re.escape(fence[0])}{{{len(fence)},}}\s*$", line):
                fence = None
            i += 1
            continue

        m = FENCE_OPEN.match(line)
        if m:
            flush()
            fence = m.group(1)
            out.append(line)
            i += 1
            continue

        if stripped == "$$":                       # multi-line display block
            flush()
            j = i + 1
            while j < len(lines) and lines[j].strip() != "$$":
                j += 1
            if j == len(lines):
                raise ValueError(f"line {ln}: unclosed $$ display block")
            out.append("```math")
            out.extend(lines[i + 1:j])
            out.append("```")
            i = j + 1
            continue

        if len(stripped) > 4 and stripped.startswith("$$") and stripped.endswith("$$"):
            flush()                                # one-line display block
            out.extend(["```math", stripped[2:-2].strip(), "```"])
            i += 1
            continue

        if not stripped:
            flush()
            out.append(line)
        else:
            para.append((ln, line))
        i += 1

    if fence:
        raise ValueError(f"unclosed code fence {fence!r}")
    flush()
    return "\n".join(out)


# --- title, templating, front matter -----------------------------------------

def extract_title(text):
    """Split a leading `# Title` line off; return (title, rest)."""
    lines = text.split("\n")
    m = re.match(r"^# +(.+?)\s*$", lines[0]) if lines else None
    if not m:
        raise ValueError("source must start with a '# Title' line")
    rest = lines[1:]
    if rest and not rest[0].strip():
        rest = rest[1:]
    return m.group(1), "\n".join(rest)


def check_templating(text):
    """Raise TemplatingError if `{{` or `{%` appears anywhere."""
    bad = [i for i, line in enumerate(text.split("\n"), 1)
           if "{{" in line or "{%" in line]
    if bad:
        raise TemplatingError(bad)


def _toml_string(s):
    escaped = (s.replace("\\", "\\\\").replace('"', '\\"')
                .replace("\n", "\\n").replace("\t", "\\t"))
    return f'"{escaped}"'


def front_matter(*, title, date, description, draft, math):
    """TOML front matter block (+++ ... +++), strings escaped for TOML."""
    datetime.date.fromisoformat(date)              # validate YYYY-MM-DD
    lines = ["+++", f"title = {_toml_string(title)}", f"date = {date}"]
    if description:
        lines.append(f"description = {_toml_string(description)}")
    if draft:
        lines.append("draft = true")
    if math:
        lines += ["", "[extra]", "math = true"]
    lines.append("+++")
    return "\n".join(lines) + "\n"


def notes_to_post(text, *, date, description=None, draft=False, math=True):
    """Whole conversion: templating check, title, math, front matter."""
    check_templating(text)                         # line numbers = source lines
    title, rest = extract_title(text)
    body = convert_math(rest)
    return front_matter(title=title, date=date, description=description,
                        draft=draft, math=math) + body


# --- CLI ---------------------------------------------------------------------

def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("src", type=Path)
    p.add_argument("dest", type=Path)
    p.add_argument("--date", required=True, help="YYYY-MM-DD")
    p.add_argument("--description")
    p.add_argument("--draft", action="store_true")
    p.add_argument("--no-math", dest="math", action="store_false")
    p.add_argument("--force", action="store_true", help="overwrite DEST")
    args = p.parse_args(argv)

    if args.dest.exists() and not args.force:
        print(f"error: {args.dest} exists (use --force to overwrite)", file=sys.stderr)
        return 1
    try:
        post = notes_to_post(args.src.read_text(encoding="utf-8"), date=args.date,
                             description=args.description, draft=args.draft,
                             math=args.math)
    except (ValueError, OSError) as err:
        print(f"error: {args.src}: {err}", file=sys.stderr)
        return 1
    args.dest.parent.mkdir(parents=True, exist_ok=True)
    args.dest.write_text(post, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
