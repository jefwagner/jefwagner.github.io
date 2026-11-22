# Post conventions (Zola 0.23.6)

Working notes: how to write a post on this site, and the non-obvious
reasons behind each rule. Update when a convention changes.

## Layout

- A post is `content/posts/<slug>.md`, or a page bundle
  `content/posts/<slug>/index.md` with its own files next to it (widget JS,
  images). Both serve at `/posts/<slug>/`. Use a bundle whenever the post
  has widgets.
- Needs a `date` (the post list is sorted by date, newest first).
- `draft = true` keeps it out of `zola build`; preview with
  `zola serve --drafts`.

## Front matter switches (`[extra]`)

| Key | Effect |
|---|---|
| `math = true` | loads KaTeX + `static/math.js` |
| `plotly = true` | loads Plotly basic and `static/widgets.js` |
| `widgets = true` | loads `static/widgets.js` only (non-Plotly widgets) |
| `hero_image = "img/x.webp"` | banner image for this post, dark mode (path under `static/`) |
| `hero_image_light = "img/y.webp"` | light-mode banner; only used with this post's own `hero_image` |
| `hero_credit = "..."` | footer image credit for this post's own pair (inline markdown) |

Hero images come as a day/night pair: no single image keeps the hero text
readable in both colour schemes. A post that sets `hero_image` without
`hero_image_light` gets a solid colour in light mode, never the site's
light image; likewise it shows its own `hero_credit` or none, never the
site's.

## Math: write it as code

Zola's markdown parser has no math support and mangles LaTeX before
KaTeX sees it (`|_{` became `<em>`, `\,` lost its backslash, `\\` became
`\`). Code is never processed, so math is written as code:

- display: a ```` ```math ```` fenced block
- inline: inline code that starts and ends with `$`, e.g. `` `$U_{\text{tot}}$` ``

GitHub renders ```` ```math ```` fences natively.

## Porting notes into a post

Notes written with plain `$...$` / `$$...$$` convert mechanically:

```text
python3 scripts/notes_to_post.py NOTES.md content/posts/<slug>/index.md \
    --date YYYY-MM-DD [--description "..."] [--draft] [--no-math]
```

- Rewrites only math delimiters and moves the leading `# Title` into the
  front matter; the prose is copied unchanged. Display math must sit on its
  own `$$` lines.
- Refuses (naming the source line) rather than guessing: `{{`/`{%`, unclosed
  `$` or `$$`, `$$` inside a paragraph, backticks inside inline math.
- Won't overwrite an existing post without `--force`.
- After porting, the post is the source of truth; edit it, not the notes.

## Checks

```text
python3 tests/check_site.py                                    # site build checks
uv run --no-project --python 3.12 tests/test_notes_to_post.py  # converter (needs 3.11+)
```

The site checks include a KaTeX render check: every math expression on
every page that loads KaTeX is rendered with `throwOnError`, so bad LaTeX
fails the tests instead of showing a red error on the live page. It needs
`node` (found on `PATH` or under `~/.nvm`) and is skipped without it.

## Zola 0.23 gotchas

- **Content is templated.** A literal `{{` or `{%` anywhere in a post, even in
  a code or math block, is Tera syntax and fails the build. Wrap it in
  `{% raw %}...{% endraw %}`. LaTeX hits this with `{{`, e.g.
  `\frac{1}{{a+b}}`; often just `{ {` or dropping redundant braces avoids it.
  (`skip_content_templating` in config can turn this off per file.)
- **No shortcodes.** They were removed in 0.23; use Tera components
  (`templates/components.html`).
- **Templates (Tera 2):** some Tera 1 filters are gone (e.g. `concat`; the
  build fails with "Unknown filter"), and a string built with `~` in a
  `{% set %}` is autoescaped on output, so quotes become `&#39;`. Write
  literal markup (quotes, `url('...')`) as template text and interpolate
  only the values, as the hero `style` attribute in `base.html` does.

## Widgets

```
{{ <widget src="name.js" height={360} /> }}
```

`name.js` sits in the page bundle and is an ES module:

```js
export default function mount(el) { /* build the figure inside el */ }
```

- Read theme colors from CSS tokens (`getComputedStyle(...).getPropertyValue("--fg")`)
  so the figure matches dark and light mode. Colors are read once at mount.
- Plotly is a global (`Plotly`) when `plotly = true`.
- A widget that throws shows an error in its own box; others still mount.
- Reference: `content/posts/fixture-math-widgets/` (draft fixture).

## Code blocks

Every fenced block needs a known language (`error_on_missing_language`);
a typo fails the build. Use `text` for plain text.
