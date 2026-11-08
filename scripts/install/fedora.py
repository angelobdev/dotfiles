"""Fedora operations of install-desktop.py; another distribution is a module with these same names."""
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

ADMIN_GROUP = 'wheel'
# The documented prerequisites of the installer itself: never removed.
PROTECTED = ('python3', 'git-core')
# The package manager, as the guided installer names it.
MANAGER = 'dnf'
# The boot target of an edition without a desktop (Server): what uninstall restores when it has no record.
BASE_TARGET = 'multi-user.target'
REPOS = Path('/etc/yum.repos.d')
AUTH_FEATURE = 'with-fingerprint'
AUTH_PROFILE = 'custom/desktop-tablet'


# rpm and dnf answers kept while nothing changes, when the installer turns it on: planning an uninstall asks dnf
# the same questions from several steps, each a solver run of seconds. Any change through sudo() forgets them.
answers = None


def remember_answers():
    global answers
    answers = {}


def forget_answers():
    if answers is not None:
        answers.clear()


def query(*command):
    if answers is None or command[0] not in ('dnf', 'rpm'):
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


def missing(packages):
    # --whatprovides also takes capabilities, such as mesa-vulkan-drivers(x86-32).
    prefix = 'no package provides '
    lines = query('rpm', '-q', '--whatprovides', *packages).stdout.splitlines()
    return [line.removeprefix(prefix) for line in lines if line.startswith(prefix)]


def candidates(packages):
    # The build dnf would install now of each package, from the enabled repositories: {name: VERSION-RELEASE.ARCH}.
    lines = query('dnf', 'repoquery', '--latest-limit', '1', '--qf', '%{name} %{version}-%{release}.%{arch}\n', *packages).stdout.splitlines()
    return {name: build for name, _, build in (line.partition(' ') for line in lines) if build and not build.endswith('.src')}


def installed(package):
    # By name, not --whatprovides: a replacement often provides the name of what it replaces.
    return query('rpm', '-q', package).returncode == 0


def install(packages, exclude=()):
    sudo('dnf', 'install', '-y', *(['--exclude=' + ','.join(exclude)] if exclude else []), *packages)


def swap(old, new):
    # --allowerasing: the replacement conflicts with what it replaces and with the packages built against it.
    sudo('dnf', 'swap', '-y', '--allowerasing', old, new)


def upgrades_pending():
    result = query('dnf', 'check-upgrade', '--quiet')
    if result.returncode not in (0, 100):
        raise RuntimeError('dnf check-upgrade failed: ' + result.stderr.strip()[:300])
    return result.returncode == 100


def upgrade():
    sudo('dnf', 'upgrade', '--refresh', '-y')


def repo_file(repo):
    if repo['kind'] == 'copr':
        owner, name = repo['name'].split('/')
        return REPOS / f'_copr:copr.fedorainfracloud.org:{owner}:{name}.repo'
    return REPOS / repo['file']


def repo_missing(repo):
    if repo['kind'] == 'release':
        return bool(missing([repo['package']]))
    return not repo_file(repo).exists()


def add_repo(repo, release):
    if repo['kind'] == 'copr':
        if missing(['dnf5-plugins']):
            install(['dnf5-plugins'])
        sudo('dnf', 'copr', 'enable', '-y', repo['name'])
    elif repo['kind'] == 'release':
        install([repo['url'].format(release=release)])
    else:
        write_file(repo_file(repo), repo['content'].lstrip())


def file_differs(path, content):
    try:
        return Path(path).read_text(encoding='utf-8') != content
    except OSError:
        return True


def write_file(path, content, mode='0644'):
    with tempfile.NamedTemporaryFile('w', encoding='utf-8', prefix='desktop-install-') as temporary:
        temporary.write(content)
        temporary.flush()
        sudo('install', '-D', '-o', 'root', '-g', 'root', '-m', mode, temporary.name, str(path))


def install_firmware(source, target):
    sudo('install', '-D', '-o', 'root', '-g', 'root', '-m', '0644', str(source), str(target))
    sudo('restorecon', str(target))


def rebuild_initramfs():
    sudo('dracut', '--force', '--regenerate-all')


def auth_base():
    fields = query('authselect', 'current', '--raw').stdout.split()
    return fields[0] if fields else ''


