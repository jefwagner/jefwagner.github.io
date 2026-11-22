# Post workflow: branch → preview → PR → deploy

The procedure for authoring a post on its own branch, previewing it
locally (or on a remote machine over SSH), and shipping it to the live
site through a PR to `main`. For *how to write* a post (front matter
switches, math as code, widgets, Zola 0.23 gotchas) see
[post-conventions.md](post-conventions.md).

The short version:

```text
python3 scripts/new_post.py <slug>           # branch post/<slug> + draft bundle
zola serve --drafts                          # write, preview at :1111
scripts/check                                # all checks
# remove draft = true, set the date
git push -u origin post/<slug>
gh pr create --base main --fill              # CI runs on the PR
gh pr merge --squash --delete-branch         # merge = deploy
```

## How the pieces fit

- `main` is the live site. Every push to `main` runs the `site` workflow
  (`.github/workflows/site.yml`): the `check` job builds and runs
  `scripts/check`, and only if that passes does the `deploy` job publish
  to GitHub Pages. A red check means nothing is deployed.
- Every push to any other branch, and every PR to `main`, runs the same
  checks but never deploys. So a post branch gets CI feedback as soon as
  it is pushed, before a PR exists.
- `draft = true` posts are left out of every non-`--drafts` build,
  including the deploy. A draft merged to `main` by accident is invisible
  on the live site.
- Local `zola serve` is the preview. There are no deployed PR previews.
- Non-post changes (templates, CSS, scripts, docs) take the same path:
  any branch name, PR to `main`, merge. Nothing is pushed to `main`
  directly.

## 1. Start the post

From a clean working tree (any branch):

```text
python3 scripts/new_post.py <slug> [--title "Your title"]
```

- `<slug>` becomes the URL, `/posts/<slug>/`: lowercase letters and
  digits joined by single hyphens (`heat-engines`).
- It fetches `origin`, then refuses (and changes nothing) if the working
  tree has any modified or untracked file, if `post/<slug>` already
  exists locally or on `origin`, or if `content/posts/<slug>` (bundle or
  `.md`) already exists on the base.
- Otherwise it creates branch `post/<slug>` from the freshly fetched
  `origin/main` (with no upstream yet), so a stale local `main` doesn't
  matter and writes `content/posts/<slug>/index.md`: a draft with
  placeholder title and description, today's date, and the `[extra]`
  switches commented out. Nothing is committed or pushed.
- `--base REF` branches from something other than `origin/main`;
  `--no-fetch` skips the fetch (offline).

Commit the scaffold together with your first real edit.

## 2. Write and preview

```text
zola serve --drafts
```

Open `http://127.0.0.1:1111/posts/<slug>/`. `--drafts` is what makes
the post visible while it is still `draft = true`. The page reloads on
every save (content, templates, `static/`, `config.toml`).

Uncomment the `[extra]` switches the post needs (`math = true` for any
math). Images and widget JS go in the bundle folder next to `index.md`.

### Remote authoring over SSH

When the repo lives on another machine, run `zola serve` there and
forward its port to your laptop:

```text
# on the remote machine (in the repo)
zola serve --drafts

# on your laptop
ssh -L 1111:localhost:1111 <host>
```

then open <http://127.0.0.1:1111/> on the laptop. Add `-N` to the
`ssh` command to forward without opening a shell.

- **One port is enough.** Zola 0.23 serves live-reload on the same port
  as the site (the injected script connects to `window.location.hostname`
  on the *serve* port), so reload-on-save works through the tunnel.
- **Keep the two port numbers the same.** The serve port is written into
  every page (links and the live-reload script), so `-L 8080:localhost:1111`
  loads the first page but breaks links and reload. If 1111 is taken on
  either side, move both: `zola serve --drafts -p 2222` with
  `ssh -L 2222:localhost:2222 <host>`.
- `zola serve` binds to `127.0.0.1` by default, which is what the tunnel
  wants; no `--interface` needed.

## 3. Check

```text
scripts/check
```

