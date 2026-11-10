"""Where the theme lives and where it goes: the state, config and data folders theme.py and its modules
read and write, in one place, so the tests redirect them once (theme_paths.STATE = <a temporary folder>)."""
import os
from pathlib import Path


HOME = Path.home()


STATE = Path(os.environ.get('XDG_STATE_HOME') or HOME / '.local/state') / 'desktop-theme'


DATA = Path(os.environ.get('XDG_DATA_HOME') or HOME / '.local/share') / 'desktop'


CONFIG = Path(os.environ.get('XDG_CONFIG_HOME') or HOME / '.config') / 'desktop'


# User themes override the ones shipped by the dotfiles.
THEME_DIRS = (CONFIG / 'themes', DATA / 'themes')


TEMPLATES = DATA / 'templates'


BTOP = Path(os.environ.get('XDG_CONFIG_HOME') or HOME / '.config') / 'btop'


# qtXct have no include: their whole config is rendered (fonts, icons, colours), like btop's theme.
QTCT = tuple(Path(os.environ.get('XDG_CONFIG_HOME') or HOME / '.config') / f'{v}/{v}.conf' for v in ('qt5ct', 'qt6ct'))


VSCODE = Path(os.environ.get('XDG_CONFIG_HOME') or HOME / '.config') / 'Code/User/settings.json'


VSCODE_EXTENSIONS = HOME / '.vscode/extensions'


# Downloaded theme wallpapers live outside the repository; wallpaper.py owns applying them.
WALLPAPERS = DATA / 'wallpapers'


SELECTION = Path(os.environ.get('XDG_STATE_HOME') or HOME / '.local/state') / 'desktop-session/wallpaper/selection.json'


WALLPAPER = Path(__file__).resolve().with_name('wallpaper.py')


USER_FONTS = Path(os.environ.get('XDG_DATA_HOME') or HOME / '.local/share') / 'fonts'


# Thumbnails make every format the gallery shows previewable (Qt lacks WebP here) and keep 8K
# wallpapers from being decoded at full size by the panel.
THUMBS = Path(os.environ.get('XDG_CACHE_HOME') or HOME / '.cache') / 'desktop-theme/thumbs'


# The Herdr app (herdr.dev) redraws itself from files in ~/.config/herdr-app: the desktop theme becomes its theme
# "desktop" (themes/desktop.json, terminal and panel colors), and settings.json points at it with the desktop's
# fonts. A key of settings.json is changed only while it is unset or still what was written here last
# (STATE/herdr-app.json): a theme or font picked in Herdr itself stays. A settings.json that does not parse is
# left alone. Herdr reloads both live.
HERDR = Path(os.environ.get('XDG_CONFIG_HOME') or HOME / '.config') / 'herdr-app'
