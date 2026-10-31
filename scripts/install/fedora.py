"""Fedora operations of install-desktop.py; another distribution is a module with these same names."""
import os
from pathlib import Path
import subprocess
import tempfile

ADMIN_GROUP = 'wheel'
REPOS = Path('/etc/yum.repos.d')
AUTH_FEATURE = 'with-fingerprint'
AUTH_PROFILE = 'custom/desktop-tablet'


def query(*command):
    return subprocess.run(command, capture_output=True, text=True, env={**os.environ, 'LC_ALL': 'C'})


def sudo(*command):
    subprocess.run(('sudo', *command), check=True)


def missing(packages):
    # --whatprovides also takes capabilities, such as mesa-vulkan-drivers(x86-32).
    prefix = 'no package provides '
    lines = query('rpm', '-q', '--whatprovides', *packages).stdout.splitlines()
    return [line.removeprefix(prefix) for line in lines if line.startswith(prefix)]


def install(packages):
    sudo('dnf', 'install', '-y', *packages)


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


def write_file(path, content):
    with tempfile.NamedTemporaryFile('w', encoding='utf-8', prefix='desktop-install-') as temporary:
        temporary.write(content)
        temporary.flush()
        sudo('install', '-D', '-o', 'root', '-g', 'root', '-m', '0644', temporary.name, str(path))


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
