"""Where the installer reads and writes, and the names it uses for the system: the repository, the manifest, its
record in $XDG_STATE_HOME/dotfiles, the session it sets up. In one place, so the tests redirect them once."""
import os
from pathlib import Path
import sys


# This file is scripts/install/install_paths.py.
REPO = Path(__file__).resolve().parents[2]
INSTALL = REPO / 'scripts/install'
PROFILES = ('core', 'hardware', 'tablet', 'plugins', 'apps', 'utils', 'assistant', 'containers', 'radio', 'gaming')
# On a 2-in-1 (touch_hardware) tablet joins them, and each profile brings its default parts: default_profiles().
DEFAULT_PROFILES = 'core,hardware,plugins'
# Units: a profile, or a part of one as profile.part ([<distro>.<profile>.parts.<part>] in the manifest), which load_plan
# makes a table of its own, so that every step, the record and removal work by unit as they do by profile.
MANIFEST = REPO / 'scripts/install/manifest.toml'
# USB vendors whose devices there are fingerprint readers: Synaptics, Goodix, Validity, Egis, FPC, FocalTech; Elan's
# readers are its 0c.. products (its other USB devices are touchscreens).
FINGERPRINT_VENDORS = {'06cb', '27c6', '138a', '1c7a', '10a5', '2808'}
MIN_FREE = 30 * 2**30
SESSION = 'hyprland-uwsm'
FLATHUB = 'https://dl.flathub.org/repo/flathub.flatpakrepo'
AUTOSTART = Path.home() / '.config/autostart/desktop-finish-install.desktop'
STAMP = Path.home() / '.local/state/dotfiles/hypr-plugins.json'
ACCOUNTS = 'org.freedesktop.Accounts'
STATE = Path(os.environ.get('XDG_STATE_HOME') or Path.home() / '.local/state') / 'dotfiles'
# What apply changed and what was there before, for uninstall: written before each step runs.
RECORD = STATE / 'install.json'
# The units the record names, one per line, for Lua and QML (save_units).
UNITS = STATE / 'units'
AUR = 'https://aur.archlinux.org/'

BOOT_SESSION = 'default session ' + SESSION
BOOT_GDM = 'enable gdm.service'
BOOT_TARGET = 'boot into graphical.target'
BOOT_AUTOSTART = 'finish the plugins at the first login'


sys.dont_write_bytecode = True
sys.path.insert(0, str(REPO / 'scripts/hyprpm'))


INTERFACE = STATE / 'interface-before-theme.ini'
