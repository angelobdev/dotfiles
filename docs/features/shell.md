# Terminal shell

[← Docs](../README.md)

zsh is the login shell of whoever installs the desktop: the `core` profile installs it with its plugins and sets it with `usermod --shell /usr/bin/zsh` (the `shell` step). The new shell applies from the next sign-in; kitty and every terminal take it from the account.

## What you get

- **Prompt:** Powerlevel10k in the upstream lean style with 8 colors, on two lines: directory and Git state above, `❯` below; on the right the exit code, the duration of slow commands, background jobs, tool versions where relevant, and the time. The 8 ANSI colors come from the terminal palette, so the prompt follows the desktop theme. Icons come from kitty's built-in Nerd Font symbols, with no font to install.
- **Completion:** zsh-autocomplete lists matches while you type; `Tab` and the arrows move through them.
- **Suggestions:** zsh-autosuggestions shows the rest of a past command in grey; `→` or `End` accepts it.
- **Syntax highlighting:** commands turn green when they exist and red when they do not, before you press Enter.
- **fzf:** `Ctrl + R` searches the history, `Ctrl + T` inserts a file, `Alt + C` enters a directory.
- **zoxide:** `z part-of-a-path` jumps to the directory used most that matches; `zi` picks one with fzf.
- **eza and bat:** `ls`, `ll` (long, with Git state), `la` (hidden files too) and `tree` use eza; `cat` uses bat, which prints files with highlighting in a terminal and as they are in a pipe.
- **History:** 50,000 commands in `~/.local/state/zsh/history`, shared between open shells, without duplicates or commands typed with a leading space.

## Files

| Path | Role |
| --- | --- |
| `zsh/.zshenv` | Read by every zsh, scripts included: points `ZDOTDIR` to `~/.config/zsh` and puts `~/.local/bin` first in `PATH`. It prints nothing, since GDM starts the session through the login shell |
| `zsh/.config/zsh/.zshrc` | The interactive setup, in load order: instant prompt, history, zsh-autocomplete (it runs `compinit`, so nothing else does), autosuggestions, fzf, zoxide, aliases, Powerlevel10k, syntax highlighting last |
| `zsh/.config/zsh/p10k.zsh` | Sources the upstream `p10k-lean-8colors.zsh` and changes only the clock (`HH:MM`, at the end of the right prompt) |
| `~/.config/zsh/local.zsh` | Optional, outside the repository: machine-specific additions, read last |

zsh, zsh-autosuggestions, zsh-syntax-highlighting, fzf, zoxide, eza and bat are Fedora packages. Fedora packages neither Powerlevel10k nor zsh-autocomplete, so the manifest pins them as `clones` of `core`: the `clones` step fetches each pinned commit, as the user and without sudo, into `~/.local/share/zsh/plugins/`. To update one, put the new commit in `scripts/install/manifest.toml` and run `./scripts/install-desktop.py apply`. On its first start Powerlevel10k downloads its `gitstatusd` helper from GitHub into `~/.cache/gitstatus` (checked against the hashes in its `install.info`); without it, Git state in the prompt still works, more slowly.

To change the prompt, edit `p10k.zsh`; `p10k configure` writes `~/.p10k.zsh` instead, which this setup does not read. A different login shell for one account: `sudo usermod --shell /bin/bash <user>`; the installer sets zsh again on its next `apply`.
