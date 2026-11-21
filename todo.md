# Session goal: port the thermo notes as the first post

Publish jef's `~/lab/thermo/notes/basics.md` as `/posts/thermo/`, listed (not
a draft). The prose is jef's and must come through unchanged; only math
delimiters change.

- Title: "Basics of thermodynamics" (jef's H1)
- Description (jef's words): "A physicist's ramblings to address some of the
  oft-skipped-over details about thermodynamics from a potential-first point
  of view"

Items:

- [x] **1. Converter script** `scripts/notes_to_post.py` (stdlib only): turns
      a notes file into a post. `$$...$$` blocks -> ```math fences; `$...$` ->
      `` `$...$` ``; existing code left alone; leading `# H1` -> front-matter
      `title`; refuses (naming the line) if the output would contain `{{` or
      `{%`. Reusable for future notes.
      *Done:* unit tests pass for table cells, `$$` with trailing spaces,
      math next to punctuation, an escaped `\$`, and inline math spanning a
      line break.
- [ ] **2. KaTeX render check** in `tests/check_site.py`: for each built post
      with `math = true`, run all its math through the vendored KaTeX in
      `node` with `throwOnError`. Skips (with a message) if `node` is missing.
      *Done:* passes on the fixture; fails on a fixture post with bad LaTeX.
- [ ] **3. Port `basics.md`** via the converter into
      `content/posts/thermo/index.md` (page bundle), `math = true`, listed.
      *Done:* site builds; KaTeX check passes on it; a one-off check shows
      undoing the delimiter conversion reproduces the source byte-for-byte
      (apart from the H1 moved into `title`).
