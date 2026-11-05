"""Arch Linux operations of install-desktop.py: the functions of fedora.py, with pacman, plus the AUR builds."""
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

ADMIN_GROUP = 'wheel'
# The documented prerequisites of the installer itself: never removed.
PROTECTED = ('python', 'git')
# The package manager, as the guided installer names it.
MANAGER = 'pacman'
# systemd's own default, which a base system keeps: without a display manager it still starts on the console.
BASE_TARGET = 'graphical.target'
CONF = Path('/etc/pacman.conf')
LOG = Path('/var/log/pacman.log')
# Tablet sign-in edits PAM, which Arch configures without authselect: not ported yet, so no table asks for it.
AUTH_PROFILE = None
# How install() runs pacman: the log names the desktop's own installs by it (see base_packages).
INSTALL = ('pacman', '-Syu', '--needed', '--noconfirm', '--')
# pacman's question numbers (alpm.h): 4 is "remove the package this one conflicts with?".
ASK_CONFLICT = '--ask=4'


# pacman answers kept while nothing changes, when the installer turns it on, as in fedora.py. Any change through
# sudo() or makepkg forgets them.
answers = None


def remember_answers():
    global answers
    answers = {}


def forget_answers():
    if answers is not None:
        answers.clear()


def query(*command):
    if answers is None or command[0] not in ('pacman', 'pacman-conf', 'checkupdates'):
        return run_query(command)
    if command not in answers:
        answers[command] = run_query(command)
    return answers[command]


def run_query(command):
    return subprocess.run(command, capture_output=True, text=True, env={**os.environ, 'LC_ALL': 'C'})


def sudo(*command):
    forget_answers()
    try:
        subprocess.run(('sudo', *command), check=True)
    finally:
        forget_answers()


def bare(names):
    # NAME.ARCH, the form the installer keeps, back to the name pacman takes. Names may hold dots (webkitgtk-6.0).
    return [name.rsplit('.', 1)[0] for name in names]


def records(text):
    # pacman -Si / -Qi: one block per package of "Key : value" lines; a long value goes on in indented lines.
    blocks, block, key = [], {}, None
    for line in text.splitlines():
        if not line.strip():
            if block:
                blocks.append(block)
            block, key = {}, None
        elif line[0].isspace() and key:
            block[key] += ' ' + line.strip()
        else:
            key, _, value = line.partition(':')
            key = key.strip()
            block[key] = value.strip()
    if block:
        blocks.append(block)
    return blocks


def words(value):
    return [] if value in ('', 'None') else value.split()


def dependency_name(dependency):
    # libgtk-3.so=0-64, python>=3.12: the name, without the version a package depends on or provides.
    return re.split(r'[<>=]', dependency, maxsplit=1)[0]


def local_packages():
    # Every installed package by name: {name: {'arch', 'explicit', 'depends', 'provides'}}, from one pacman -Qi.
    packages = {}
    for block in records(query('pacman', '-Qi').stdout):
        if 'Name' in block:
            packages[block['Name']] = {
                'arch': block.get('Architecture', 'any'),
                'explicit': block.get('Install Reason', '').startswith('Explicitly'),
                'depends': [dependency_name(item) for item in words(block.get('Depends On', ''))],
                'provides': [dependency_name(item) for item in words(block.get('Provides', ''))],
            }
    return packages


def provider_index(packages):
    # {what is provided: the packages that provide it}, so a lookup does not walk every package.
    index = {}
    for package, info in packages.items():
        for provided in info['provides']:
            index.setdefault(provided, []).append(package)
    return index


def providers(packages, name, index=None):
    # The installed packages that satisfy a dependency on name: the package of that name, else what provides it.
    if name in packages:
        return [name]
    return (provider_index(packages) if index is None else index).get(name, [])


def full_name(packages, name):
    return f'{name}.{packages[name]["arch"]}'


def missing(packages):
    # pacman -T prints each dependency the system does not satisfy, by name or by what a package provides.
    return query('pacman', '-T', '--', *packages).stdout.split() if packages else []


