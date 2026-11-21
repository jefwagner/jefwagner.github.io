# Session goal: Zola skeleton for the new blog

Fresh Zola site for jefwagner.github.io: builds locally, dark Ayu theme, math and
widget support. All prose is jef's; templates and stubs only carry
`TODO: jef writes this` placeholders.

- [x] **1. Commit the clean slate** so later items start from a clean tree:
      the staged removal of the old site, as-you-like-it moved to
      `static/as-you-like-it/`, plus a `.gitignore` for `public/`.
      *Done:* `git status` clean; only `static/as-you-like-it/` and
      `planning/` remain (plus `.gitignore`, `todo.md`, `backlog.md`).
- [x] **2. Minimal Zola site that builds**: `config.toml`, `base` / `index` /
      `section` / `page` templates, content stubs for `/`, `/posts/`, `/about/`.
      *Done:* `zola build` succeeds; posts live at `/posts/<slug>/`; landing
      page lists posts; `public/as-you-like-it/index.html` is byte-identical
      to the source.
- [x] **3. Theme: Ayu Dark, high contrast, editor-style.** One stylesheet with
      the palette as CSS variables; Ayu Dark by default, Ayu Light when the
      browser requests light (`prefers-color-scheme: light`). Sans for prose,
      monospace for code, a matching code-highlighting theme, and a hero-banner
      slot at the top of the page (solid block until a real image exists).
      *Done:* both modes render; body text and link colors meet WCAG AA
      contrast against their backgrounds.
- [x] **4. Math and widgets.** KaTeX auto-render with default (LaTeX-style)
      fonts; a `widget` shortcode that embeds a post's own JS / Plotly figure;
      a **draft** fixture post (placeholder text, an equation, a code block,
      one sample slider widget).
      *Done:* `zola serve --drafts` renders the fixture correctly; plain
      `zola build` excludes it.
