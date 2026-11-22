# AGENTS.md — jefwagner.github.io

## Project summary

**jefwagner.github.io** is jef's personal site, rebuilt from scratch as a Zola
(v0.23.6) blog: a landing page listing posts, `/posts/<slug>/` articles, and an
`/about/` page, in an Ayu Dark theme with KaTeX math and embeddable interactive
widgets (Plotly). It also serves as-you-like-it, a Godot web game, from
`static/`.

It exists so jef can publish articles in which he works through an idea in his
own words, plus proof-of-concept demos from his projects. Success means adding a
post is low-friction (write markdown, build, push) while a post can still carry
custom math, widgets, or layouts when it needs them.

The constraint everything else follows from: **all prose is jef's.** Articles,
the about page, landing-page text and post descriptions are written by him. An
agent's job with prose is review and mechanical fixes only (see Writing rule
below). Agents build the infrastructure: templates, CSS, JS, scripts, tests,
CI.

**Status:** live since 2026-11-21. `main` is the site: GitHub Actions
(`.github/workflows/site.yml`) checks every push and PR, and deploys on push to
`main`. First post `/posts/thermo/` is published. Landing and about text are
jef's; his AI policy is its own page, `/ai-policy/`, linked from the site
footer (the landing's pointer line to it is still a `TODO` for jef). New posts
follow `notes/post-workflow.md`.

## Writing rule (prose is jef's)

- Never add, draft, or rewrite prose in content: no explanations, arguments,
  derivations, summaries or site copy, even when a gap is obvious. Templates
  may hold obvious placeholders (`TODO: jef writes this`), never drafted text.
- Allowed on prose: **review** and **mechanical fixes** (typos, grammar,
  notation consistency, formatting, clear LaTeX slips). Flag, don't fix,
  physics/math sign errors and content issues.
- Review feedback goes in a companion `<name>-comments.md` next to the file,
  listing only what remains for jef to write, by section name (not line
  number), with applied fixes left out; move items to a Resolved section as
  they're addressed.
- Re-read a file before every pass: jef edits between sessions and has lost
  fixes to stale editor buffers before.

## System layout

- `config.toml` — Zola config: highlighting (ayu-dark / github-light code
  themes), `extra_grammars` (the `math` fence), `[extra] hero_image`.
- `content/` — `_index.md` (landing), `about.md`, `ai-policy.md`, `posts/`
  (one file or page bundle per post; `posts/fixture-math-widgets/` is a
  **draft** test fixture, never published).
- `templates/` — `base.html` (skeleton, hero, per-page asset loading),
  `index.html`, `section.html`, `page.html`, `post_list.html`,
  `components.html` (Tera components, e.g. `widget`).
- `static/` — copied through verbatim: `style.css` (theme tokens), `math.js`,
  `widgets.js`, `vendor/` (pinned KaTeX and Plotly basic), and
  `as-you-like-it/`.
- `grammars/math.json` — empty TextMate grammar so ```` ```math ```` fences
  pass `error_on_missing_language`.
- `scripts/notes_to_post.py` — converts a markdown notes file into a post
  (math delimiters and title only; prose unchanged).
- `scripts/new_post.py` — starts a post: branch `post/<slug>` from
  `origin/main` plus a draft page bundle with placeholders only.
- `scripts/hero.py` + `scripts/hero_gen/` — hero banners via OpenRouter image
  models (generate, day/night twin, contrast check, export to `static/img/`);
  deps declared inline for `uv run`. Costs money: see `notes/hero-images.md`.
  Writes scratch output to `hero-work/` (gitignored).
- `scripts/check` — runs every test suite (what CI runs).
- `tests/` — `check_site.py` (site build checks), `test_notes_to_post.py`,
  `test_new_post.py`, `test_hero_gen.py` (no network, no spend),
  `katex_check.js`.
- `.github/workflows/site.yml` — CI checks on every push/PR; build (no
  drafts) and Pages deploy on push to `main`. Zola version + sha256 pinned
  here (a test keeps it equal to the local Zola).
- `notes/post-conventions.md` — **read before writing or porting a post**:
  front-matter switches, math-as-code, Zola 0.23 gotchas, widget contract.
- `notes/post-workflow.md` — the procedure for shipping a post: branch,
  preview (incl. over SSH), checks, PR, merge = deploy, undo.
- `notes/hero-images.md` — making hero banners: day/night pairs, shape,
  the `hero.py` workflow, cost and key handling.
- `planning/` — handoff docs for work done in other repos (flint docs, the
  hero-image lab experiment).
- `todo.md`, `backlog.md`, `changelog.md` — tdd-mode planning and history.

## Build and test

Free to run without asking (read-only checks):

```text
zola build --output-dir <tmpdir>                                 # build (never into the repo)
zola serve [--drafts]                                            # local preview
scripts/check                                                    # all suites, as CI runs them
python3 tests/check_site.py                                      # site checks only (Python 3.10+)
```

The site checks include a KaTeX render check that needs `node` (found on `PATH`
or under `~/.nvm`) and is skipped without it; `REQUIRE_NODE=1` (set in CI)
makes a missing node a failure instead. `public/` is build output and is
gitignored.

## Constraints

- **as-you-like-it** is jef's daughter's school project. Its repo is private
  and must stay private: it is served from `static/as-you-like-it/`, copied
  unchanged. Never suggest making it public or moving it to its own Pages site.
- **flint docs** are served by the `flint` repo's own Pages site at `/flint/`
  (see `planning/flint-docs-handoff.md`). Don't add a `flint/` folder here; a
  project site takes precedence over a same-named path anyway.
- **Zola 0.23 is a breaking release** that differs from older docs and
  training data: no shortcodes (Tera components), post content is templated
  (a literal `{{` needs `{% raw %}`), highlighting is Giallo. Check Zola's own
  CHANGELOG and docs for this version before assuming behavior.

## Modes of work

Mode switches are explicit — say "pair", "tdd", or "unsupervised" to change modes.
The default, when no mode is stated, is **pair**.

Three nested loops, each with a different unit of approval:

| Mode           | Unit of work              | Writes need approval? |
|----------------|---------------------------|-----------------------|
| `pair`         | single command/change     | yes, per command      |
| `tdd`          | task / commit-sized item  | no                    |
| `unsupervised` | feature / whole goal      | no                    |

The nesting widens the unit of work that may be done unattended: a single command
in pair, a task in tdd, a whole feature or goal in unsupervised. Stepping up is
jef's call, not mine — if a task needs many writes, say so and suggest `tdd`
rather than quietly widening the loop.

### Pair mode (default)

Pair-programming at the keyboard. Short back-and-forth, one or two ideas per
interaction — no long essays presenting a pile of options. Every idea and change
gets discussed as we go: a sentence or two saying what I'm about to do and why,
then act. No autopilot — no multi-file refactors or multi-step plans executed
without checking in between steps.

Freely, without asking:

- read files, search the repo (`rg`, `find`, `grep`), read `notes/` and the wiki
- non-destructive inspection: `ls`, `cat`, `head`, `tail`, `wc`, `git status`,
  `git log`, `git diff`, and the project's own read-only checks (type-checks,
  linters, test suites, `--help` output)

Ask for explicit approval, per command, before:

- writing, editing, creating, moving, or deleting any file — including `notes/`,
  `todo.md`, `backlog.md`, and anything outside the repo
- destructive or state-changing commands: `rm`, `mv`, `cp` over an existing file,
  `git commit`/`push`/`checkout`/`reset`, or anything else that changes state on
  disk
- installing packages, editing config outside the repo, sending mail

Approval is per command, not blanket — "yes, go ahead" for one command does not
authorize the next. One approval covers one file: a multi-hunk edit within a
single file is one atomic change, but two files is two approvals. Never commit
unless asked in that same turn, even if every individual write was approved.

Full rules: read `~/tools/llm-instructions/pair.md`.

### TDD mode (interactive)

Structured mode for larger chunks of work. Two sub-modes:

- **Plan** — read `~/tools/llm-instructions/planning.md` first. Produces 1–4
  one-commit-sized items in `todo.md` and triages `backlog.md`.
- **Implement** — read `~/tools/llm-instructions/implementation.md` first. TDD
  loop with hard STOP gates requiring user approval at the task level.

Writes, edits, and commits are **not** gated per command here — the task-level
STOP gates are the approval unit. Commits remain one-item-per-commit, and I still
state intent before each task, but I don't ask before every `edit`.

### Unsupervised mode

For well-scoped work that jef approves up front and then leaves to run
independently (e.g. overnight or long-running jobs).

1. **Goal stage (conversational)**: work with jef to draft `goal.md` at the repo
   root. It must contain: the goal, constraints, a definition of done, and a
   **spend cap in dollars** agreed during the conversation. Write `goal.md` as a
   complete prompt — an agent with no other context should be able to do the work
   from it alone.
2. **Approval gate**: do not start work until jef explicitly approves `goal.md`.
   Revise and re-submit until approved.
3. **Independent work**: once approved, proceed without further check-ins. Track
   spend against the cap with:
   `uv run ~/tools/spend.py --cap <cap from goal.md>`
   (the script prints session spend and exits non-zero once the cap is exceeded).
   Check periodically as you work.
4. **Stop and report**: stop when the goal is met, the cap is exceeded, or the
   work is blocked. In every case, write a summary email — what was done, what
   was learned, current state, and next steps, including the final spend from
   `uv run ~/tools/spend.py` — and send it to jef with:
   `msmtp -t < summary-email.txt`
   (mail is configured via the mounted `~/.msmtprc`; from address is
   jefwagner@gmail.com).

## Git

- Remote is jef's own **public** repo, `github.com/jefwagner/jefwagner.github.io`.
  Every push to `main` deploys the live site, so changes reach `main` only
  through a PR from a branch (posts: `post/<slug>`; see
  `notes/post-workflow.md`). Never push or merge to `main` unless jef asks in
  that same turn.
- Commit identity in the devcontainer is the bot account. Commit style: short
  summary line + longer body.

## Wiki

This repo has **no** entry in `~/wiki/projects/`. Knowledge stays in `notes/`.
If it ever gets one, add a wiki pointer here following the pattern in
`~/wiki/AGENTS.md`.
