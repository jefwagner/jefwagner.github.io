# Backlog

- flint docs handoff: `/flint/` is 404 since go-live (2026-11-21), and it is
  the PyPI homepage for numpy-flint. Run `planning/flint-docs-handoff.md` in
  the flint repo (rename to `flint`, own Pages site).
- Thermo post leftovers (optional review points from
  `~/lab/thermo/notes/basics-comments.md`, now applying to
  `content/posts/thermo/index.md`): drop "(up to a sign)" in the Legendre
  section; name $1/T$ in the reservoir result. jef's prose to write.
- Scrollytelling page template (sticky graphic panel + steps).
- Hero-image generation script via OpenRouter image models (possibly its own
  lab experiment).
- RSS/Atom feed and favicon.
- Single source for vendored versions: KaTeX and Plotly versions are in both
  `templates/base.html` paths and `static/vendor/` dir names; move them to
  `config.toml [extra]` so an upgrade is one edit.
- Styled 404 page (currently Zola's bare default).
- Manual light/dark theme toggle (currently follows the browser). Note:
  Giallo writes `color-scheme: light dark` inline on every `<pre>`, so code
  blocks would ignore a toggle; set `add_color_scheme = false` under
  `[markdown.highlighting]` and drive `color-scheme` from the toggle.
- Publish-readiness check for posts: fail when a non-draft post still has
  a `TODO` title/description/body (found in the go-live dry run: an
  un-drafted scaffold passes every check), and warn when a PR to `main`
  still contains `draft = true` posts (harmless, since drafts aren't built,
  but easy to forget to flip).
