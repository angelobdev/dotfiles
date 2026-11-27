# Migrations

One-shot scripts for the state of a desktop that Stow links cannot reach: keys renamed in
`~/.config/desktop/shell.json`, files generated in `~/.local/state`, settings of other programs. Files the installer
writes outside the home are its `files` step's, which applies again on its own.

- Name: `YYYYMMDDhhmm-what-it-does.sh` (or `.py`), the time it was written; they run in that order.
- Each runs once per user, as the user, from the home folder, with `DOTFILES_REPO` set to the repository:
  at login (`desktop-session start`) and after a pull of the repository (the updates panel, the guided installer).
- Exit 0: done, recorded in `~/.local/state/dotfiles/migrations/`. Exit 75: not yet (what it needs is missing),
  the queue stops and tries again next time. Any other exit: a notification with its last line, and the queue
  stops until the next run. Output goes to `~/.local/state/dotfiles/migrations.log`.
- Write them to be safe to run on a desktop that never had the old state (a migration also runs on every desktop
  installed before it existed); a new install records every migration of its version as done.
- `python3 ~/.local/libexec/desktop/migrations.py pending` lists the ones still to run.
