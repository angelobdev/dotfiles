# Releasing

[← Docs](../README.md)

Installs follow releases, not `develop`, where the work lands. A release is an annotated tag `vMAJOR.MINOR.PATCH` on a commit of `develop`, the `stable` branch (the default branch on GitHub) moved to it, a section of [`CHANGELOG.md`](../../CHANGELOG.md) and a GitHub release with that section. Users see the section before they update (the repository card of the updates panel, the Repository line of `desktop-manager updates`) and once after it, in **What's new**.

## Versions

- **Patch** (`v1.0.1`): fixes only.
- **Minor** (`v1.1.0`): new features, new shortcuts, new options; nothing the user has to do.
- **Major** (`v2.0.0`): something the user may have to act on: a profile removed or renamed, a shortcut that now does something else, a setting moved. Its notes say what to do.

## Making a release

From a clone with `git config desktop.maintainer true` on `develop`, all of it merged and pushed:

```sh
./scripts/release.py draft v1.1.0      # a section from the commits since the last release (feat, fix, perf, refactor; --all for every commit)
$EDITOR CHANGELOG.md                   # paste it under the intro, newest first, and write it for users
git commit -m 'docs: changelog for v1.1.0' CHANGELOG.md && git push
./scripts/release.py publish v1.1.0    # checks, then asks before it pushes anything
```

`publish` refuses unless the version is newer than the last tag, `develop` is clean and equal to `origin/develop`, `CHANGELOG.md` at that commit has a non-empty `## v1.1.0 - DATE` section, `origin/stable` is an ancestor (a release only moves it forward) and `check.yml` passed on that commit (`gh run list`; `--skip-ci` when GitHub is down). Then it tags the commit with the section as the message, pushes the tag, pushes the commit to `stable` (and to each branch of `LEGACY`) and creates the GitHub release (`gh release create --verify-tag`).

Write the section for the person using the desktop: what they can now do and where, what looks or behaves differently, what was fixed that they may have met. Leave out refactors, tests and docs unless they change something visible. It is Markdown shown by Qt's `Text.MarkdownText` and by GitHub: headings `###`, lists, bold, inline code and links work in both. It stays in English, like every other text in the repository but the Italian catalog.

## Branches

- `develop`: the daily work, where pull requests go; CI runs on every push to it.
- `stable`: the default branch on GitHub, moved only by `publish`, so a plain `git clone` gets the latest release and the README on GitHub is the released one.
- `main`: what every clone followed before releases began (renamed to `develop` on 2026-11-26). The code those clones run follows only the branch they track, so `publish` moves a `main` with `stable` (`LEGACY` in `release.py`): their next update brings them the code that moves them to `stable`. Once the clones in use are on `stable`, empty `LEGACY` and delete `main` on GitHub; a clone still on it then follows `stable` anyway, as `channel.upstream()` does for a branch gone from the remote.

## How a clone follows them

`shell/.local/libexec/desktop/channel.py` is shared by `updates.py` (the update icon and Settings), `install-tui.py` (the updates screen and `--apply-updates`) and `about.py`:

- `upstream()`: the branch tracked and its remote; when that branch is gone from the remote, `origin/stable` takes its place.
- `target()`: after the fetch, the branch to follow is `<remote>/stable`; the upstream instead for a maintainer, or while the remote has no `stable` yet.
- `update_command()`: `git merge --ff-only <remote>/stable` on `stable`; `git switch -C stable --track <remote>/stable` for a clone still on another branch (offered only as a fast-forward: clean, nothing newer than `stable`).
- `version()`: `git describe --tags --abbrev=0 --match 'v[0-9]*'`, `''` before the first release.
- `between()`: the changelog sections after the installed version up to the new one, read from the new commit (`git show <remote>/stable:CHANGELOG.md`).
- `whats_new()`: the sections installed since `~/.local/state/desktop-shell/whats-new.json` (`seen`). With no file, a shell that has run update checks before (`updates.json` exists) sees the notes of every release up to its version once (it may come straight to a later one), and a new install records its version silently. A downgrade shows nothing.

`services/Release.qml` asks `channel.py whats-new` four seconds after the shell starts and after every update check (a pull ends with one), opens `panels/WhatsNewPanel.qml` when there is something, and records the version as seen (`channel.py seen`) when it closes. **About** asks `whats-new --current`, which does not record anything.

## Tests

`scripts/tests/test_channel.py` covers the parsing, the version order, the branch choice, What's new for a new install, an old install, an update over several releases and a downgrade, and the draft. `test_updates.py` and `test_install_tui.py` cover a clone following `stable`, the changelog of the new release and a clone newer than `stable`.
