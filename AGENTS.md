# AGENTS.md — blog (jefwagner.github.io)

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
footer. The hero is the moonbase day/night banner, credited in the footer
(`hero_credit`). New posts follow `notes/post-workflow.md`.
2026-11-27: moved from `~/github-pages` to `~/projects/blog` and given an
agent devcontainer; the `docs/wrap-up-hero` close-out still awaits its PR
to `main`.

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
  themes), `extra_grammars` (the `math` fence), `[extra]` hero settings
  (`hero_title`, the `hero_image`/`hero_image_light` pair, `hero_credit`).
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
  hero-image lab experiment). Historical: they name the old clone path
  `~/github-pages`; the repo is now `~/projects/blog`.
- `.devcontainer/` — the agent container (see Containment); `git-askpass.sh`
  supplies the repo PAT inside it.
- `todo.md`, `backlog.md`, `changelog.md` — tdd-mode planning and history.

## Build and test

Free to run without asking (read-only checks):

```text
zola build --output-dir <tmpdir>                                 # build (never into the repo)
zola serve [--drafts]                                            # local preview (host)
zola serve --drafts --interface 0.0.0.0 -u 127.0.0.1             # preview from the container
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

The modes and their rules come from the global instructions
(`~/.pi/agent/AGENTS.md`) and the skills: `/skill:pair`, `/skill:tdd-plan`
then `/skill:tdd-implement`, `/skill:unsupervised-goal` then
`/skill:unsupervised-run`. The default is **pair**. All three modes are
allowed in this repo; switching is jef's call.

What this repo adds:

- **Read-only checks** pair mode may run freely: `scripts/check`,
  `python3 tests/check_site.py`, `zola build --output-dir <tmpdir>` (never
  into the repo), `zola check`.
- **The Writing rule above applies in every mode**, unsupervised included.
  An unsupervised goal may build infrastructure or review prose; it may never
  draft it.
- **Unsupervised base branch:** `main`, but a run never pushes to it: it
  pushes its `agent/<slug>` branch and jef opens and merges the PR (merging
  deploys). The end-of-run test suite is `scripts/check` with
  `REQUIRE_NODE=1`.
- **Spend has two meters here.** `scripts/hero.py` paid commands spend the
  same OpenRouter key as pi. In an unsupervised run, count them against the
  goal's cap (`--max-cost` per call, plus `spend.py`), and don't run them at
  all unless the goal says so.

## Planning and progress files

`todo.md` (current session, 1–4 commit-sized items), `backlog.md` (persistent
ideas, triaged in planning), `changelog.md` (dated history, written by
`close-chunk`). Lasting knowledge goes in `notes/`.

## Containment

**Work inside the devcontainer** (`devcontainer up --workspace-folder .`,
then `devcontainer exec --workspace-folder . pi`). The properties below are
enforced by the container, not promised by this file: a session on the host
has the personal SSH key and defeats all of it. If a session is running
outside the container, say so before doing anything else.

### What the container enforces

- **No personal SSH key**, and no `ssh`, `scp`, `sftp`, `ssh-agent` or
  `rsync` binary. Git has no SSH transport.
- **One GitHub credential**: the repo-scoped PAT, mounted read-only. No other
  repo's PAT, no lab-bot GitHub credential.
- **One API key**: the lab-bot's spend-capped OpenRouter key at
  `~/.pi/agent/auth.json`, used by pi and by `scripts/hero.py`.
- **No `~/.aws`, `~/.azure`, `~/.config/lab-bot`, or host tool directory.**
- **`~/wiki/` is read-only.** The instructions, skills and
  `~/tools/spend.py` are read-only too.
- **No mail credentials.** The one writable path outside the workspace is
  `~/outbox`, where `notify-jef` drops a message for agentd on the host to
  check and send. The container can't choose the recipient.
- `--cap-drop=ALL`, `--security-opt=no-new-privileges:true`; port 1111 is
  published on the host's loopback only, for the preview.

Consequence: **the worst realistic outcome of a bad unattended run is commits
and `agent/*` branches in this repo, plus one notification to jef.** It can't
reach the live site, because only a merge to `main` deploys and `main` takes
changes only through a PR jef merges.

### Credentials

Agent sessions push as `jefwagner` with a fine-grained PAT scoped to
`jefwagner/jefwagner.github.io` only (Contents read/write; see the
`pat-setup` skill). It lives at `~/.config/jef/blog-pat` (mode 600, outside
the repo) and is mounted at the same path. `git-askpass.sh` reads it at call
time; `devcontainer.json` sets `GIT_ASKPASS`, `GIT_TERMINAL_PROMPT=0` and
`GIT_SSH_COMMAND=/bin/false`. The remote is HTTPS.

The PAT has **no Workflows permission**, so a push that changes
`.github/workflows/` is refused. CI and deploy changes are made by jef on the
host. If a git command prompts interactively, something is misconfigured:
stop and say so.

### Branches

- **`main` is the live site**: every push to it deploys. It rejects
  force-pushes and deletion (branch protection), which binds jef too.
- Agent work goes on `agent/<short-desc>` branches; posts on `post/<slug>`
  (`scripts/new_post.py`, `notes/post-workflow.md`). Never commit to `main`
  directly, and never push or merge to it unless jef asks in that same turn.
- Unattended work always runs in a worktree (the `unsupervised-run` skill).

### Residual risk

- **Spend.** `spend.py` and `hero.py --max-cost` report and refuse; nothing
  else interrupts. Treat a non-zero `spend.py` exit as a stop signal.
- **Damage within this repo.** `reset --hard`, `rm` and force-pushes to
  unprotected branches are still possible, hence worktrees and branches.
- **The prose rule is prose.** Nothing mechanical stops an agent from
  drafting text into `content/`. jef reviews every PR before it deploys,
  and that review is the only thing holding the line.
- **as-you-like-it is private** but its build ships publicly from
  `static/`. Don't add anything there beyond the unchanged build.

## Git

- Remote: jef's own **public** repo,
  `https://github.com/jefwagner/jefwagner.github.io`, over HTTPS.
- Commit identity comes from the repo-local git config. Style: short summary
  line, blank line, then a body.
- Never commit unless asked in that same turn. No history rewriting:
  merges and new commits only, never force-push.

## Wiki

`~/wiki/` is **mounted read-only**. Read it freely, but **never write to it,
and don't write wiki proposals.** The wiki is becoming a project catalog that
the orchestrator maintains. Things worth keeping go in `notes/` (the
`close-chunk` skill); unsupervised runs put them in the summary's "For the
catalog" section.
