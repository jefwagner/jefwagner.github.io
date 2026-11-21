# Backlog

- GitHub Actions deploy workflow (pinned Zola v0.23.6); switch Pages source
  to "GitHub Actions" only when merging to `main`.
  With it: one command that runs both test suites under uv Python 3.12, and
  Node in CI so the KaTeX render check runs instead of being skipped.
- Thermo post leftovers (optional review points from
  `~/lab/thermo/notes/basics-comments.md`, now applying to
  `content/posts/thermo/index.md`): drop "(up to a sign)" in the Legendre
  section; name $1/T$ in the reservoir result. jef's prose to write.
- Scrollytelling page template (sticky graphic panel + steps).
- Hero-image generation script via OpenRouter image models (possibly its own
  lab experiment).
- Move this clone out of `~/lab/thermo/` (it currently shows as untracked
  there).
- RSS/Atom feed and favicon.
- Single source for vendored versions: KaTeX and Plotly versions are in both
  `templates/base.html` paths and `static/vendor/` dir names; move them to
  `config.toml [extra]` so an upgrade is one edit.
- Styled 404 page (currently Zola's bare default).
- Manual light/dark theme toggle (currently follows the browser). Note:
  Giallo writes `color-scheme: light dark` inline on every `<pre>`, so code
  blocks would ignore a toggle; set `add_color_scheme = false` under
  `[markdown.highlighting]` and drive `color-scheme` from the toggle.