def candidates(packages):
    # The build pacman would install now of each package, from the synced databases: {name: VERSION-REL}. A name
    # in two repositories comes from the first, as pacman picks it.
    builds = {}
    for block in records(query('pacman', '-Si', '--', *packages).stdout) if packages else ():
        if 'Name' in block and 'Version' in block:
            builds.setdefault(block['Name'], block['Version'])
    return builds


def version(package):
    # By name: pacman -Q also answers for what a package provides (pacman -Q sh prints bash).
    fields = query('pacman', '-Q', '--', package).stdout.split()
    return fields[1] if len(fields) == 2 and fields[0] == package else ''


def installed(package):
    return bool(version(package))


def install(packages, exclude=()):
    # -Syu, never -S alone: installing from databases newer than the system is a partial upgrade, which Arch does
    # not support. exclude is for weak dependencies, which pacman never installs: the Arch tables have none.
    sudo(*INSTALL, *packages)


def swap(old, new):
    # The replacement conflicts with what it replaces: pacman asks to remove it, and --noconfirm would say no.
    sudo('pacman', '-Syu', '--needed', '--noconfirm', ASK_CONFLICT, '--', new)


def upgrades_pending():
    # checkupdates syncs a copy of the databases, so this asks the mirrors without root. Before pacman-contrib and
    # fakeroot, which it needs, are installed nothing can tell without syncing: the upgrade counts as pending.
    if not shutil.which('checkupdates') or not shutil.which('fakeroot'):
        return True
    result = query('checkupdates', '--nocolor')
    if result.returncode not in (0, 2):
        raise RuntimeError('checkupdates failed: ' + (result.stderr or result.stdout).strip()[:300])
    return result.returncode == 0


def upgrade():
    sudo('pacman', '-Syu', '--noconfirm')


# Repositories: sections of pacman.conf. The default file lists multilib commented out, and enabling it means
# uncommenting that section, which disabling comments out again. A file without it gets one at the end, under a
# mark that tells disabling to take both away. Line ends stay as they are, so the file comes back byte for byte.
MARK = '# Added by the desktop installer (scripts/install-desktop.py): its uninstall removes it.'


def section_span(lines, name, commented):
    # Where the section is: its header and the settings under it, up to a blank line or the next header.
    prefix = '#' if commented else ''
    for start, line in enumerate(lines):
        if line.strip() == f'{prefix}[{name}]':
            end = start + 1
            while end < len(lines) and lines[end].strip() and not lines[end].lstrip('#').lstrip().startswith('['):
                end += 1
            return start, end
    return None


def with_section(text, name, include):
    lines = text.splitlines(keepends=True)
    if section_span(lines, name, commented=False):
        return text
    span = section_span(lines, name, commented=True)
    if span:
        start, end = span
        lines[start:end] = [line[1:] if line.startswith('#') else line for line in lines[start:end]]
        return ''.join(lines)
    return text + ('' if text.endswith('\n') else '\n') + f'\n{MARK}\n[{name}]\nInclude = {include}\n'


def without_section(text, name):
    lines = text.splitlines(keepends=True)
    span = section_span(lines, name, commented=False)
    if not span:
        return text
    start, end = span
    if start and lines[start - 1].strip() == MARK:
        start -= 1
        if start and not lines[start - 1].strip():
            start -= 1
        del lines[start:end]
    else:
        lines[start:end] = ['#' + line for line in lines[start:end]]
    return ''.join(lines)


def repo_missing(repo):
    return repo['name'] not in query('pacman-conf', '--repo-list').stdout.split()


def add_repo(repo, release):
    # The databases come with the next -Syu: the upgrade step, else the install.
    write_file(CONF, with_section(CONF.read_text(encoding='utf-8'), repo['name'], repo['include']))


def file_differs(path, content):
    try:
        return Path(path).read_text(encoding='utf-8') != content
    except OSError:
        return True


def write_file(path, content):
    with tempfile.NamedTemporaryFile('w', encoding='utf-8', prefix='desktop-install-') as temporary:
        temporary.write(content)
        temporary.flush()
        sudo('install', '-D', '-o', 'root', '-g', 'root', '-m', '0644', temporary.name, str(path))