def auth_pending():
    fields = query('authselect', 'current', '--raw').stdout.split()
    pending = [] if AUTH_FEATURE in fields[1:] else [AUTH_FEATURE]
    return pending + ([] if fields[:1] == [AUTH_PROFILE] else [AUTH_PROFILE])


def auth_apply(pending, tablet_auth):
    if AUTH_FEATURE in pending:
        sudo('authselect', 'enable-feature', AUTH_FEATURE)
    if AUTH_PROFILE in pending:
        # As the desktop user: the script asks sudo for each change.
        subprocess.run((str(tablet_auth), 'install'), check=True)


# Uninstall: the reverse of the operations above.

def installed_names(specs):
    # NAME.ARCH of each installed spec: a name, a NAME.ARCH, or a capability such as mesa-dri-drivers(x86-32), which
    # names its i686 package. rpm takes capabilities only with --whatprovides, and NAME.ARCH only without.
    capabilities = [spec for spec in specs if '(' in spec]
    plain = [spec for spec in specs if '(' not in spec]
    lines = []
    for options, group in ((('--whatprovides',), capabilities), ((), plain)):
        if group:
            lines += query('rpm', '-q', *options, '--qf', '%{NAME}.%{ARCH}\n', *group).stdout.splitlines()
    names = []
    for line in lines:
        if line and ' ' not in line and line not in names:
            names.append(line)
    return names


REQUIRED = re.compile(r'requires (\S+)(?: [<>=]+ \S+)?, but none of the providers can be installed')


def providers(capabilities):
    # A file such as /usr/bin/pkg-config, or a name such as kmod: whatever installed package provides it.
    lines = query('rpm', '-q', '--whatprovides', '--qf', '%{NAME}.%{ARCH}\n', *capabilities).stdout.splitlines() if capabilities else []
    return [line for line in lines if line and ' ' not in line]


def dnf_removal(names):
    # The rows of dnf's answer, or None with its complaint when it refuses the whole removal.
    result = query('dnf', 'remove', '--assumeno', *names)
    rows, inside = [], False
    for line in result.stdout.splitlines():
        if line.startswith('Removing'):
            inside = True
        elif not line.startswith(' '):
            inside = False
        elif inside:
            fields = line.split()
            if len(fields) >= 3:
                rows.append(f'{fields[0]}.{fields[1]}')
    if rows or 'Nothing to do' in result.stdout + result.stderr:
        return rows, ''
    return None, (result.stderr or result.stdout).strip()


def removable(names):
    # What can go of names, and everything dnf removes with them. A package that stays may still need one of them,
    # as kmod, a dependency of the protected systemd-udev, needs /usr/bin/pkg-config: dnf then refuses everything.
    # Whatever provides what it needs stays too, and dnf is asked again. No root needed, nothing changes.
    names = list(names)
    while names:
        rows, complaint = dnf_removal(names)
        if rows is not None:
            return names, rows
        needed = set(providers(sorted(set(REQUIRED.findall(complaint)))))
        if not needed & set(names):
            raise RuntimeError('dnf remove --assumeno failed: ' + complaint[-300:])
        names = [name for name in names if name not in needed]
    return [], []


def removal(names):
    # Every package dnf would remove, dependent packages and unused dependencies included.
    return removable(names)[1]


def installed_by_hand(names):
    # Of these installed packages, the ones a person asked for rather than dnf for a dependency.
    # Anything dnf did not pull in counts: User, Group, External User (rpm -i) and None (reason unknown), so a
    # package uninstall cannot account for is kept rather than removed.
    lines = query('dnf', 'repoquery', '--installed', '--qf', '%{name}.%{arch} %{reason}\n', *names).stdout.splitlines() if names else []
    pulled = ('Dependency', 'Weak Dependency', 'Clean')
    return {name for name, _, reason in (line.partition(' ') for line in lines) if name and reason.strip() and reason.strip() not in pulled}


def requirements(names):
    # Every installed package these need, directly or through others, as NAME.ARCH.
    lines = query('dnf', 'repoquery', '--installed', '--providers-of=requires', '--recursive', '--qf', '%{name}.%{arch}\n',
                  *names).stdout.splitlines() if names else []
    return {line for line in lines if line and ' ' not in line}


