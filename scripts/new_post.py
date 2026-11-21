"""Start a new post on its own branch.

Usage:  python3 scripts/new_post.py SLUG [--title TITLE] [--base REF] [--no-fetch]

Fetches origin, checks the tree is clean and the slug is unused, creates
branch post/SLUG from REF (default origin/main), and writes a draft page
bundle at content/posts/SLUG/index.md with placeholder text only. Nothing
is committed or pushed. See notes/post-workflow.md for the full procedure.
"""

import argparse
import datetime
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SLUG_RE = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")
DEFAULT_TITLE = "TODO: title"
PLACEHOLDER = "TODO: jef writes this"


NEXT_STEPS = """\
Created branch {branch} with a draft post at {path}
(uncommitted; commit it with your first real edit).

Next:
  zola serve --drafts              # preview at http://127.0.0.1:1111/posts/{slug}/
  ssh -L 1111:localhost:1111 HOST  # remote: run on your laptop, then open the same URL
  scripts/check                    # all site checks, before pushing
Then follow notes/post-workflow.md: un-draft, push, PR, merge, deploy.
"""


def validate_slug(slug):
    """Raise ValueError unless slug is lowercase words joined by single hyphens."""
    if not SLUG_RE.fullmatch(slug):
        raise ValueError(f"bad slug {slug!r}: use lowercase letters and digits "
                         "joined by single hyphens, e.g. heat-engines")


def toml_string(value):
    """A TOML basic string. JSON string escapes are a valid subset of TOML's."""
    return json.dumps(value, ensure_ascii=False)


def render_post(title, date):
    """Front matter + placeholder body. No prose beyond placeholders."""
    return f"""+++
title = {toml_string(title)}
date = {date}
description = {toml_string(PLACEHOLDER)}
draft = true

[extra]
# math = true       # KaTeX; write math as ```math fences / `$...$` code
# plotly = true     # Plotly + widgets.js
# widgets = true    # widgets.js only
# hero_image = "img/x.png"
+++

{PLACEHOLDER}
"""


def git(repo, *args):
    """Run git in repo; return the CompletedProcess (never raises)."""
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True)


def ref_exists(repo, ref):
    return git(repo, "rev-parse", "--verify", "--quiet", ref).returncode == 0


def preflight(repo, slug, base):
    """Problems that block scaffolding (empty list = OK)."""
    problems = []
    dirty = git(repo, "status", "--porcelain", "--untracked-files=all").stdout
    if dirty.strip():
        files = ", ".join(line[3:] for line in dirty.splitlines())
        problems.append(f"working tree is not clean (commit or stash first): {files}")
    branch = f"post/{slug}"
    if ref_exists(repo, f"refs/heads/{branch}"):
        problems.append(f"branch {branch} already exists locally")
    if ref_exists(repo, f"refs/remotes/origin/{branch}"):
        problems.append(f"branch origin/{branch} already exists")
    if not ref_exists(repo, f"{base}^{{commit}}"):
        problems.append(f"base ref {base} not found (fetch, or check --base)")
    else:
        for path in [f"content/posts/{slug}", f"content/posts/{slug}.md"]:
            if git(repo, "cat-file", "-e", f"{base}:{path}").returncode == 0:
                problems.append(f"{path} already exists in {base}")
    return problems


def main(argv=None, repo=REPO):
    """fetch -> preflight -> branch -> write the bundle -> print next steps."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("slug", help="lowercase-hyphenated, e.g. heat-engines")
    parser.add_argument("--title", default=DEFAULT_TITLE)
    parser.add_argument("--base", default="origin/main",
                        help="ref to branch from (default: origin/main)")
    parser.add_argument("--no-fetch", action="store_true",
                        help="skip `git fetch origin`")
    args = parser.parse_args(argv)

    def fail(message):
        print(f"new_post: {message}", file=sys.stderr)
        return 1

    try:
        validate_slug(args.slug)
    except ValueError as err:
        return fail(err)
    if not args.no_fetch:
        fetched = git(repo, "fetch", "--quiet", "origin")
        if fetched.returncode != 0:
            return fail("git fetch origin failed:\n" + fetched.stderr)
    problems = preflight(repo, args.slug, args.base)
    if problems:
        return fail("refusing to start the post:\n  " + "\n  ".join(problems))

    branch = f"post/{args.slug}"
    switched = git(repo, "switch", "--quiet", "--no-track", "-c", branch, args.base)
    if switched.returncode != 0:
        return fail(f"git switch failed:\n{switched.stderr}")
    rel = Path("content") / "posts" / args.slug / "index.md"
    post = repo / rel
    post.parent.mkdir(parents=True)
    post.write_text(render_post(args.title, datetime.date.today().isoformat()),
                    encoding="utf-8")
    print(NEXT_STEPS.format(branch=branch, path=rel.as_posix(), slug=args.slug))
    return 0


if __name__ == "__main__":
    sys.exit(main())
