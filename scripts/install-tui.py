#!/usr/bin/env python3
"""Guided install-desktop.py: install the desktop, keep it updated, or remove it, reviewing each change first."""
from argparse import ArgumentParser
from collections import namedtuple
from contextlib import redirect_stderr, redirect_stdout
import curses
import getpass
import importlib.util
import io
import json
import locale
import os
from pathlib import Path
import platform
import shlex
import shutil
import subprocess
import sys
import textwrap
import threading

REPO = Path(__file__).resolve().parent.parent
sys.dont_write_bytecode = True
_spec = importlib.util.spec_from_file_location('install_desktop', REPO / 'scripts/install-desktop.py')
installer = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(installer)
sys.path.insert(0, str(REPO / 'scripts/hyprpm'))
import bundle  # noqa: E402

# One line each; docs/guide/installation.md has the long version.
DESCRIPTIONS = {
    'core': 'Hyprland, Quickshell, GDM with the hyprland-uwsm session, portals, audio, network, fonts and zsh: the desktop itself.',
    'hardware': 'Firmware, video decoding, cameras and power of a recent Intel laptop, fingerprint reader, firewall zone, sshd off.',
    'tablet': 'A 2-in-1: screen rotation, stylus, sign-in without the fingerprint reader while folded, touchscreen gestures (Hyprgrass).',
    'plugins': 'What building the Hyprland plugins needs, from RPM Fusion too; the RPM Fusion ffmpeg replaces ffmpeg-free.',
    'apps': 'Zen Browser, 1Password, VS Code, Neovim, gh, glab, uv, gcc and a few command-line tools.',
    'herdr': 'The Herdr app and herdr-core in ~/.local: the assistant console for any coding agent; they update themselves.',
    'containers': 'Docker (moby-engine, docker-compose, the docker group) and Tailscale.',
    'media': 'Loupe, Papers and Showtime for images, PDFs and videos.',
    'gaming': 'Steam, gamescope and the 32-bit drivers games need.',
    'steam-hidpi': 'The Steam launcher that scales the client for the monitor it opens on.',
    'codecs': 'The RPM Fusion codecs in place of the free builds: ffmpeg, intel-media-driver, GStreamer freeworld, OpenH264, HEIF, aptX.',
}
PLUGIN_STATES = {
    bundle.CURRENT: 'built for this Hyprland and up to date',
    bundle.MISSING: 'not built yet',
    bundle.INCOMPLETE: 'a rebuild stopped halfway: it runs again at the next login',
    bundle.PACKAGING_CHANGED: 'their packaging changed: rebuilt at the next login, before they load',
    bundle.COMPOSITOR_CHANGED: 'Hyprland was updated: rebuilt at the next login, before they load',
    bundle.UNVERIFIED: 'this Hyprland build is not verified for them yet: they stay off',
    bundle.MISMATCHED: 'hyprland and hyprland-devel differ: finish the update, they stay off until then',
}
MIN_SIZE = (16, 60)
PALETTE = (('accent', curses.COLOR_CYAN), ('warn', curses.COLOR_YELLOW), ('error', curses.COLOR_RED), ('ok', curses.COLOR_GREEN))
UP = (curses.KEY_UP, 'k')
DOWN = (curses.KEY_DOWN, 'j')
ENTER = ('\n', '\r', curses.KEY_ENTER)
BACK = ('\x1b', 'b', curses.KEY_LEFT)
ERASE = (curses.KEY_BACKSPACE, '\x7f', '\b')
SUDO_REFRESH = 60

# One step as the review found it: error is why its check failed, output what the check printed.
Review = namedtuple('Review', 'title items error output')
# What of one profile is on this system: missing names what is not, out of total things it sets up.
Status = namedtuple('Status', 'missing total')


def stow_files(package):
    root = REPO / package
    return [path for path in sorted(root.rglob('*')) if path.is_file()] if root.is_dir() else []


def linked(package, path):
    target = Path.home() / path.relative_to(REPO / package)
    return target.is_symlink() and target.resolve() == path.resolve()


def profile_status(plan, name):
    # Only what can be seen without sudo: its packages, its swaps, its AUR packages, its archives and its Stow links.
    one = plan._replace(profiles=(name,))
    wanted = list(dict.fromkeys(installer.wanted_packages(one)))
    missing = (installer.packages_pending(one) if wanted else []) + installer.swaps_pending(one)
    missing += [item.split()[0] for item in installer.aur_pending(one)]
    missing += [item.split()[0] for item in installer.archives_pending(one)]
    links = [(package, path) for package in plan.table[name].get('stow', ()) for path in stow_files(package)]
    missing += [str(path.relative_to(REPO)) for package, path in links if not linked(package, path)]
    return Status(missing, len(wanted) + len(installer.swaps(one)) + len(installer.merged(one, 'aur')) + len(installer.merged(one, 'archives'))
                  + len(links))


def installed(status):
    return bool(status.total) and not status.missing


def status_label(status):
    if installed(status):
        return 'installed'
    if status.total and len(status.missing) < status.total:
        return f'{status.total - len(status.missing)}/{status.total}'
    return ''


def preselected(statuses):
    # On a desktop already set up, what it has; on a fresh system, the defaults.
    if not installed(statuses['core']):
        return tuple(installer.default_profiles().split(','))
    return tuple(name for name in installer.PROFILES if name == 'core' or installed(statuses[name]))


def status_text(status):
    if installed(status):
        return 'Installed. Turning it off removes nothing: the installer never uninstalls.'
    if status_label(status):
        shown = ', '.join(status.missing[:6]) + (', ...' if len(status.missing) > 6 else '')
        return f'Partly installed ({status_label(status)}); missing: {shown}.'
    return 'Not installed.'


def toggled(profiles, name):
    # core is the desktop itself and never goes. The order stays the one of PROFILES, which the manifest merges in.
    if name == 'core':
        return tuple(profiles)
    chosen = set(profiles) ^ {name}
    return tuple(profile for profile in installer.PROFILES if profile in chosen)


