# Handoff: hero-image generation via OpenRouter (lab experiment)

Prompt for a fresh agent session in a new lab experiment (`newlab init`,
suggested name `hero-gen`). Use it to design the experiment with jef and
write its `AGENTS.md` Project summary, following `~/lab/AGENTS.md`. Then
work in whatever mode jef picks there (pair by default).

## Background

- jef's site, `https://jefwagner.github.io`, is a Zola 0.23.6 blog (repo
  `jefwagner/jefwagner.github.io`, local clone `~/github-pages`). Every page
  has a **hero banner**: a full-width header with the site nav and the site
  title on top of it. It's a solid color block today, and it can show an
  image instead.
- The site wants a way to make hero images for the site and per post,
  without hand-editing images every time. The idea is to generate them with
  image models through OpenRouter. It's a lab experiment because the
  model/prompt/cost questions are open and may go nowhere.

## How the site uses a hero image (facts from the site repo)

- **Selection:** `config.toml` `[extra] hero_image = ""` is the site-wide
  image, and a post overrides it with `[extra] hero_image = "img/x.png"`
  in its front matter. Paths are relative to `static/`, so files go in
  `static/img/`. Empty means a solid color.
- **Rendering** (`templates/base.html`, `static/style.css`): the image is a
  CSS `background-image` on `<header class="hero">` with
  `background-size: cover; background-position: center`. It's purely
  decorative, with no `<img>` and no alt text. The nav links and the site
  title (`2.25rem`, bold) sit **on top of the image** in the `--hero-fg`
  color, inside a centered `42rem` column.
- **Shape:** the banner spans the full viewport width and is short, about
  170px tall by estimate (padding `1rem` top and `3rem` bottom, the nav, and
  the title with `2.5rem` top margin). Measure it in a browser to be sure.
  So it's very wide: roughly 8:1 to 11:1 on desktop and about 2:1 on a
  phone, and `cover` crops whatever doesn't fit around the center. Image
  models generate a few fixed aspect ratios, so expect to crop. The center
  band has to work on its own.
- **Light and dark mode:** the site follows the browser. The same image is
  used in both modes, but the text on top changes color:
  - dark: `--hero-fg #E6B450` (Ayu orange) on fallback `--hero-bg #131721`
  - light: `--hero-fg #8F5000` (dark orange) on fallback `--hero-bg #F3F4F5`

  An image has to keep that text readable, and the site's tests enforce WCAG
  AA (4.5:1) for its own color pairs (`tests/check_site.py` has a contrast
  helper). One image can't easily suit both a light and a dark text color.
  Figuring out how to handle that is part of the experiment (see the
  questions below).
- **Weight:** the image loads on every page that uses it, so file size
  matters. WebP or well-compressed PNG/JPEG, at a sensible width (around
  1920–2560px), are worth measuring.

## OpenRouter access

- Lab devcontainers mount a **lab-specific OpenRouter key** (not the host
  key) read-only at `~/.pi/agent/auth.json`, from host
  `~/.config/lab-bot/pi-auth.json`. Read the key from there or pass it in
  through an env var. Never commit it, print it, or log it.
- Image generation costs money per image. Track spend per run, and agree a
  cap with jef before any batch generation. An unsupervised run needs the
  spend cap in its `goal.md`.
- Which models generate images, the request format, and pricing all change
  often. **Check them against OpenRouter's current docs and model list**
  rather than relying on memory or this file.

## Questions the experiment should answer

1. Which OpenRouter image model(s) give usable banner art for this site's
   look (Ayu palette, calm, low-detail behind text), and at what cost per
   image?
2. How do you get a usable very wide banner: generate wide and crop,
   outpaint, tile, or compose? What survives `cover` cropping across phone
   and desktop widths?
3. How do you keep the nav and title readable in **both** color modes? Some
   options: constrain the image to a luminance band and check contrast in
   the text region, darken or lighten it in post-processing, or have the
   site support light and dark variants or a CSS overlay. The last one
   would be a change to the site repo, so report back rather than doing it
   (see below).
4. What should the script take as input: a free prompt from jef, a post's
   front matter (title and description, which jef writes), or a fixed
   site-style preamble plus a subject? And what does it output: a file in
   `static/img/` plus the front-matter line to paste?

## Constraints carried over from the site

- **The site's prose is jef's.** The script can *read* a post's title and
  description as prompt input, but it must never write or rewrite site
  content beyond the `hero_image` path. Prompts and style choices get jef's
  approval.
- **Keep the experiment self-contained** (lab rule). Don't edit
  `~/github-pages` from the lab session. Produce images and a script there,
  and report what the site needs.
- The site's tests require every color pair to pass WCAG AA. If the script
  checks contrast, reuse the same definition (relative luminance, 4.5:1 for
  normal text; the title is large text, so 3:1 also applies).

## Definition of done

- A script (lab repo) that turns an approved prompt or a post's metadata
  into a banner image sized and compressed for the hero, with the cost of
  each generation reported.
- A short findings note in the lab's `notes/`: the models tried, cost per
  usable image, the cropping approach, the contrast approach, and what
  failed.
- At least one generated banner jef likes, checked on the local site:
  copy it into `~/github-pages/static/img/`, set `hero_image`, and look at
  it with `zola serve` in both color modes at phone and desktop widths.
  That check happens in a site session, not the lab.
- A report back to the site repo saying what to integrate: where the
  script should live (port it to `scripts/` or keep it in the lab) and any
  template or CSS changes needed. Those are done in a site session through
  the usual PR workflow (`notes/post-workflow.md`).

## Out of scope (mention, don't do)

- Site template or CSS changes (variants, overlays, responsive
  `srcset`/Zola `resize_image`): propose them, and the site session does
  them.
- Social or Open Graph preview images. These are related but separate.
- Writing the site's backlog or changelog. The site session updates them
  when this lands.
