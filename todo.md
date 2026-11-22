# todo

Session goal: publish jef's landing and about text with the AI policy on its
own page, and bring hero-image generation from `~/lab/or-img-gen` into the
site, shipping the moonbase day/night banner.

- [ ] **Landing/about content + AI policy page + footer.** Commit jef's
  edited `_index.md`/`about.md` with the mechanical typo/grammar fixes. Move
  the AI policy verbatim to `content/ai-policy.md` (`/ai-policy/`); the
  landing keeps the intro and gets a `TODO: jef writes this` pointer line.
  Add a small site footer in `base.html` linking `/ai-policy/`. Tests:
  drop `test_placeholders_only`; footer link on every page; policy page
  builds. Housekeeping: flint docs are live, so drop the `/flint/` 404
  note in AGENTS.md.
- [ ] **Light-mode hero variant.** `[extra] hero_image_light` (site and
  per-page, same override rules as `hero_image`), applied under
  `prefers-color-scheme: light`; with no light image, light mode is a solid
  colour even if a dark image is set (one image can't pass AA in both
  modes). Tests for both modes, override, and fallback.
- [ ] **Port `hero_gen` as `scripts/hero/` with a small CLI.** Module from
  the lab (OpenRouter client, prompts, crop, contrast, export, site
  geometry) plus a CLI for generate / twin / export with the contrast and
  cost report; deps (Pillow, numpy, requests) declared inline for
  `uv run`, so the site tests stay stdlib-only. Its tests join
  `scripts/check` (no network, no spend). Key read from the env, never
  logged. Commit `planning/hero-image-handoff.md` as history.
- [ ] **Ship the moonbase banner.** Moonbase night/day pair from
  `or-img-gen/out/export/` into `static/img/`, set as the site-wide hero;
  an image credit in the footer per jef's AI policy (wording is jef's:
  placeholder until written). Verify both modes at phone and desktop widths
  with `zola serve`.