def repo_ids(repo):
    # The repository ids a manifest entry adds: the sections of the .repo files it installs.
    if repo['kind'] == 'copr':
        return ['copr:copr.fedorainfracloud.org:' + repo['name'].replace('/', ':')]
    files = query('rpm', '-ql', repo['package']).stdout.split() if repo['kind'] == 'release' else [str(repo_file(repo))]
    ids = []
    for path in (path for path in files if path.endswith('.repo')):
        try:
            ids += re.findall(r'^\[([^\]]+)\]', Path(path).read_text(encoding='utf-8'), re.MULTILINE)
        except OSError:
            pass
    return ids


def packages_from(repo):
    # The installed packages that came from this repository, as NAME.ARCH.
    # A release package updated from its own repository does not count: it goes with the repository.
    ids = set(repo_ids(repo))
    lines = query('dnf', 'repoquery', '--installed', '--qf', '%{name}.%{arch} %{from_repo}\n').stdout.splitlines() if ids else []
    return {fields[0] for fields in map(str.split, lines) if len(fields) == 2 and fields[1] in ids
            and fields[0].rsplit('.', 1)[0] != repo.get('package')}


def remove(names):
    # Only what can go: a package something that stays still needs is left installed.
    names = removable(names)[0]
    if names:
        sudo('dnf', 'remove', '-y', *names)


def remove_repo(repo):
    if repo['kind'] == 'copr':
        sudo('dnf', 'copr', 'remove', '-y', repo['name'])
    elif repo['kind'] == 'release':
        remove([repo['package']])
    else:
        sudo('rm', '-f', str(repo_file(repo)))


def auth_revert(items, tablet_auth):
    # The profile first: tablet-auth.sh selects local again with the same features.
    if AUTH_PROFILE in items:
        subprocess.run((str(tablet_auth), 'remove'), check=True)
    if AUTH_FEATURE in items:
        sudo('authselect', 'disable-feature', AUTH_FEATURE)


def history():
    # Every transaction, oldest first, with the packages it changed.
    listed = query('dnf', 'history', 'list', '--json')
    try:
        ids = sorted(transaction['id'] for transaction in json.loads(listed.stdout or '[]'))
        command_lines = {transaction['id']: transaction.get('command_line', '') for transaction in json.loads(listed.stdout or '[]')}
        details = json.loads(query('dnf', 'history', 'info', '--json', *map(str, ids)).stdout or '[]') if ids else []
    except ValueError as error:
        raise RuntimeError(f'dnf history did not return JSON: {error}') from error
    for transaction in details:
        transaction['command_line'] = command_lines.get(transaction['id'], '')
    return sorted(details, key=lambda transaction: transaction['id'])


def nevra_name(nevra):
    # libva-intel-media-driver-0:26.3.5-1.fc45.x86_64 -> libva-intel-media-driver.x86_64
    name = nevra.rsplit('-', 2)[0]
    return f'{name}.{nevra.rsplit(".", 1)[-1]}'


def base_packages(transactions):
    # The installation of the system itself: the first transactions, Anaconda's, have no command line or an
    # --installroot. It ends at the first one typed in the system; later ones without a command line (PackageKit,
    # GNOME Software) came after it.
    last = 0
    for transaction in transactions:
        if transaction['command_line'] and '--installroot' not in transaction['command_line']:
            break
        last = transaction['id']
    return {nevra_name(package['nevra']) for t in transactions if t['id'] <= last
            for package in t.get('packages', ()) if package.get('action') not in ('Remove', 'Removed', 'Replaced')}


def default_zone():
    # The zone each edition starts with; editions without their own use firewalld's.
    for identity, zone in (('fedora-release-identity-workstation', 'FedoraWorkstation'), ('fedora-release-identity-server', 'FedoraServer')):
        if installed(identity):
            return zone
    return 'public'


def owned(path):
    return query('rpm', '-qf', str(path)).returncode == 0


def auth_reconstruct(packages):
    # Without a record: the tablet profile is always ours, the fingerprint feature only if fprintd-pam came with us.
    fields = query('authselect', 'current', '--raw').stdout.split()
    items = [AUTH_PROFILE] if fields[:1] == [AUTH_PROFILE] else []
    if AUTH_FEATURE in fields[1:] and any(name.rsplit('.', 1)[0] == 'fprintd-pam' for name in packages):
        items.append(AUTH_FEATURE)
    return items
