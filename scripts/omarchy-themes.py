#!/usr/bin/env python3
"""The themes of Omarchy (basecamp/omarchy) as shipped themes of this desktop, in shell/.local/share/desktop/themes.

Each Omarchy theme becomes <id>/theme.json: its colors.toml through theme_import.convert (the same conversion as
`desktop-theme import`), its vscode.json as the VS Code theme (VS Code's Default Modern without one), the GTK accent nearest to its accent colour, and its
backgrounds as wallpapers fetched on demand: links pinned to the last Omarchy commit that had them in the repository
(they now ship as a package of their own), each with its sha256, and with the loop and the intro Omarchy has for a
still (omacom/omarchy-themes-loops and -intros, MIT, pinned the same way). A background that shows Omarchy's name or
logo is left out. A shipped theme of the same id is replaced; the
desktop's own themes (glass, glass-light, graphite, high-contrast) are never touched. Omarchy's catppuccin is the
Mocha variant: it becomes catppuccin-mocha, the id the desktop already uses.

    scripts/omarchy-themes.py OMARCHY_CHECKOUT [--ref SHA] [--cache DIR] [--dry-run]

OMARCHY_CHECKOUT is a clone of basecamp/omarchy (its themes/ folder gives the colours); nothing in it runs.
The backgrounds (and their listings) are downloaded once into the cache folder to compute their checksums;
GITHUB_TOKEN, when set, lifts the API limit of 60 anonymous calls an hour.
"""
import argparse
import colorsys
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tomllib
import urllib.request

ROOT = Path(__file__).resolve().parent.parent
THEMES = ROOT / 'shell/.local/share/desktop/themes'
sys.path.insert(0, str(ROOT / 'shell/.local/libexec/desktop'))
import theme_import  # noqa: E402

# The parent of b20666c ("Ship the theme backgrounds from omarchy-themes-backgrounds"): the last commit with
# themes/*/backgrounds in the repository.
BACKGROUNDS_REF = 'c2ea2d87ce0330a318c7bd9e8c6352b7bfa29d35'
# The videos of a still, by its name without the leading number: a loop plays in its place, an intro once before it.
VIDEOS = {'loop': ('omacom/omarchy-themes-loops', '4c158ea83f4e30d1653a345f66e4e85e990a93c8'),
          'intro': ('omacom/omarchy-themes-intros', 'fd582b322ae09e4e3beae1456f0f9a168d4ceb2b')}
# Backgrounds with Omarchy's name or its OMA logo on them.
BRANDED = re.compile(r'(^|-)oma(rchy)?(-|$)')
OWN = {'glass', 'glass-light', 'graphite', 'high-contrast'}
IDS = {'catppuccin': 'catppuccin-mocha'}
NAMES = {'catppuccin': 'Catppuccin Mocha', 'rose-pine': 'Rosé Pine', 'retro-82': 'Retro 82'}
IMAGES = ('.jpg', '.jpeg', '.png', '.webp')
# GTK (libadwaita) accent colours by hue, in degrees.
ACCENTS = (('red', 0), ('orange', 30), ('yellow', 50), ('green', 120), ('teal', 175), ('blue', 215), ('purple', 270),
           ('pink', 325), ('red', 360))
AGENT = {'User-Agent': 'dotfiles-theme-sync'}


def get(url):
    headers = dict(AGENT)
    # The API allows 60 anonymous calls an hour; a token (GITHUB_TOKEN, `gh auth token`) lifts that.
    if url.startswith('https://api.github.com/') and os.environ.get('GITHUB_TOKEN'):
        headers['Authorization'] = 'Bearer ' + os.environ['GITHUB_TOKEN']
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=60) as response:
        return response.read()


def accent_name(value):
    red, green, blue = (int(value[i:i + 2], 16) / 255 for i in (1, 3, 5))
    hue, lightness, saturation = colorsys.rgb_to_hls(red, green, blue)
    if saturation < 0.2 or lightness < 0.12 or lightness > 0.92:
        return 'slate'
    degrees = hue * 360
    return min(ACCENTS, key=lambda accent: abs(accent[1] - degrees))[0]


def stem(name):
    return re.sub(r'^\d+[-_ ]*', '', Path(name).stem)


def videos(cache):
    """{kind: {theme: {name: path in its repository}}} from the trees of the video repositories, by the full name of the
    file without its extension ("1-white")."""
    found = {}
    for kind, (repository, ref) in VIDEOS.items():
        saved = cache / f'{kind}-tree-{ref}.json'
        if not saved.is_file():
            saved.parent.mkdir(parents=True, exist_ok=True)
            saved.write_bytes(get(f'https://api.github.com/repos/{repository}/git/trees/{ref}?recursive=1'))
        found[kind] = {}
        for item in json.loads(saved.read_text())['tree']:
            path = item['path']
            if item['type'] == 'blob' and path.count('/') == 1 and path.endswith('.mp4'):
                theme_name, name = path.split('/')
                found[kind].setdefault(theme_name, {})[Path(name).stem] = path
    return found


