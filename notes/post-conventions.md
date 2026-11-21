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
| `hero_image = "img/x.png"` | banner image for this post (path under `static/`) |

## Math: write it as code

Zola's markdown parser has no math support and mangles LaTeX before
KaTeX sees it (`|_{` became `<em>`, `\,` lost its backslash, `\\` became
`\`). Code is never processed, so math is written as code:

- display: a ```` ```math ```` fenced block
- inline: inline code that starts and ends with `$`, e.g. `` `$U_{\text{tot}}$` ``

Porting notes written with plain `$...$` / `$$...$$` (like the thermo notes)
is a mechanical conversion. GitHub renders ```` ```math ```` fences natively.

## Zola 0.23 gotchas

- **Content is templated.** A literal `{{` or `{%` anywhere in a post, even in
  a code or math block, is Tera syntax and fails the build. Wrap it in
  `{% raw %}...{% endraw %}`. LaTeX hits this with `{{`, e.g.
  `\frac{1}{{a+b}}`; often just `{ {` or dropping redundant braces avoids it.
  (`skip_content_templating` in config can turn this off per file.)
- **No shortcodes.** They were removed in 0.23; use Tera components
  (`templates/components.html`).

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
