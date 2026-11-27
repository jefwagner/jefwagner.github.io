# Changelog

## 2026-11-22: content, AI policy page, hero banner

jef's own landing and about text is live, his AI policy has its own page,
and the site has its first hero banner, made with tooling brought in from
the `or-img-gen` lab experiment (PR #5).

- Content: jef's landing intro and about page (mechanical fixes only); his
  AI policy moved word for word to `/ai-policy/`, linked from a new site
  footer. The hero title is "Jef with one *f*" (`[extra] hero_title`,
  inline markdown); tab titles stay "Jef Wagner".
- Light-mode hero: `hero_image` / `hero_image_light` are a day/night pair,
  chosen together, because the lab found no single image keeps the hero
  text at WCAG AA in both colour modes. `hero_credit` (footer image credit,
  required by jef's AI policy) travels with its pair; a page with its own
  pair never inherits the site's light image or credit.
- `scripts/hero.py` + `scripts/hero_gen/`: generate / twin (paid, capped
  per call), check and export (offline, contrast-gated into `static/img/`),
  models, spend. Never prints or logs the key; sends a generic app title.
  Its tests (no network, no spend) run in `scripts/check` via uv's PEP 723
  support, so the other suites stay stdlib-only. Prompts still DRAFT.
- Moonbase banner (Nano Banana): 2880x360 WebP, 73/72 KB; a test keeps the
  configured pair passing contrast and under 150 KB.
- flint docs are live from the flint repo's own Pages site.
- Learned: Zola 0.23 uses Tera 2 (no `concat`; strings built in `set` are
  autoescaped); a new deploy can look broken for up to 10 minutes because
  Pages serves `style.css` with `max-age=600` (hard refresh).

## 2026-11-21 (third chunk): post workflow and go-live

The new site is live, deployed by GitHub Actions from `main`, and adding a
post now has a documented, tested path: its own branch, local preview
(also over SSH), PR with CI, merge = deploy.

- `scripts/check` runs every test suite; the `site` workflow runs it on
  every push and PR with pinned Zola v0.23.6 (sha256-verified) and Node,
  and `REQUIRE_NODE=1` makes CI fail rather than skip the KaTeX render
  check. Deploy is a separate job, gated on the checks, from `main` only,
  and never builds drafts.
- `scripts/new_post.py <slug>` creates `post/<slug>` from a freshly
  fetched `origin/main` with a draft page bundle (placeholders only),
  refusing on a dirty tree or a slug/branch already in use.
- `notes/post-workflow.md` is the procedure, refined by a full dry run
  with a throwaway post (PR #2, closed unmerged). Learned: Zola 0.23
  serves live-reload on the serve port, so one `ssh -L` forward is
  enough, but both ends must use the same port number; and nothing yet
  catches a `TODO` title in an un-drafted post (backlog).
- Go-live (PR #1): Pages source switched to GitHub Actions *before*
  merging, so the legacy builder never ran Jekyll over the Zola sources.
  `/flint/` is 404 until the flint docs handoff (backlog); `/resume/` and
  the other old pages are gone on purpose.
- Gotchas: `astral-sh/setup-uv` publishes no moving major tag (pinned
  `v10.4.0`); the local `gh` is 2.4 (no `gh run list --branch`).

## 2026-11-21 (second chunk): first post

Published jef's thermo notes as the first post, `/posts/thermo/`
("Basics of thermodynamics"), with the prose unchanged.

- `scripts/notes_to_post.py` converts a notes file into a post: rewrites
  only math delimiters and moves the H1 into the title, and refuses Tera
  syntax or ambiguous math instead of guessing. Reusable for future notes.
- KaTeX render check (`tests/katex_check.js`, run by the site tests when
  `node` is available): every math expression on every built math page is
  rendered with `throwOnError`, since Zola never validates LaTeX.
- The post is now the source of truth for the article; the copy in
  `~/lab/thermo/notes/` is no longer the one to edit.

## 2026-11-21

Rebuilt jefwagner.github.io from scratch as a Zola blog skeleton, on branch
`jef/new-blog-testing` (not yet deployed; `main` still serves the old site).

- Cleared the old resume site. as-you-like-it (private repo) is now served
  from `static/as-you-like-it/` at the same URL; flint docs move to the flint
  repo's own Pages site (handoff in `planning/flint-docs-handoff.md`);
  transforms and termcanvas docs were dropped.
- Minimal Zola 0.23.6 site: landing page with post list, `/posts/<slug>/`,
  `/about/`. All prose is TODO placeholders for jef to write.
- Theme: Ayu Dark by default, Ayu Light when the browser prefers light,
  WCAG AA contrast enforced by tests (a few Ayu colors adjusted). Code
  highlighting uses ayu-dark / github-light, because ayu-light's syntax
  colors fail AA. Hero banner slot, system fonts.
- Math via KaTeX, written as code (```math fences and `$...$` inline code)
  so Zola's markdown can't mangle it. Interactive widgets via a Tera
  component plus self-hosted Plotly basic. Both opt-in per post.
- Discovered on the way: Zola 0.23 removed shortcodes (now Tera components)
  and templates post content, so a literal `{{` needs `{% raw %}`. See
  `notes/post-conventions.md`.
- `tests/check_site.py`: 30 stdlib build checks
  (`python3 tests/check_site.py`).