def summary(table, name):
    profile = table.get(name, {})
    parts = [f'{len(profile["packages"])} packages'] if profile.get('packages') else []
    for key, label in (('repos', 'repositories'), ('services', 'services'), ('groups', 'groups'), ('stow', 'links')):
        if profile.get(key):
            parts.append(f'{label}: {", ".join(profile[key])}')
    if profile.get('aur'):
        parts.append('from the AUR: ' + ', '.join(item['package'] for item in profile['aur']))
    if profile.get('swaps'):
        parts.append('replaces ' + ', '.join(f'{old} with {new}' for old, new in profile['swaps']))
    return '; '.join(parts) + '.' if parts else ''


def removing(plan):
    # An uninstall plan carries the record of what to undo.
    return plan.record is not None


def command(plan, action='apply'):
    if removing(plan):
        return f'./scripts/install-desktop.py {action} --uninstall'
    words = ['./scripts/install-desktop.py', action, '--profiles', ','.join(plan.profiles)]
    if plan.firmware:
        words += ['--firmware', shlex.quote(plan.firmware)]
    return ' '.join(words)


def firmware_items(plan):
    # The vendor blobs this model still needs; none unless tablet is chosen and the model matches.
    return installer.firmware_needed(plan)


def missing_firmware(plan, items):
    return [item for item in items if not installer.firmware_source(plan, item)]


def review_step(plan, step):
    # Captured: a check that prints would scribble over the screen.
    output = io.StringIO()
    try:
        with redirect_stdout(output):
            items = step.pending(plan)
        error = ''
    except (subprocess.CalledProcessError, RuntimeError, OSError) as failure:
        items, error = [], str(failure)
    return Review(step.title, items, error, output.getvalue().strip())


def review_warnings(plan, reviews):
    if removing(plan):
        warnings = installer.record_notes(plan)
    else:
        try:
            warnings = installer.preflight_warnings(plan)
        except OSError as error:
            warnings = [str(error)]
    for review in reviews:
        warnings += [line.removeprefix('Warning: ') for line in review.output.splitlines() if line.strip()]
    return warnings


def review_rows(reviews, expanded):
    # Every row names the step it belongs to, so Enter on a detail line folds its step.
    rows = []
    for index, review in enumerate(reviews):
        if review.error:
            status, style, details = 'check failed', 'error', review.error.splitlines()
        elif review.items:
            status, style, details = f'{len(review.items)} to do', 'accent', review.items
        else:
            status, style, details = 'nothing to do', 'dim', []
        mark = ('-' if index in expanded else '+') if details else ' '
        rows.append((index, f'{mark} {review.title:<10} {status}', style))
        if index in expanded:
            rows += [(index, '      ' + line, 'error' if review.error else 'dim') for line in details]
    return rows


def clip(text, width):
    return text if len(text) <= width else text[:max(width - 3, 0)] + '...'


def first_work(reviews):
    # The cursor starts where there is something to look at.
    return next((index for index, entry in enumerate(reviews) if entry.items or entry.error), 0)


def complete(text):
    # Directory names only: the field asks for a directory.
    if text in ('', '~'):
        return '~/'
    head, slash, prefix = text.rpartition('/')
    base = Path(os.path.expanduser(head + slash)) if slash else Path.cwd()
    try:
        names = sorted(path.name for path in base.iterdir() if path.is_dir() and path.name.startswith(prefix)
                       and (prefix.startswith('.') or not path.name.startswith('.')))
    except OSError:
        return text
    if not names:
        return text
    # What every name starts with: sorted, the first and the last differ the most.
    shared = next((index for index, pair in enumerate(zip(names[0], names[-1])) if pair[0] != pair[1]), min(len(names[0]), len(names[-1])))
    completed = head + slash + names[0][:shared]
    return completed + '/' if len(names) == 1 else completed


class Screen:
    def __init__(self, window):
        self.window = window
        self.styles = {'dim': curses.A_DIM, 'bold': curses.A_BOLD}
        window.keypad(True)
        self.cursor(False)
        if curses.has_colors():
            curses.use_default_colors()
            for index, (name, color) in enumerate(PALETTE, 1):
                curses.init_pair(index, color, -1)
                self.styles[name] = curses.color_pair(index)

    def style(self, name):
        return self.styles.get(name, 0)

    def cursor(self, visible):
        try:
            curses.curs_set(1 if visible else 0)
        except curses.error:
            pass

    def size(self):
        return self.window.getmaxyx()

    def put(self, row, column, text, style=0):
        height, width = self.size()
        if 0 <= row < height and 0 <= column < width:
            try:
                self.window.addnstr(row, column, text, width - column, style)
            except curses.error:
                # Writing the bottom right cell moves the cursor out of the window: the text is there anyway.
                pass

    def wrap(self, row, text, style=0, indent=2):
        width = max(self.size()[1] - indent - 2, 20)
        for line in textwrap.wrap(text, width) or ['']:
            self.put(row, indent, line, style)
            row += 1
        return row

    def frame(self, title, keys):
        # The first body row, or None when the terminal is too small to draw anything useful.
        self.window.erase()
        height, width = self.size()
        if height < MIN_SIZE[0] or width < MIN_SIZE[1]:
            self.put(0, 0, f'Enlarge the terminal to {MIN_SIZE[1]}x{MIN_SIZE[0]} (Ctrl+C quits).')
            return None
        self.put(0, 0, f' Desktop installer - {title}'.ljust(width), curses.A_REVERSE | curses.A_BOLD)
        self.put(height - 1, 1, keys, self.style('dim'))
        return 2

    def footer(self, text, style):
        height, width = self.size()
        self.put(height - 1, 0, ' ' * width)
        self.put(height - 1, 1, text, self.style(style) | curses.A_BOLD)

    def key(self):
        self.window.refresh()
        return self.window.get_wch()


