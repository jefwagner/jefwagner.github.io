# todo

Session goal: a documented, tested procedure for authoring a post on its own
branch, previewing it locally (and over SSH), and shipping it through a PR to
`main` — ending with the new site live.

- [x] **One check command + CI on every push/PR.** Add `scripts/check` so
  that `check_site.py` and the converter tests run with one command under uv
  Python 3.12. Add a GitHub Actions workflow that builds with pinned Zola
  v0.23.6 and runs it with Node available, so the KaTeX render check runs
  instead of being skipped.
  Done: a pushed branch goes green; a throwaway bad-LaTeX commit goes red
  (then reverted).
- [x] **Deploy job.** On push to `main` (and `workflow_dispatch`), build and
  deploy via `actions/upload-pages-artifact` + `actions/deploy-pages`, gated
  on the checks passing.
  Done: workflow is valid and the deploy job is skipped on non-`main` pushes;
  its first real run is in the go-live item.
- [ ] **`scripts/new_post <slug>` + `notes/post-workflow.md`.** The script
  refuses a dirty tree or an existing slug/branch, fetches and creates
  `post/<slug>` from `origin/main`, writes `content/posts/<slug>/index.md`
  (placeholder title, today's date, `draft = true`, `[extra]` switches
  commented out; no prose), and prints next steps. Unit tests for it.
  The doc covers the whole procedure: scaffold, `zola serve --drafts`,
  remote authoring via `ssh -L 1111:localhost:1111` (verify whether Zola
  0.23 live-reload needs a second forwarded port), checks, un-drafting,
  push, PR, merge, deploy, verifying live, branch cleanup, and reverting a
  published post.
- [ ] **Go live + dry run.** PR `jef/new-blog-testing` → `main` following the
  doc; CI green; jef merges and switches the Pages source to "GitHub
  Actions"; verify live `/`, `/posts/thermo/`, `/as-you-like-it/`, `/flint/`.
  Then dry-run the post flow with a throwaway post: scaffold → serve (local
  and over SSH) → push → PR with CI → close unmerged, delete the branch.
  Commit: doc fixes from the friction found, plus the AGENTS.md status update
  (deployed, branch pushed, pointer to `notes/post-workflow.md`).