def install_firmware(source, target):
    sudo('install', '-D', '-o', 'root', '-g', 'root', '-m', '0644', str(source), str(target))


def rebuild_initramfs():
    # mkinitcpio is Arch's default; an install may have chosen dracut instead.
    if shutil.which('mkinitcpio'):
        sudo('mkinitcpio', '-P')
    elif shutil.which('dracut'):
        sudo('dracut', '--force', '--regenerate-all')
    else:
        raise RuntimeError('Neither mkinitcpio nor dracut is installed: the initramfs cannot be rebuilt.')


def auth_base():
    return ''


def auth_pending():
    return []


def auth_apply(pending, tablet_auth):
    raise RuntimeError('Tablet sign-in is not ported to Arch yet: it needs PAM edited without authselect.')


# The AUR: a PKGBUILD checked out at its pinned commit, built and installed by makepkg as the desktop user.

def build_package(directory):
    # --syncdeps and --install ask sudo for pacman; --rmdeps removes what only the build needed.
    forget_answers()
    try:
        subprocess.run(('makepkg', '--syncdeps', '--install', '--rmdeps', '--cleanbuild', '--clean', '--needed', '--noconfirm'),
                       cwd=directory, check=True)
    finally:
        forget_answers()


# Uninstall: the reverse of the operations above.

def installed_names(specs):
    # NAME.ARCH of each installed spec: a package name, or something an installed package provides.
    packages, names = local_packages(), []
    index = provider_index(packages)
    for spec in specs:
        for name in providers(packages, dependency_name(spec), index):
            if full_name(packages, name) not in names:
                names.append(full_name(packages, name))
    return names


def printed(result):
    return [line for line in result.stdout.splitlines() if line and ' ' not in line]


def cascade(names):
    # What pacman removes with names: what depends on them (-c, as dnf does) and the dependencies nothing else
    # needs (-s). No root needed, nothing changes.
    result = query('pacman', '-Rsc', '--print', '--print-format', '%n.%a', '--', *bare(names))
    if result.returncode:
        raise RuntimeError('pacman -Rsc --print failed: ' + (result.stderr or result.stdout).strip()[-300:])
    return printed(result)


BREAKS = re.compile(r'removing (\S+) breaks dependency')


def brought():
    # The packages the desktop's installs brought, from the first install of this installer on: makepkg's too.
    transactions = history()
    installer = ' '.join(INSTALL)
    first = next((t['id'] for t in transactions if t['command_line'].startswith(installer)), None)
    return {package['name'] for t in transactions if first is not None and t['id'] >= first
            for package in t['packages'] if package['action'] == 'installed'}


def left_behind(rows):
    # What -s keeps although nothing needs it. It keeps a dependency that anything could need through what it
    # provides: lib32-systemd provides libudev.so=1-32, and device-mapper depends on a bare libudev.so, which
    # systemd-libs gives it. The dependencies of what goes that the desktop's installs brought go too, once pacman,
    # asked about exactly these, finds that nothing staying depends on them; the ones it would break stay.
    packages, going = local_packages(), set(bare(rows))
    index = provider_index(packages)
    reached, todo = set(), [name for name in going if name in packages]
    while todo:
        for dependency in packages[todo.pop()]['depends']:
            for provider in providers(packages, dependency, index):
                if provider not in reached and provider not in going:
                    reached.add(provider)
                    todo.append(provider)
    origin = brought()
    extra = sorted(name for name in reached if name in origin and not packages[name]['explicit'])
    while extra:
        result = query('pacman', '-Rs', '--print', '--print-format', '%n.%a', '--', *sorted(going), *extra)
        if result.returncode == 0:
            return [row for row in printed(result) if bare([row])[0] not in going]
        broken = set(BREAKS.findall(result.stderr + result.stdout)) & set(extra)
        if not broken:
            raise RuntimeError('pacman -Rs --print failed: ' + (result.stderr or result.stdout).strip()[-300:])
        extra = [name for name in extra if name not in broken]
    return []


