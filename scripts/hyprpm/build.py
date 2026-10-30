#!/usr/bin/env python3
"""Pinned upstream builds, shared between preparation and hyprpm's build sandbox."""
import hashlib
from pathlib import Path
import shutil
import subprocess
import sys

PLUGINS = {
    'Hyprspace': ('KZDKM/Hyprspace', '258b7b8bcea177e99da74946cf5cddd1dfe0e1ab', 'Hyprspace.so'),
    'hyprgrass': ('horriblename/hyprgrass', '8ca1af717d5b4ea1215a781df52bcef02d7b15e6', 'build/src/libhyprgrass.so'),
    'hyprglass': ('hyprnux/hyprglass', '28b38df92176baf3d42fe58bf6c3b663d230c6c9', 'hyprglass.so'),
    'HyprCapture': ('gfhdhytghd/HyprCapture', 'fd465d85d953592862e30b296dd69ad746bc79af', 'build/libhyprcapture.so'),
}
# Keeps the fingers of a gesture from reaching the window under them.
HYPRGRASS_PATCH = Path(__file__).resolve().with_name('hyprgrass-hold-touches.patch')


def run(*args, **kwargs):
    return subprocess.run(args, check=True, **kwargs)


def rpm_version(package):
    return subprocess.check_output(['rpm', '-q', '--qf', '%{VERSION}-%{RELEASE}.%{ARCH}', package], text=True)


def fingerprint():
    version = rpm_version('hyprland')
    if version != rpm_version('hyprland-devel'):
        raise RuntimeError('hyprland and hyprland-devel must have the same RPM version')
    if version != '0.57.0-1.fc44.x86_64':
        raise RuntimeError('Hyprland build differs from the verified version: update and verify pins before building')
    return hashlib.sha256((version + Path(__file__).read_text() + HYPRGRASS_PATCH.read_text()).encode()).hexdigest()[:20]


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
        if name == 'hyprgrass':
            # A build that stopped halfway has already patched this checkout.
            run('git', 'checkout', '--', '.', cwd=cache)
            run('git', 'apply', str(HYPRGRASS_PATCH), cwd=cache)
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