def system_lines():
    release = installer.os_release()
    return (
        ('System', f'{release.get("PRETTY_NAME", "unknown")}, {platform.machine()}'),
        ('Model', installer.dmi('product_name') or 'unknown'),
        ('User', getpass.getuser()),
        ('Free on /', f'{shutil.disk_usage("/").free // 2**30} GiB'),
        ('Repository', str(REPO)),
        ('Plugins', PLUGIN_STATES[bundle.status()]),
    )


def post_pending():
    # The first login of a new install opens a terminal for this; once it has finished, there is nothing to finish.
    return bool(os.environ.get('HYPRLAND_INSTANCE_SIGNATURE')) and installer.AUTOSTART.exists()


def menu_entries():
    # Updates only once there is a desktop to update.
    entries = [('install', 'Install or update the desktop', 'Choose the profiles, review what is left to do, then apply it.')]
    if installer.desktop_present():
        entries.append(('updates', 'Check for updates', 'System packages, Flatpak apps, AUR packages and zsh plugins newer '
                        'than their pins, and this repository: see what is new, check what to take, apply it.'))
    if post_pending():
        entries.append(('post', 'Finish the installation', 'Build the Hyprland plugins and list what is left to do by hand.'))
    entries.append(('uninstall', 'Remove the desktop', 'Undo what the installer set up: plugins, login, links and settings, '
                    'then the packages and repositories it added. From a console, with Hyprland logged out.'))
    entries.append(('quit', 'Quit', 'Leave without changing anything.'))
    return entries


def menu(ui):
    entries = menu_entries()
    lines = system_lines()
    cursor = 0
    while True:
        row = ui.frame('Welcome', 'Up/Down move   Enter select   q quit')
        if row is None:
            ui.key()
            continue
        row = ui.wrap(row, 'Turns this system into the desktop of this repository. Nothing changes until you confirm the plan.') + 1
        for label, value in lines:
            ui.put(row, 2, label, ui.style('dim'))
            ui.put(row, 14, value)
            row += 1
        row += 1
        for index, (_, title, _) in enumerate(entries):
            ui.put(row, 2, ('> ' if index == cursor else '  ') + title, curses.A_REVERSE if index == cursor else 0)
            row += 1
        ui.wrap(row + 1, entries[cursor][2], ui.style('dim'))
        key = ui.key()
        if key in UP:
            cursor = (cursor - 1) % len(entries)
        elif key in DOWN:
            cursor = (cursor + 1) % len(entries)
        elif key in ENTER:
            return entries[cursor][0]
        elif key in ('q', '\x1b'):
            return 'quit'


def detect(ui, plan):
    statuses = {}
    for index, name in enumerate(installer.PROFILES):
        row = ui.frame('Profiles', 'Ctrl+C quits')
        if row is not None:
            ui.wrap(row, f'Looking for the profiles already on this system ({index + 1}/{len(installer.PROFILES)}): {name}')
            ui.window.refresh()
        statuses[name] = profile_status(plan, name)
    return statuses


def choose_profiles(ui, plan, mode, statuses, preset=False):
    profiles = tuple(plan.profiles)
    cursor = 0
    found = installed(statuses['core'])
    if mode == 'post':
        intro = 'Choose the profiles you installed: plugins builds the Hyprland plugins.'
    elif preset:
        intro = 'The profiles given with --profiles start on' + ('; i chooses the installed ones' if found else '') + '. core always stays on.'
    elif found:
        intro = 'The profiles found on this system start on. core is the desktop itself and always stays on.'
    else:
        intro = 'Choose what to install. core is the desktop itself and always stays on.'
    defaults = tuple(installer.default_profiles().split(','))
    keys = 'Up/Down move   Space toggle   d defaults   ' + ('i installed   ' if found else '') + 'Enter continue   Esc back   q quit'
    while True:
        row = ui.frame('Profiles', keys)
        if row is None:
            ui.key()
            continue
        row = ui.wrap(row, intro) + 1
        for index, name in enumerate(installer.PROFILES):
            selected = index == cursor
            box = '[*]' if name == 'core' else '[x]' if name in profiles else '[ ]'
            ui.put(row, 2, ('> ' if selected else '  ') + f'{box} {name}', curses.A_REVERSE if selected else 0)
            ui.put(row, 21, status_label(statuses[name]), ui.style('ok' if installed(statuses[name]) else 'warn'))
            ui.put(row, 33, clip(DESCRIPTIONS[name], ui.size()[1] - 35), ui.style('dim'))
            row += 1
        name = installer.PROFILES[cursor]
        row += 1
        ui.put(row, 2, name + ('  (default)' if name in defaults else '  (opt-in)'), ui.style('accent') | curses.A_BOLD)
        row = ui.wrap(row + 1, DESCRIPTIONS[name])
        row = ui.wrap(row, summary(plan.table, name), ui.style('dim'))
        ui.wrap(row, status_text(statuses[name]), ui.style('ok' if installed(statuses[name]) else 'dim'))
        key = ui.key()
        if key in UP:
            cursor = (cursor - 1) % len(installer.PROFILES)
        elif key in DOWN:
            cursor = (cursor + 1) % len(installer.PROFILES)
        elif key == ' ':
            profiles = toggled(profiles, name)
        elif key == 'd':
            profiles = defaults
        elif key == 'i' and found:
            profiles = preselected(statuses)
        elif key in ENTER:
            return 'next', profiles
        elif key in BACK:
            return 'back', profiles
        elif key == 'q':
            return 'quit', profiles