def match(clips, name, files):
    """The video of a still: the one of its full name, else the only one of its name without the number, when no other
    still of the theme has that name too (White has 1-white, 2-white and 3-white, and one video for 1-white)."""
    if Path(name).stem in clips:
        return clips[Path(name).stem]
    if sum(stem(other) == stem(name) for other in files) > 1:
        return None
    found = [path for clip, path in clips.items() if stem(clip) == stem(name)]
    return found[0] if len(found) == 1 else None


def video(kind, path, cache):
    repository, ref = VIDEOS[kind]
    url = f'https://raw.githubusercontent.com/{repository}/{ref}/{path}'
    local = cache / kind / path
    if not local.is_file():
        local.parent.mkdir(parents=True, exist_ok=True)
        local.write_bytes(get(url))
    return {'url': url, 'sha256': hashlib.sha256(local.read_bytes()).hexdigest()}


def wallpapers(theme, ref, cache, clips=None):
    """The backgrounds of a theme at ref, as theme.json wallpaper entries, numbered in their order."""
    saved = cache / theme / f'listing-{ref}.json'
    if not saved.is_file():
        saved.parent.mkdir(parents=True, exist_ok=True)
        saved.write_bytes(get(f'https://api.github.com/repos/basecamp/omarchy/contents/themes/{theme}/backgrounds?ref={ref}'))
    listing = json.loads(saved.read_text())
    files = sorted(entry['name'] for entry in listing if entry['type'] == 'file' and entry['name'].lower().endswith(IMAGES)
                   and not entry['name'].lower().startswith('omarchy.') and not BRANDED.search(stem(entry['name']).lower()))
    entries = []
    for number, name in enumerate(files, 1):
        url = f'https://raw.githubusercontent.com/basecamp/omarchy/{ref}/themes/{theme}/backgrounds/{name}'
        local = cache / theme / name
        if not local.is_file():
            local.parent.mkdir(parents=True, exist_ok=True)
            local.write_bytes(get(url))
        rest = re.sub(r'^\d+[-_ ]*', '', name)
        item = {'file': f'{number:02d}-{rest}', 'url': url, 'sha256': hashlib.sha256(local.read_bytes()).hexdigest(), 'source': 'omarchy'}
        for kind, by_theme in (clips or {}).items():
            path = match(by_theme.get(theme, {}), name, files)
            if path:
                item[kind] = video(kind, path, cache)
        entries.append(item)
    return entries


def theme(folder, ref, cache, clips=None):
    omarchy_id = folder.name
    name = NAMES.get(omarchy_id) or ' '.join(word.capitalize() for word in omarchy_id.split('-'))
    result = theme_import.convert(tomllib.loads((folder / 'colors.toml').read_text()), name)
    result['system']['accentColor'] = accent_name(result['palette']['accent'])
    vscode = folder / 'vscode.json'
    if vscode.is_file():
        data = json.loads(vscode.read_text())
        result['vscode'] = {'theme': data['name']} | ({'extension': data['extension']} if data.get('extension') else {})
    else:
        # VS Code's own theme for the mode, so it does not keep the colours of the theme before.
        result['vscode'] = {'theme': 'Default Light Modern' if result['mode'] == 'light' else 'Default Dark Modern'}
    result['wallpapers'] = wallpapers(omarchy_id, ref, cache, clips)
    return IDS.get(omarchy_id, omarchy_id), result


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('checkout', type=Path)
    parser.add_argument('--ref', default=BACKGROUNDS_REF)
    parser.add_argument('--cache', type=Path, default=Path('/tmp/omarchy-backgrounds'))
    parser.add_argument('--dry-run', action='store_true')
    options = parser.parse_args()
    folders = sorted(path.parent for path in (options.checkout / 'themes').glob('*/colors.toml'))
    if not folders:
        sys.exit(f'No themes/*/colors.toml in {options.checkout}')
    clips = videos(options.cache)
    for folder in folders:
        theme_id, data = theme(folder, options.ref, options.cache, clips)
        if theme_id in OWN:
            print(f'skip {theme_id}: a theme of the desktop')
            continue
        target = THEMES / theme_id / 'theme.json'
        print(f'{"replace" if target.is_file() else "add":8} {theme_id:18} {data["mode"]:5} {data["system"]["accentColor"]:7} '
              f'{len(data["wallpapers"])} wallpapers, {sum("loop" in w for w in data["wallpapers"])} loops, '
              f'{sum("intro" in w for w in data["wallpapers"])} intros')
        if not options.dry_run:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')


if __name__ == '__main__':
    main()
