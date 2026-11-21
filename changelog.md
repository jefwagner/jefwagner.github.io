# Changelog

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
