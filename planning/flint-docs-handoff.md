# Handoff: serve flint docs from the flint repo's own GitHub Pages site

Prompt for a fresh agent session. Work in pair mode: discuss each step with
jef and get approval before each write or state-changing command.

## Background

- jef's user site `jefwagner.github.io` (repo `jefwagner/jefwagner.github.io`)
  is being rebuilt from scratch with Zola. Today it serves the flint docs as
  **committed build output** in its `flint/` folder, at
  `https://jefwagner.github.io/flint/`.
- Those docs come from the repo `jefwagner/numpy-flint` (public, default
  branch `main`). They are Sphinx 7.2 docs with the `furo` theme and
  `sphinx.ext.autodoc`, sourced from `docs/` (`conf.py`, `index.rst`,
  `usage.rst`, `python_api.rst`, `c_api.rst`, `c_ext.rst`, `devel.rst`).
- The goal is for the flint repo to build and deploy its own docs to its own
  GitHub Pages project site, so the user site no longer carries a copy.

## Key fact: the rename preserves the URL

A project Pages site is served at `https://jefwagner.github.io/<repo-name>/`.
jef will **rename `numpy-flint` to `flint`**, so the project site lands at
`https://jefwagner.github.io/flint/`, the URL that already appears in:

- `pyproject.toml` → `[project.urls] Homepage`
- `readme.md` (two links to the "project homepage")

So no redirects are needed and existing links keep working.

- The **PyPI package name stays `numpy-flint`**. A repo rename doesn't affect
  PyPI or `pip install numpy-flint`.
- GitHub redirects the old repo URL (`github.com/jefwagner/numpy-flint`) to
  the new name, including git remotes. Still update URLs that name the repo
  directly, e.g. the "Bug Tracker" URL in `pyproject.toml` (points at
  `.../numpy-flint/issues`). Update local clones with
  `git remote set-url origin https://github.com/jefwagner/flint.git`.

## Steps

1. **Rename the repo** `numpy-flint` → `flint` (jef does this in the GitHub
   UI, Settings → General → Repository name). Update local remotes.
2. **Add a docs workflow** `.github/workflows/docs.yml` that, on push to
   `main` (plus `workflow_dispatch`):
   - sets up Python and installs the package plus `sphinx` and `furo`;
   - builds the docs (`sphinx-build -b html docs <outdir>`);
   - uploads with `actions/upload-pages-artifact` and deploys with
     `actions/deploy-pages` (needs `permissions: pages: write,
     id-token: write`, and an `environment: github-pages`).
   - **Watch out:** `autodoc` imports the module, and flint is a C extension.
     The package must actually be built and installed in the job
     (`pip install .`) before `sphinx-build`, or the API pages come out empty.
     Check that the build output's API pages contain the documented members.
3. **Enable Pages** for the repo: Settings → Pages → Source: **GitHub
   Actions**.
4. **Verify** `https://jefwagner.github.io/flint/` serves the new build. A
   project site takes precedence over a same-named folder in the user site, so
   it should win even while the old copy still exists in
   `jefwagner.github.io/flint/`. Check a few deep links (`usage.html`,
   `python_api.html`), and the search page.
5. **Report back** so the `flint/` folder can be dropped from the user-site
   rebuild. That happens in the other session, not this one.

## Out of scope (mention, don't do)

- `build_wheels.yml` uses deprecated runners (`ubuntu-20.04`, `macos-11`,
  `windows-2019`) and `actions/upload-artifact@v3`, which GitHub has retired.
  The wheel build probably no longer runs. Flag this to jef as possible
  follow-up work, but don't change it as part of this task.

## Definition of done

- Repo is named `flint`; local remotes updated.
- A docs workflow builds the docs (with populated API pages) and deploys them
  on push to `main`.
- `https://jefwagner.github.io/flint/` serves the docs from the flint repo.
- `pyproject.toml` URLs are correct for the new repo name.