def choose_firmware(ui, plan, items):
    text = plan.firmware or ''
    position = len(text)
    status, style = 'Leave it empty to go on without it.', 'dim'
    try:
        while True:
            row = ui.frame('Vendor firmware', 'Enter search and continue   Tab complete   Esc back')
            if row is None:
                ui.key()
                continue
            for item in items:
                row = ui.wrap(row, f'{item["purpose"]} needs {Path(item["target"]).name}, which nobody may redistribute.', curses.A_BOLD)
                ui.put(row, 4, 'From  ' + item['source'], ui.style('dim'))
                ui.put(row + 1, 4, 'To    ' + item['target'], ui.style('dim'))
                row += 3
            row = ui.wrap(row, 'Give a directory with a copy: the file is found by its hash, in subdirectories too, whatever its name.') + 1
            ui.put(row, 2, 'Directory')
            width = ui.size()[1] - 16
            start = max(0, position - width + 1)
            ui.put(row, 14, text[start:start + width].ljust(width), curses.A_UNDERLINE)
            ui.wrap(row + 2, status, ui.style(style))
            ui.window.move(row, 14 + position - start)
            ui.cursor(True)
            key = ui.key()
            if key in ENTER:
                if not text.strip():
                    return 'next', None
                folder = Path(text.strip()).expanduser()
                if not folder.is_dir():
                    status, style = f'{folder} is not a directory.', 'error'
                    continue
                ui.footer('Searching...', 'accent')
                ui.window.refresh()
                lacking = missing_firmware(plan._replace(firmware=text.strip()), items)
                if not lacking:
                    return 'next', text.strip()
                names = ', '.join(Path(item['target']).name for item in lacking)
                status, style = f'No copy of {names} in {folder}. Fix the directory, or empty it to go on without it.', 'error'
            elif key == '\x1b':
                return 'back', text.strip() or None
            elif key == '\t':
                text = complete(text)
                position = len(text)
            elif key in ERASE:
                if position:
                    text, position = text[:position - 1] + text[position:], position - 1
            elif key == curses.KEY_DC:
                text = text[:position] + text[position + 1:]
            elif key == curses.KEY_LEFT:
                position = max(0, position - 1)
            elif key == curses.KEY_RIGHT:
                position = min(len(text), position + 1)
            elif key in (curses.KEY_HOME, '\x01'):
                position = 0
            elif key in (curses.KEY_END, '\x05'):
                position = len(text)
            elif key == '\x15':
                text, position = '', 0
            elif isinstance(key, str) and key.isprintable():
                text, position = text[:position] + key + text[position:], position + 1
    finally:
        ui.cursor(False)


def collect(ui, plan):
    # A fresh look each time (check again, after apply), shared by the steps within it.
    plan.distro.remember_answers()
    installer.found_firmware.cache_clear()
    reviews = []
    steps = installer.UNSTEPS if removing(plan) else installer.STEPS
    for index, step in enumerate(steps):
        row = ui.frame('Checking', 'Ctrl+C quits')
        if row is not None:
            row = ui.wrap(row, f'Checking what is left to do ({index + 1}/{len(steps)}): {step.title}') + 1
            for review in reviews[-(ui.size()[0] - row - 2):]:
                done = 'check failed' if review.error else f'{len(review.items)} to do' if review.items else 'nothing to do'
                ui.put(row, 4, f'{review.title:<10} {done}', ui.style('dim'))
                row += 1
            ui.window.refresh()
        reviews.append(review_step(plan, step))
    return reviews


def review(ui, plan):
    reviews = collect(ui, plan)
    warnings = review_warnings(plan, reviews)
    expanded = set()
    cursor, top = first_work(reviews), 0
    while True:
        row = ui.frame('Review', 'Up/Down move   Enter details   a apply   r check again   Esc back   q quit')
        if row is None:
            ui.key()
            continue
        height = ui.size()[0]
        work = [entry for entry in reviews if entry.items or entry.error]
        if removing(plan):
            ui.put(row, 2, 'Removing', ui.style('dim'))
            ui.put(row, 14, 'what the installer set up' + (f', as the {plan.distro.MANAGER} history tells' if plan.record.get('reconstructed') else ', from its record'))
        else:
            ui.put(row, 2, 'Profiles', ui.style('dim'))
            ui.put(row, 14, ', '.join(plan.profiles))
        row += 1
        if plan.firmware:
            ui.put(row, 2, 'Firmware', ui.style('dim'))
            ui.put(row, 14, plan.firmware)
            row += 1
        ui.put(row, 2, 'Same as', ui.style('dim'))
        ui.put(row, 14, command(plan))
        row += 2
        for warning in warnings:
            row = ui.wrap(row, '! ' + warning, ui.style('warn'))
        if not work:
            done = 'nothing of the desktop is left.' if removing(plan) else 'this system already matches the chosen profiles.'
            row = ui.wrap(row, 'Nothing to do: ' + done, ui.style('ok'))
        else:
            steps = '1 step has' if len(work) == 1 else f'{len(work)} steps have'
            row = ui.wrap(row, f'{steps} work. Each one checks again right before it runs, so the counts can change.', ui.style('dim'))
        row += 1
        rows = review_rows(reviews, expanded)
        cursor = min(cursor, len(rows) - 1)
        visible = max(height - 1 - row, 1)
        top = min(max(top, cursor - visible + 1), cursor)
        for offset, (_, text, style) in enumerate(rows[top:top + visible]):
            selected = top + offset == cursor
            ui.put(row + offset, 2, ('> ' if selected else '  ') + text, ui.style(style) | (curses.A_REVERSE if selected else 0))
        key = ui.key()
        if key in UP:
            cursor = max(cursor - 1, 0)
        elif key in DOWN:
            cursor = min(cursor + 1, len(rows) - 1)
        elif key == curses.KEY_PPAGE:
            cursor = max(cursor - visible, 0)
        elif key == curses.KEY_NPAGE:
            cursor = min(cursor + visible, len(rows) - 1)
        elif key in ENTER or key == ' ':
            step = rows[cursor][0]
            expanded ^= {step}
            # Folding leaves the cursor on the step line, not on a row that is gone.
            cursor = next(index for index, entry in enumerate(review_rows(reviews, expanded)) if entry[0] == step)
        elif key == 'r':
            reviews = collect(ui, plan)
            warnings = review_warnings(plan, reviews)
            expanded.clear()
            cursor, top = first_work(reviews), 0
        elif key == 'a' and work:
            verb = 'Remove the desktop in' if removing(plan) else 'Apply'
            ui.footer(f'{verb} {steps.split()[0]} {"step" if len(work) == 1 else "steps"} now? sudo asks for your password once. [y/N]', 'warn')
            if ui.key() in ('y', 'Y'):
                return 'apply'
        elif key in BACK:
            return 'back'
        elif key == 'q':
            return 'quit'


