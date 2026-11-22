# Hero images

How hero banners are made for this site. The tool is `scripts/hero.py`
(package `scripts/hero_gen/`), ported from the lab experiment
`~/lab/or-img-gen`. The experiment's full findings, models tried, and the
exploration notebook stay there: `~/lab/or-img-gen/notes/findings.md`.

## What the site needs

- A **day/night pair** per banner: `hero_image` (dark mode, the default
  scheme) and `hero_image_light`. No single image keeps the hero text
  (`--hero-fg`) at WCAG AA in both schemes: dark-mode text needs a
  background luminance ≤ 0.072, light-mode text ≥ 0.696. Override rules are
  in `post-conventions.md`.
- Shape: **8:1, 2880×360 WebP (q75)**, around 50–100 KB. The hero is about
  190 CSS px tall and full width, and `background-size: cover` crops it: a
  phone shows only the centre ~quarter, a 2560px screen crops the top and
  bottom.
- Composition that survives the crop: dense detail only in the outer fifths,
  a thin strip of small activity along the bottom edge across the full
  width, plain sky everywhere else (the text sits left of centre).

## Workflow

```text
uv run scripts/hero.py models                                   # free
uv run scripts/hero.py generate --theme moonbase --palette night  # ~$0.06
uv run scripts/hero.py twin hero-work/gen/<night>.jpg --to day    # ~$0.06
uv run scripts/hero.py check hero-work/gen/<img>.jpg --mode dark  # offline
uv run scripts/hero.py export hero-work/gen/<night>.jpg --name hero-<x>-night --mode dark
uv run scripts/hero.py export hero-work/gen/<day>.jpg   --name hero-<x>-day   --mode light
uv run scripts/hero.py spend
```

- `generate` takes `--theme` (see `hero_gen/prompts.py`), `--post SLUG`
  (title and description as the subject, optionally `--setting THEME`), or
  `--subject TEXT`. Default model `google/gemini-nano-banana-2.1` at native
  8:1, 2K: about $0.06 per image, roughly half of rolls usable.
- Generate the night image first, then `twin` it to day (an edit of the same
  scene); look at both, since twins sometimes smear or ghost.
- `check` prints the 5th-percentile contrast behind the nav (needs 4.5) and
  title (needs 3.0) at five viewport widths, and writes a preview sheet to
  `hero-work/previews/`. The preview font is an approximation.
- `export` crops, resizes and writes `static/img/<name>.webp`, refuses if
  contrast fails (`--force` to override) or the name exists, and prints the
  front-matter line to paste.
- Paid commands refuse before sending if the expected cost exceeds
  `--max-cost` (default $0.50). Every request is logged to
  `hero-work/cost_log.jsonl`. `hero-work/` is gitignored.
- The key comes from `$OPENROUTER_API_KEY` (or the lab devcontainer's
  `~/.pi/agent/auth.json`) and is never printed or logged.

## Attribution

Hero images are AI-generated, which jef's AI policy (`/ai-policy/`) lists as
acceptable with attribution, so a banner on the site needs a credit:
`hero_credit` in `config.toml` for the site pair, or in a post's front
matter next to its own pair. The footer shows it while that pair is in use
(inline markdown, so it can link to the policy). The wording is jef's.

The site banner is the moonbase pair (`static/img/hero-moonbase-*.webp`),
exported from the lab's raw Nano Banana generations.

## Open

- The prompt texts in `hero_gen/prompts.py` are still marked DRAFT, pending
  jef's approval.
- `background-position: center bottom` would keep the bottom strip on very
  wide screens (backlog).