def removal(names):
    # Every package uninstall removes: pacman's answer, and what it leaves behind that nothing needs.
    if not names:
        return []
    rows = cascade(names)
    return rows + left_behind(rows)


def remove(names):
    if not names:
        return
    extra = left_behind(cascade(names))
    sudo('pacman', '-Rsc', '--noconfirm', '--', *bare(names))
    if extra:
        sudo('pacman', '-Rs', '--noconfirm', '--', *bare(extra))


def installed_by_hand(names):
    # Of these installed packages, the ones installed explicitly rather than as a dependency.
    packages = local_packages()
    return {name for name in names if packages.get(bare([name])[0], {}).get('explicit')}


def requirements(names):
    # Every installed package these need, directly or through others, as NAME.ARCH.
    packages = local_packages()
    index = provider_index(packages)
    seen, todo = set(), [name for name in bare(names) if name in packages]
    while todo:
        for dependency in packages[todo.pop()]['depends']:
            for provider in providers(packages, dependency, index):
                if provider not in seen:
                    seen.add(provider)
                    todo.append(provider)
    return {full_name(packages, name) for name in seen}


def packages_from(repo):
    # The installed packages that came from this repository, as NAME.ARCH: pacman -Sl marks them [installed], or
    # [installed: VERSION] when the one installed differs.
    lines = query('pacman', '-Sl', repo['name']).stdout.splitlines()
    packages = local_packages()
    names = [fields[1] for fields in map(str.split, lines) if len(fields) >= 4 and fields[3].startswith('[installed')]
    return {full_name(packages, name) for name in names if name in packages}


def remove_repo(repo):
    write_file(CONF, without_section(CONF.read_text(encoding='utf-8'), repo['name']))


def auth_revert(items, tablet_auth):
    raise RuntimeError('Tablet sign-in is not ported to Arch yet: there is nothing of it to undo.')


HISTORY_LINE = re.compile(r"^\[[^\]]+\] \[PACMAN\] Running '(.*)'$")
ACTION_LINE = re.compile(r'^\[[^\]]+\] \[ALPM\] (installed|reinstalled|upgraded|downgraded|removed) (\S+) \(')


def history():
    # The transactions of pacman's log, oldest first: the command that ran and what it changed.
    try:
        lines = LOG.read_text(encoding='utf-8', errors='replace').splitlines()
    except FileNotFoundError:
        return []
    except OSError as error:
        raise RuntimeError(f'{LOG} cannot be read: {error}') from error
    transactions = []
    for line in lines:
        match = HISTORY_LINE.match(line)
        if match:
            transactions.append({'id': len(transactions) + 1, 'command_line': match[1], 'packages': []})
            continue
        match = ACTION_LINE.match(line)
        if match:
            # Changes logged before any command, as in the container image, are a transaction of their own.
            if not transactions:
                transactions.append({'id': 1, 'command_line': '', 'packages': []})
            transactions[-1]['packages'].append({'name': match[2], 'action': match[1]})
    return transactions


def base_packages(transactions):
    # The system before the desktop: what was installed before the first install of this installer, which the log
    # names by its command line. pacstrap, archinstall and whatever the user added before all count, so nothing
    # they brought is taken for the desktop's. Without such an install, nobody can tell: an empty set.
    installer = ' '.join(INSTALL)
    first = next((t['id'] for t in transactions if t['command_line'].startswith(installer)), None)
    if first is None:
        return set()
    names = set()
    for transaction in transactions:
        if transaction['id'] >= first:
            break
        for package in transaction['packages']:
            if package['action'] == 'removed':
                names.discard(package['name'])
            else:
                names.add(package['name'])
    packages = local_packages()
    return {full_name(packages, name) for name in names if name in packages}


def default_zone():
    # Arch enables no firewall; firewalld's own default.
    return 'public'


def owned(path):
    return query('pacman', '-Qo', '--', str(path)).returncode == 0


def auth_reconstruct(packages):
    return []
