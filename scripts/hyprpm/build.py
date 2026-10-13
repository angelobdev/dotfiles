#!/usr/bin/env python3
"""Pinned upstream builds, shared between preparation and hyprpm's build sandbox."""
import hashlib
from pathlib import Path
import shutil
import subprocess
import sys

PLUGINS = {
    'Hyprspace': ('KZDKM/Hyprspace', 'cf08bed82621c1fb943ef4934ff0ba36540fea77', 'Hyprspace.so'),
    'hyprgrass': ('horriblename/hyprgrass', '8e605468cbf429791d61ddbfaeb14ff5e08fec3e', 'build/src/libhyprgrass.so'),
    'hyprglass': ('hyprnux/hyprglass', '84c1a5ab217101a317d4edaab7fba2efcc1bf346', 'hyprglass.so'),
    'hypr-hot-edge': ('claychinasky/hypr-hot-edge', '32b2dffdf2900a5a4b8cd10133f6a58cfd7ec4d6', 'build/hypr-hot-edge.so'),
    'HyprCapture': ('gfhdhytghd/HyprCapture', 'bf4d1f9021fc288200002f5a7d8291ed56f0df83', 'build/libhyprcapture.so'),
}


def run(*args, **kwargs):
    return subprocess.run(args, check=True, **kwargs)


def rpm_version(package):
    return subprocess.check_output(['rpm', '-q', '--qf', '%{VERSION}-%{RELEASE}.%{ARCH}', package], text=True)


def fingerprint():
    version = rpm_version('hyprland')
    if version != rpm_version('hyprland-devel'):
        raise RuntimeError('hyprland and hyprland-devel must have the same RPM version')
    if version != '0.56.2-17.fc44.x86_64':
        raise RuntimeError('Hyprland build differs from the verified version: update and verify pins before building')
    return hashlib.sha256((version + Path(__file__).read_text()).encode()).hexdigest()[:20]


def build(name):
    repo, revision, artifact = PLUGINS[name]
    cache = Path.home() / '.cache/dotfiles/hyprpm-build' / fingerprint() / name
    cache.parent.mkdir(parents=True, exist_ok=True)
    stamp = cache / '.dotfiles-built'
    if not stamp.exists() or not (cache / artifact).is_file():
        if not (cache / '.git').exists():
            cache.mkdir(parents=True, exist_ok=True)
            run('git', 'init', '-q', str(cache))
            run('git', 'remote', 'add', 'origin', 'https://github.com/' + repo + '.git', cwd=cache)
        run('git', 'fetch', '--depth', '1', 'origin', revision, cwd=cache)
        run('git', 'checkout', '--detach', revision, cwd=cache)
        run('git', 'submodule', 'update', '--init', '--recursive', '--depth', '1', cwd=cache)
        if name == 'hypr-hot-edge':
            # The plugin uses Lua APIs shared by 5.4/5.5; match Fedora's compositor.
            cmake = cache / 'CMakeLists.txt'
            text = cmake.read_text()
            old = 'pkg_search_module(LUA REQUIRED lua5.5 lua-5.5 lua55 lua>=5.5)'
            new = 'pkg_check_modules(LUA REQUIRED lua>=5.4 lua<5.5)'
            if old not in text and new not in text:
                raise RuntimeError('Lua patch context has changed')
            cmake.write_text(text.replace(old, new))
        jobs = '2'  # Keep desktop responsiveness and memory use predictable.
        if name in ('Hyprspace', 'hyprglass'):
            run('make', '-j' + jobs, cwd=cache)
        elif name == 'hyprgrass':
            run('meson', 'setup', 'build', '--reconfigure', cwd=cache) if (cache / 'build/build.ninja').exists() else run('meson', 'setup', 'build', cwd=cache)
            run('ninja', '-C', 'build', '-j' + jobs, cwd=cache)
        else:
            run('cmake', '-S', '.', '-B', 'build', '-DCMAKE_BUILD_TYPE=Release', '-DBUILD_TESTING=OFF', cwd=cache)
            run('cmake', '--build', 'build', '--parallel', jobs, cwd=cache)
        if not (cache / artifact).is_file():
            raise RuntimeError('Build produced no artifact: ' + name)
        stamp.write_text(revision + '\n')
    Path('out').mkdir(exist_ok=True)
    shutil.copy2(cache / artifact, Path('out') / (name + '.so'))
    if name == 'HyprCapture':
        # Screenshots need only the UI. Do not install or activate the optional
        # TensorFlow/AEC microphone pipeline as a side effect of screenshots.
        target = Path.home() / '.local/bin/hyprcapture-ui'
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(cache / 'build/hyprcapture-ui', target)
        target.chmod(0o755)
        licenses = Path.home() / '.local/share/licenses/hyprcapture'
        licenses.mkdir(parents=True, exist_ok=True)
        for source in (cache / 'resources/licenses').iterdir():
            if source.is_file():
                shutil.copy2(source, licenses / source.name)


if __name__ == '__main__':
    if len(sys.argv) != 2 or sys.argv[1] not in PLUGINS:
        sys.exit('Usage: build.py ' + '|'.join(PLUGINS))
    build(sys.argv[1])
