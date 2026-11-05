#!/usr/bin/env python3
"""Guided install-desktop.py: pick the profiles and the firmware, review what is left to do, then apply it."""
from argparse import ArgumentParser
from collections import namedtuple
from contextlib import redirect_stdout
import curses
import getpass
import importlib.util
import io
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

# One line each; docs/guide/installation.md has the long version.
DESCRIPTIONS = {
    'core': 'Hyprland, Quickshell, GDM with the hyprland-uwsm session, portals, audio, network, fonts and zsh: the desktop itself.',
    'hardware': 'Firmware, video decoding and sensors of an Intel 2-in-1, fingerprint and tablet sign-in, firewall zone, sshd off.',
    'plugins': 'What building the Hyprland plugins needs, from RPM Fusion too; the RPM Fusion ffmpeg replaces ffmpeg-free.',
    'apps': 'Zen Browser, 1Password, VS Code, Neovim, gh, glab, uv, gcc and a few command-line tools.',
    'containers': 'Docker (moby-engine, docker-compose, the docker group) and Tailscale.',
    'media': 'Loupe, Papers and Showtime for images, PDFs and videos.',
    'gaming': 'Steam, gamescope and the 32-bit drivers games need.',
    'steam-hidpi': 'The Steam launcher that scales the client for the monitor it opens on.',
    'codecs': 'The RPM Fusion codecs in place of the free builds: ffmpeg, intel-media-driver, GStreamer freeworld, OpenH264, HEIF, aptX.',
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
    if profile.get('swaps'):
        parts.append('replaces ' + ', '.join(f'{old} with {new}' for old, new in profile['swaps']))
    return '; '.join(parts) + '.' if parts else ''


def command(plan, action='apply'):
    words = ['./scripts/install-desktop.py', action, '--profiles', ','.join(plan.profiles)]
    if plan.firmware:
        words += ['--firmware', shlex.quote(plan.firmware)]
    return ' '.join(words)


def firmware_items(plan):
    # The vendor blobs this model still needs; none unless hardware is chosen and the model matches.
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
    )


def menu(ui):
    entries = [('install', 'Install or update the desktop', 'Choose the profiles, review what is left to do, then apply it.')]
    if os.environ.get('HYPRLAND_INSTANCE_SIGNATURE'):
        entries.append(('post', 'Finish the installation', 'Build the Hyprland plugins and list what is left to do by hand.'))
    entries.append(('quit', 'Quit', 'Leave without changing anything.'))
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


def choose_profiles(ui, plan, mode):
    profiles = tuple(plan.profiles)
    cursor = 0
    if mode == 'post':
        title, intro = 'Profiles', 'Choose the profiles you installed: plugins builds the Hyprland plugins.'
    else:
        title, intro = 'Profiles', 'Choose what to install. core is the desktop itself and always stays on.'
    defaults = tuple(installer.DEFAULT_PROFILES.split(','))
    while True:
        row = ui.frame(title, 'Up/Down move   Space toggle   d defaults   Enter continue   Esc back   q quit')
        if row is None:
            ui.key()
            continue
        row = ui.wrap(row, intro) + 1
        for index, name in enumerate(installer.PROFILES):
            selected = index == cursor
            box = '[*]' if name == 'core' else '[x]' if name in profiles else '[ ]'
            ui.put(row, 2, ('> ' if selected else '  ') + f'{box} {name}', curses.A_REVERSE if selected else 0)
            ui.put(row, 22, clip(DESCRIPTIONS[name], ui.size()[1] - 24), ui.style('dim'))
            row += 1
        name = installer.PROFILES[cursor]
        row += 1
        ui.put(row, 2, name + ('  (default)' if name in defaults else '  (opt-in)'), ui.style('accent') | curses.A_BOLD)
        row = ui.wrap(row + 1, DESCRIPTIONS[name])
        ui.wrap(row, summary(plan.table, name), ui.style('dim'))
        key = ui.key()
        if key in UP:
            cursor = (cursor - 1) % len(installer.PROFILES)
        elif key in DOWN:
            cursor = (cursor + 1) % len(installer.PROFILES)
        elif key == ' ':
            profiles = toggled(profiles, name)
        elif key == 'd':
            profiles = defaults
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
    reviews = []
    for index, step in enumerate(installer.STEPS):
        row = ui.frame('Checking', 'Ctrl+C quits')
        if row is not None:
            row = ui.wrap(row, f'Checking what is left to do ({index + 1}/{len(installer.STEPS)}): {step.title}') + 1
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
            row = ui.wrap(row, 'Nothing to do: this system already matches the chosen profiles.', ui.style('ok'))
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
            ui.footer(f'Apply {steps.split()[0]} {"step" if len(work) == 1 else "steps"} now? sudo asks for your password once. [y/N]', 'warn')
            if ui.key() in ('y', 'Y'):
                return 'apply'
        elif key in BACK:
            return 'back'
        elif key == 'q':
            return 'quit'


def interface(window, plan):
    # A state machine over the screens; what comes back is run after curses has given the terminal back.
    ui = Screen(window)
    stage, mode = 'menu', 'install'
    while True:
        if stage == 'menu':
            mode = menu(ui)
            if mode == 'quit':
                return None
            stage = 'profiles'
        elif stage == 'profiles':
            outcome, profiles = choose_profiles(ui, plan, mode)
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
    print(f'Running: {command(plan)}', flush=True)
    subprocess.run(('sudo', '-v'), check=True)
    stop = threading.Event()
    threading.Thread(target=keep_sudo, args=(stop,), daemon=True).start()
    try:
        done = installer.run_steps(plan, False)
    finally:
        stop.set()
    installer.next_steps(plan, done)
    if done and installer.booted() and confirm('Reboot now? [y/N] '):
        subprocess.run(('sudo', 'systemctl', 'reboot'), check=True)
    return 0


def main(argv=None):
    parser = ArgumentParser(description=__doc__)
    parser.add_argument('--firmware', metavar='DIR', help='directory the firmware screen starts with')
    parser.add_argument('--profiles', default=installer.DEFAULT_PROFILES, help=f'profiles chosen at the start (default: {installer.DEFAULT_PROFILES})')
    args = parser.parse_args(argv)
    profiles = tuple(args.profiles.split(','))
    if not installer.valid_profiles(profiles):
        parser.error(f'--profiles needs core, and takes only {", ".join(installer.PROFILES)}.')
    if os.geteuid() == 0:
        sys.exit('Run as the desktop user: the installer asks sudo for each system change.')
    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        sys.exit('Run it in a terminal; without one, use install-desktop.py.')
    plan = installer.load_plan(profiles, firmware=args.firmware)
    installer.refuse(plan)
    locale.setlocale(locale.LC_ALL, '')
    os.environ.setdefault('ESCDELAY', '25')
    try:
        choice = curses.wrapper(interface, plan)
    except curses.error as error:
        sys.exit(f'This terminal cannot draw the installer ({error}): use install-desktop.py.')
    if choice is None:
        print('Nothing changed.')
        return 0
    action, plan = choice
    if action == 'post':
        installer.post(plan)
        return 0
    return apply(plan)


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit('\nInterrupted. Run it again: each step picks up where it stopped.')
    except (subprocess.CalledProcessError, RuntimeError, OSError) as error:
        sys.exit(f'{error}\nRun it again once fixed: each step picks up where it stopped.')