Runs everything CI runs: the site build checks (including the KaTeX
render check, which fails on bad LaTeX that Zola itself accepts) and the
script unit tests. Locally, the KaTeX check is skipped if `node` is
missing; in CI it is required.

## 4. Make it publishable

Before opening the PR, in the post's front matter:

- remove `draft = true`,
- set `date` to the publish date (the post list sorts by it),
- replace the `TODO` title and description. **No check catches a
  leftover `TODO` here**, so read the front matter.

Then confirm it shows **without** `--drafts`: stop the server and run
plain `zola serve`. The post should be in the list on `/` and at
`/posts/<slug>/`. Run `scripts/check` again.

(A deliberately unfinished post can also be merged with `draft = true`
kept; it just won't appear on the site.)

## 5. Push and open a PR

```text
git push -u origin post/<slug>
gh pr create --base main --fill
```

- The push alone starts CI on the branch; `gh run list --limit 3` shows
  it.
- `--fill` takes the PR title and body from the commits; edit them in
  the browser or drop `--fill` to be prompted.
- The PR shows the `site / check` result. Wait for green before
  merging. A red run: `gh run view <id> --log-failed`.
- Pushing more commits to the branch updates the PR and re-runs CI.

## 6. Merge = deploy

```text
gh pr merge --squash --delete-branch
```

- Squash keeps `main` at one commit per post, which is also what makes
  undoing a post a single revert (step 8).
- `--delete-branch` deletes the remote branch and the local one, and
  switches you to your local `main`, which is now behind; see step 8.
- The merge pushes to `main`, which runs `check` again and then
  `deploy`. Watch it:

```text
gh run list --limit 3          # find the run on main
gh run watch <id> --exit-status
```

Note: the `gh` here is 2.4 (Ubuntu's package), which has no `--branch`
filter on `gh run list` and no `gh pr revert`; the commands in this
doc are the ones that work with it.

## 7. Verify live

```text
curl -sI https://jefwagner.github.io/posts/<slug>/ | head -1   # HTTP/2 200
```

then look at it in a browser: the post, its math/widgets, and its entry
on the landing page. Pages can take a minute after the deploy job
finishes; a hard refresh beats the browser cache.

## 8. Clean up, or undo a post

Clean up after a merge (`--delete-branch` has already left you on
`main`):

```text
git pull --ff-only          # local main catches up with the merge
git fetch --prune           # drops the stale origin/post/<slug> ref
```

If the branch wasn't deleted by `--delete-branch`:

```text
git branch -D post/<slug>
git push origin --delete post/<slug>
```

To abandon a post that has a PR open: `gh pr close <number>
--delete-branch` (same branch cleanup, nothing merged), then the two
commands above.

To take a published post down:

- **Hide it, keep it:** on a new branch set `draft = true`, PR, merge.
- **Remove it entirely:** revert the squash commit, then PR and merge
  the revert:

  ```text
  git switch -c revert-<slug> origin/main
  git revert <squash-commit-sha>
  git push -u origin revert-<slug>
  gh pr create --base main --fill
  ```

Either way the next deploy takes it off the site. Never push directly to
`main`: it deploys, so go through a PR.

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `new_post: refusing to start the post: working tree is not clean` | commit, stash, or delete the listed files first; untracked files count |
| post missing from `zola serve` | still `draft = true`: use `zola serve --drafts` |
| build error mentioning Tera / `{{` | a literal `{{` or `{%` in the post (often LaTeX); see post-conventions, "Zola 0.23 gotchas" |
| build error about an unknown language | every code fence needs a known language; `text` for plain |
| `KatexRender` fails in `scripts/check` or CI | the log names the page and expression; fix the LaTeX |
| CI red at "Set up job" | an action version doesn't resolve; check the annotation |
| `test_zola_version_matches_local` fails | local Zola differs from the CI pin: bump `ZOLA_VERSION` and `ZOLA_SHA256` in the workflow (or install the pinned Zola) |
| live page unchanged after merge | deploy still running or failed (`gh run list`), or browser cache |