def notice(ui, title, text):
    while True:
        row = ui.frame(title, 'Enter back')
        if row is not None:
            ui.wrap(row, text)
        if ui.key() in ENTER + BACK:
            return


# Updates: what is newer than the installed desktop, from each source, to pick and apply. The repository goes
# alone and first: what it brings can move the pins, so the rest is checked again after it.
# selectable: there is something to apply. pins: what applying it writes into the manifest.
Source = namedtuple('Source', 'key title summary details note selectable pins error', defaults=(False, (), ''))
MANIFEST = REPO / 'scripts/install/manifest.toml'
HELPERS = REPO / 'shell/.local/libexec/desktop'
# The installer step that applies each source; Flatpak and the repository are done here.
STEP_OF = {'system': 'upgrade', 'aur': 'aur', 'clones': 'clones', 'archives': 'archives'}


def shell_helper(name):
    # A helper of the shell, from this repository. Its folder goes last on the path: it holds a calendar.py, which
    # must not hide the standard library's.
    if str(HELPERS) not in sys.path:
        sys.path.append(str(HELPERS))
    spec = importlib.util.spec_from_file_location('desktop_' + name, HELPERS / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def counted(number, word):
    return f'{number} {word}' + ('' if number == 1 else 's')


def failed_source(key, title, error):
    return Source(key, title, 'check failed', str(error).splitlines(), '', error=str(error))


def package_source(plan, updates):
    # The same listing as the update icon in the bar.
    listed, error = updates.system_updates()
    if error:
        return failed_source('system', 'System packages', error)
    note = f'Applied as the installer applies it: {plan.distro.MANAGER}, every update at once.'
    if any(package['name'] in updates.COMPOSITOR for package in listed):
        note += ' Hyprland is among them: log out and back in afterwards, and the plugins rebuild at that login.'
    summary = f'{counted(len(listed), "update")} ({plan.distro.MANAGER})' if listed else 'up to date'
    return Source('system', 'System packages', summary, [f'{package["name"]} {package["version"]}' for package in listed],
                  note, bool(listed))


def flatpak_source(updates):
    listed, error = updates.flatpak_listing()
    if error:
        return failed_source('flatpak', 'Flatpak apps', error)
    details = [f'{app["id"]} {app["version"]}'.strip() for app in listed]
    return Source('flatpak', 'Flatpak apps', counted(len(listed), 'update') if listed else 'up to date', details,
                  'flatpak update: the system apps with sudo, your own as you.', bool(listed))


PIN_NOTES = {
    'aur': 'Review the PKGBUILD changes first (Enter shows the links). The new commits go into '
           'scripts/install/manifest.toml, for you to commit, and makepkg builds them.',
    'clones': "Each clone follows its release tags (track = 'tags' in the manifest) or else the head of its branch. "
              'The new commits go into scripts/install/manifest.toml, for you to commit, and the clones step checks them out.',
    'archives': 'Release archives update themselves once installed (Herdr and hc): a new pin only changes what a new install '
                'unpacks. The new version and sha256 go into scripts/install/manifest.toml, for you to commit.',
}


def pin_source(plan, kind, title):
    # The pins of the installed profiles with a newer commit upstream; None when the profiles pin nothing of kind.
    items = installer.merged(plan, kind)
    if not items:
        return None
    pins, held, details, failed = [], [], [], []
    for item in items:
        try:
            pin = installer.newer_pin(kind, item)
        except OSError as error:
            pin, details = False, details + [f'{installer.pin_name(kind, item)}: {error}']
        if pin is False:
            failed.append(installer.pin_name(kind, item))
        elif pin and kind == 'clones' and not installer.clone_ours(installer.clone_path(item)):
            # The clones step leaves a changed clone alone: the pin would move without it.
            held.append(pin.name)
            details += [f'{pin.name} {pin.label}: ~/{item["path"]} has local changes, so it stays as it is '
                        f'(git -C ~/{item["path"]} status shows them).']
        elif pin:
            pins.append(pin)
            details += [f'{pin.name} {pin.label}', '  changes: ' + pin.url]
    error = f'{", ".join(failed)}: the remote did not answer.' if failed else ''
    summary = (', '.join(f'{pin.name} {pin.label}' for pin in pins) or (f'{", ".join(held)}: newer, but changed here' if held else '')
               or ('check failed' if failed else ('at their latest versions' if kind == 'archives' else 'at their latest commits')))
    return Source(kind, title, summary, details + ([error] if error else []), PIN_NOTES[kind], bool(pins), tuple(pins), error)


def git(*arguments):
    # Never a password or passphrase prompt over the screen: ssh fails instead, unless the user set their own command.
    environment = dict(os.environ, GIT_TERMINAL_PROMPT='0', LC_ALL='C')
    if 'GIT_SSH_COMMAND' not in environment and not installer.query('git', '-C', str(REPO), 'config', 'core.sshCommand').stdout.strip():
        environment['GIT_SSH_COMMAND'] = 'ssh -o BatchMode=yes'
    return subprocess.run(('git', '-C', str(REPO), *arguments), capture_output=True, text=True, env=environment, timeout=120)


def repository_source():
    # Only a fast-forward: a clean tree whose branch has nothing its upstream lacks.
    upstream = git('rev-parse', '--abbrev-ref', '--symbolic-full-name', '@{u}')
    if upstream.returncode:
        return Source('repository', 'Repository', 'no upstream branch to compare with', [], 'git branch --set-upstream-to sets one.')
    upstream = upstream.stdout.strip()
    fetched = git('fetch', '--quiet', upstream.split('/', 1)[0])
    if fetched.returncode:
        return failed_source('repository', 'Repository', 'git fetch failed: ' + (fetched.stderr or fetched.stdout).strip()[-300:])
    behind = int(git('rev-list', '--count', 'HEAD..@{u}').stdout.strip() or 0)
    ahead = int(git('rev-list', '--count', '@{u}..HEAD').stdout.strip() or 0)
    log = git('log', '--format=%h %s', 'HEAD..@{u}').stdout.splitlines()
    dirty = bool(git('status', '--porcelain', '--untracked-files=no').stdout.strip())
    note = f'git merge --ff-only {upstream}: it changes the running desktop at once, as editing the files does.'
    if not behind:
        summary = f'up to date with {upstream}' + (f', {ahead} commits ahead' if ahead else '')
        return Source('repository', 'Repository', summary, [], note)
    if ahead:
        return Source('repository', 'Repository', f'{behind} behind and {ahead} ahead of {upstream}: merge it by hand', log, note)
    if dirty:
        return Source('repository', 'Repository', f'{behind} commits behind {upstream}, with local changes: commit or stash them first',
                      log, note)
    return Source('repository', 'Repository', f'{behind} commits behind {upstream}', log, note, True)


def desktop_source(plan):
    # What the installed profiles still need from the manifest, after a pull for instance. The upgrade is the
    # System packages line.
    work = [review for review in (review_step(plan, step) for step in installer.STEPS if step.title != 'upgrade')
            if review.items or review.error]
    details = []
    for review in work:
        details.append(f'{review.title}: ' + (f'check failed: {review.error.splitlines()[0]}' if review.error else f'{len(review.items)} to do'))
        details += ['  ' + item for item in review.items[:5]] + (['  ...'] if len(review.items) > 5 else [])
    summary = f'{counted(len(work), "step")} to do' if work else 'matches the installed profiles'
    return Source('desktop', 'Desktop', summary, details, 'Install or update the desktop, in the menu, applies this, after its own review.')


def plugins_source():
    return Source('plugins', 'Hyprland plugins', PLUGIN_STATES[bundle.status()], [],
                  'Built for one Hyprland build, and replaced only at a login, before they load.')


def maintainer():
    # Who moves the pins: `git config desktop.maintainer true` in this repository. Everyone else gets the pins
    # with the repository, and the Desktop line applies them: pinning here would leave local changes that stop
    # the next pull.
    return git('config', '--bool', 'desktop.maintainer').stdout.strip() == 'true'


def check_updates(ui, plan):
    plan.distro.remember_answers()
    updates = shell_helper('updates')
    pins = (
        ('aur', 'AUR packages', lambda: pin_source(plan, 'aur', 'AUR packages')),
        ('clones', 'zsh plugins', lambda: pin_source(plan, 'clones', 'zsh plugins')),
        ('archives', 'Release archives', lambda: pin_source(plan, 'archives', 'Release archives')),
    ) if maintainer() else ()
    checks = (
        ('system', 'System packages', lambda: package_source(plan, updates)),
        ('flatpak', 'Flatpak apps', lambda: flatpak_source(updates)),
        *pins,
        ('repository', 'Repository', repository_source),
        ('desktop', 'Desktop', lambda: desktop_source(plan)),
        ('plugins', 'Hyprland plugins', plugins_source),
    )
    sources = []
    for index, (key, title, check) in enumerate(checks):
        row = ui.frame('Updates', 'Ctrl+C quits')
        if row is not None:
            ui.wrap(row, f'Looking for updates ({index + 1}/{len(checks)}): {title}')
            ui.window.refresh()
        try:
            source = check()
        except (subprocess.SubprocessError, RuntimeError, OSError, ValueError) as error:
            source = failed_source(key, title, error)
        if source:
            sources.append(source)
    return sources


def recorded_profiles():
    # The profiles the installer applied here, from its record; a missing package does not make one less of them.
    # Quiet: an unreadable record says so on stderr, over the screen.
    with redirect_stderr(io.StringIO()):
        record = installer.load_record()
    if record.get('uninstalled'):
        return ()
    return tuple(name for name in installer.PROFILES if name in record.get('profiles', ()) or name == 'core' and record.get('profiles'))


def default_choice(sources):
    # Everything there is to apply, but the repository, which goes alone.
    return {source.key for source in sources if source.selectable and source.key != 'repository'}


def update_rows(sources, chosen, expanded):
    rows = []
    for index, source in enumerate(sources):
        box = ('[x]' if source.key in chosen else '[ ]') if source.selectable else '   '
        style = 'accent' if source.selectable else 'error' if source.error else 'dim'
        mark = ('-' if index in expanded else '+') if source.details else ' '
        rows.append((index, f'{mark} {box} {source.title:<17} {source.summary}', style))
        if index in expanded:
            rows += [(index, '        ' + line, 'dim') for line in source.details]
    return rows


def picked_sources(sources, chosen):
    # What a confirmed apply does: the repository alone when it is checked, else every checked source.
    picked = [source for source in sources if source.selectable and source.key in chosen]
    repository = [source for source in picked if source.key == 'repository']
    return ('pull', repository) if repository else ('apply', picked)


def updates_screen(ui, plan):
    sources = check_updates(ui, plan)
    chosen, expanded = default_choice(sources), set()
    cursor, top = 0, 0
    while True:
        row = ui.frame('Updates', 'Up/Down move   Space toggle   Enter details   a apply   r check again   Esc back   q quit')
        if row is None:
            ui.key()
            continue
        height = ui.size()[0]
        row = ui.wrap(row, 'What is newer than this desktop. The checked lines are applied together; the repository goes '
                      'alone and first, and the rest is checked again after it.', ui.style('dim')) + 1
        rows = update_rows(sources, chosen, expanded)
        cursor = min(cursor, len(rows) - 1)
        source = sources[rows[cursor][0]]
        # Room for the note of the highlighted line at the bottom.
        visible = max(height - 1 - row - 4, 1)
        top = min(max(top, cursor - visible + 1), cursor)
        for offset, (_, text, style) in enumerate(rows[top:top + visible]):
            selected = top + offset == cursor
            ui.put(row + offset, 2, clip(('> ' if selected else '  ') + text, ui.size()[1] - 4),
                   ui.style(style) | (curses.A_REVERSE if selected else 0))
        ui.wrap(row + len(rows[top:top + visible]) + 1, source.note, ui.style('dim'))
        key = ui.key()
        if key in UP:
            cursor = max(cursor - 1, 0)
        elif key in DOWN:
            cursor = min(cursor + 1, len(rows) - 1)
        elif key == curses.KEY_PPAGE:
            cursor = max(cursor - visible, 0)
        elif key == curses.KEY_NPAGE:
            cursor = min(cursor + visible, len(rows) - 1)
        elif key in ENTER:
            index = rows[cursor][0]
            expanded ^= {index}
            cursor = next(position for position, entry in enumerate(update_rows(sources, chosen, expanded)) if entry[0] == index)
        elif key == ' ' and source.selectable:
            chosen ^= {source.key}
        elif key == 'r':
            sources = check_updates(ui, plan)
            chosen, expanded = default_choice(sources), set()
            cursor, top = 0, 0
        elif key == 'a':
            action, picked = picked_sources(sources, chosen)
            if not picked:
                ui.footer('Nothing is checked: Space checks a line.', 'warn')
                ui.key()
            elif action == 'pull':
                ui.footer('Update the repository now? The rest is checked again after it. [y/N]', 'warn')
                if ui.key() in ('y', 'Y'):
                    return action, picked
            else:
                ui.footer(f'Apply {len(picked)} now? sudo asks for your password once. [y/N]', 'warn')
                if ui.key() in ('y', 'Y'):
                    return action, picked
        elif key in BACK:
            return 'back', None
        elif key == 'q':
            return 'quit', None


def interface(window, plan, preset=False, start='menu'):
    # A state machine over the screens; what comes back is run after curses has given the terminal back.
    # preset: --profiles was given, and wins over what is found on the system. start: menu, or updates.
    ui = Screen(window)
    stage, mode, statuses = start, 'install', None
    while True:
        if stage == 'menu':
            mode = menu(ui)
            if mode == 'quit':
                return None
            stage = mode if mode in ('uninstall', 'updates') else 'profiles'
        elif stage == 'updates':
            # Of the profiles of this desktop, whatever --profiles says.
            stage = 'menu'
            if not installer.desktop_present():
                notice(ui, 'Updates', 'The desktop is not installed yet: Install or update the desktop comes first.')
                continue
            profiles = recorded_profiles()
            if not profiles:
                if statuses is None:
                    statuses = detect(ui, plan)
                profiles = tuple(name for name in installer.PROFILES if name == 'core' or installed(statuses[name]))
            current = plan._replace(profiles=profiles)
            outcome, picked = updates_screen(ui, current)
            if outcome == 'quit':
                return None
            if outcome in ('pull', 'apply'):
                return 'pull' if outcome == 'pull' else 'updates', current, picked
        elif stage == 'uninstall':
            # Back to the menu whatever the answer, unless the removal is confirmed.
            stage = 'menu'
            if installer.hyprland_running():
                notice(ui, 'Remove the desktop', 'Hyprland is running, and removing the desktop takes away the configuration '
                       'it runs on. Log out, switch to a console with Ctrl+Alt+F3, sign in there and start this again.')
                continue
            if ui.frame('Remove the desktop', 'Ctrl+C quits') is not None:
                ui.wrap(2, 'Reading what the installer set up...')
                ui.window.refresh()
            try:
                with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                    removal = installer.uninstall_plan(plan)
            except (subprocess.CalledProcessError, RuntimeError, OSError) as error:
                notice(ui, 'Remove the desktop', f'What the installer set up could not be read: {error}')
                continue
            outcome = review(ui, removal)
            if outcome == 'quit':
                return None
            if outcome == 'apply':
                return 'uninstall', removal
        elif stage == 'profiles':
            if statuses is None:
                statuses = detect(ui, plan)
                if not preset:
                    plan = plan._replace(profiles=preselected(statuses))
            outcome, profiles = choose_profiles(ui, plan, mode, statuses, preset)
            plan = plan._replace(profiles=profiles)
            if outcome == 'quit':
                return None
            if outcome == 'back':
                stage = 'menu'
            elif mode == 'post':
                return 'post', plan
            elif firmware_items(plan):
                stage = 'firmware'
            else:
                plan, stage = plan._replace(firmware=None), 'review'
        elif stage == 'firmware':
            outcome, firmware = choose_firmware(ui, plan, firmware_items(plan))
            plan = plan._replace(firmware=firmware)
            stage = 'review' if outcome == 'next' else 'profiles'
        elif stage == 'review':
            outcome = review(ui, plan)
            if outcome == 'quit':
                return None
            if outcome == 'apply':
                return 'apply', plan
            stage = 'firmware' if firmware_items(plan) else 'profiles'


def keep_sudo(stop):
    # A long dnf transaction outlasts the sudo timeout: refresh it so the run does not stop to ask again.
    while not stop.wait(SUDO_REFRESH):
        subprocess.run(('sudo', '-n', '-v'), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def confirm(question):
    try:
        return input(question).strip().lower() in ('y', 'yes')
    except EOFError:
        return False


def apply(plan):
    if removing(plan):
        installer.refuse_uninstall()
        installer.load_record(set_aside=True)  # An unreadable record is kept aside before uninstall marks it undone.
    print(f'Running: {command(plan)}', flush=True)
    subprocess.run(('sudo', '-v'), check=True)
    stop = threading.Event()
    threading.Thread(target=keep_sudo, args=(stop,), daemon=True).start()
    try:
        done = installer.run_steps(plan, False, installer.UNSTEPS if removing(plan) else installer.STEPS)
    finally:
        stop.set()
    if removing(plan):
        installer.after_uninstall(plan, done)
    else:
        installer.next_steps(plan, done)
    if done and installer.booted() and confirm('Reboot now? [y/N] '):
        subprocess.run(('sudo', 'systemctl', 'reboot'), check=True)
    return 0


def pull(plan):
    # Then this program starts again from the new version, on the updates screen: the pins may have moved.
    before = git('rev-parse', 'HEAD').stdout.strip()
    print('Running: git merge --ff-only @{u}', flush=True)
    subprocess.run(('git', '-C', str(REPO), 'merge', '--ff-only', '@{u}'), check=True)
    after_pull(plan, before)
    print('Checking again with the new version...', flush=True)
    os.execv(sys.executable, [sys.executable, str(REPO / 'scripts/install-tui.py'), '--updates'])


def after_pull(plan, before):
    # The running desktop follows its files at once, but a new file needs its link first: Hyprland would load a
    # module that requires it and fail until then, and Quickshell does not pick new files up on its own.
    changed = git('diff', '--name-only', before, 'HEAD').stdout.split()
    if not changed or not shutil.which('stow'):
        return
    print('Linking new files: ' + ' '.join(installer.stow_command(plan, 'apply')), flush=True)
    subprocess.run(installer.stow_command(plan, 'apply'), check=True)
    if not os.environ.get('HYPRLAND_INSTANCE_SIGNATURE'):
        return
    if any(path.startswith('hypr/') for path in changed):
        subprocess.run(('hyprctl', 'reload'), check=False, stdout=subprocess.DEVNULL)
    if any(path.startswith('quickshell/') for path in changed):
        # Through Hyprland, not from here: the shell's supervisor starts it with the session's environment.
        print('Restarting the shell...', flush=True)
        command = str(Path.home() / '.local/bin/desktop-shell') + ' restart'
        subprocess.run(('hyprctl', 'eval', f'hl.dispatch(hl.dsp.exec_cmd({json.dumps(command)}))'), check=False,
                       stdout=subprocess.DEVNULL)


def update_flatpaks():
    # The system's apps with sudo, as the installer installs them; your own as you.
    subprocess.run(('sudo', 'flatpak', 'update', '--system', '-y', '--noninteractive'), check=True)
    if installer.query('flatpak', 'list', '--user', '--app', '--columns=application').stdout.strip():
        subprocess.run(('flatpak', 'update', '--user', '-y', '--noninteractive'), check=True)


def refresh_bar():
    # The update icon shows what updates.py found last: check again, as the update terminal does.
    command = Path.home() / '.local/bin/desktop-updates'
    if command.exists():
        subprocess.run((str(command), 'check'), check=False)


def apply_updates(plan, picked):
    keys = {source.key for source in picked}
    print('Updating: ' + ', '.join(source.title for source in picked), flush=True)
    subprocess.run(('sudo', '-v'), check=True)
    stop = threading.Event()
    threading.Thread(target=keep_sudo, args=(stop,), daemon=True).start()
    pins = [pin for source in picked for pin in source.pins]
    try:
        if pins:
            text = MANIFEST.read_text(encoding='utf-8')
            for pin in pins:
                text = installer.apply_pin(text, pin)
            MANIFEST.write_text(text, encoding='utf-8')
            print(f'Pinned in {MANIFEST.relative_to(REPO)}: ' + ', '.join(f'{pin.name} {pin.label}' for pin in pins), flush=True)
            # Read again: the steps below build and check out what it pins now.
            plan = installer.load_plan(plan.profiles, firmware=plan.firmware)
        titles = {STEP_OF[key] for key in keys if key in STEP_OF}
        steps = tuple(step for step in installer.STEPS if step.title in titles)
        if steps:
            installer.run_steps(plan, False, steps)
        if 'flatpak' in keys:
            update_flatpaks()
    finally:
        stop.set()
    if keys & {'system', 'flatpak'}:
        refresh_bar()
    if pins:
        print(f'{MANIFEST.relative_to(REPO)} changed: commit it, so the other machines get the same pins.')
    state = bundle.status()
    if state not in (bundle.CURRENT, bundle.MISSING):
        print('Hyprland plugins: ' + PLUGIN_STATES[state] + '.')
    print('Done.')
    return 0


def set_locale():
    """The environment's locale, for curses to draw UTF-8. One the system lacks (LC_MESSAGES=en_US.UTF-8 with
    only Italian installed, say) makes setlocale fail: then the character set alone, else C.UTF-8."""
    for category, name in ((locale.LC_ALL, ''), (locale.LC_CTYPE, ''), (locale.LC_CTYPE, 'C.UTF-8')):
        try:
            locale.setlocale(category, name)
            return
        except locale.Error:
            continue


def main(argv=None):
    parser = ArgumentParser(description=__doc__)
    parser.add_argument('--firmware', metavar='DIR', help='directory the firmware screen starts with')
    parser.add_argument('--profiles', help='profiles chosen at the start (default: the ones installed, or on a fresh system '
                        f'{installer.DEFAULT_PROFILES}, and tablet on a 2-in-1)')
    parser.add_argument('--updates', action='store_true', help='start on the updates screen')
    args = parser.parse_args(argv)
    profiles = tuple((args.profiles or installer.default_profiles()).split(','))
    if not installer.valid_profiles(profiles):
        parser.error(f'--profiles needs core, and takes only {", ".join(installer.PROFILES)}.')
    if os.geteuid() == 0:
        sys.exit('Run as the desktop user: the installer asks sudo for each system change.')
    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        sys.exit('Run it in a terminal; without one, use install-desktop.py.')
    plan = installer.load_plan(profiles, firmware=args.firmware)
    installer.refuse(plan)
    set_locale()
    os.environ.setdefault('ESCDELAY', '25')
    try:
        choice = curses.wrapper(interface, plan, bool(args.profiles), 'updates' if args.updates else 'menu')
    except curses.error as error:
        sys.exit(f'This terminal cannot draw the installer ({error}): use install-desktop.py.')
    if choice is None:
        print('Nothing changed.')
        return 0
    action, plan, *picked = choice
    if action == 'post':
        installer.post(plan)
        return 0
    if action == 'pull':
        return pull(plan)
    if action == 'updates':
        return apply_updates(plan, picked[0])
    return apply(plan)


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit('\nInterrupted. Run it again: each step picks up where it stopped.')
    except (subprocess.CalledProcessError, RuntimeError, OSError) as error:
        sys.exit(f'{error}\nRun it again once fixed: each step picks up where it stopped.')
