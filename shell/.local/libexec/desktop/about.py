#!/usr/bin/env python3
"""What Settings → System → About shows, as one JSON object: the distribution, the computer, the kernel, the
processor and memory, Hyprland and Quickshell, and the desktop repository's commit. Anything unreadable is
an empty string, never an error."""
import json
import os
from pathlib import Path
import platform
import re
import subprocess

# This file is a Stow link into the repository: shell/.local/libexec/desktop/about.py.
REPO = Path(__file__).resolve().parents[4]


def run(command, timeout=3):
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False)
    except (OSError, subprocess.SubprocessError):
        return ''
    return result.stdout.strip() if result.returncode == 0 else ''


def read(path):
    try:
        return Path(path).read_text(encoding='utf-8', errors='replace').strip()
    except OSError:
        return ''


def os_release(path='/etc/os-release'):
    values = {}
    for line in read(path).splitlines():
        key, _, value = line.partition('=')
        values[key] = value.strip().strip('"\'')
    return values.get('PRETTY_NAME') or values.get('NAME', '')


def model(root='/sys/class/dmi/id'):
    # Vendor and product as the firmware gives them, minus placeholders some boards leave in.
    placeholders = ('to be filled by o.e.m.', 'system product name', 'system manufacturer', 'default string')
    vendor, product = (read(f'{root}/{name}') for name in ('sys_vendor', 'product_name'))
    vendor = '' if vendor.lower() in placeholders else vendor
    product = '' if product.lower() in placeholders else product
    # "HP" and "HP OmniBook …": the vendor once.
    if vendor and product.lower().startswith(vendor.lower()):
        return product
    return ' '.join(part for part in (vendor, product) if part)


def processor(path='/proc/cpuinfo'):
    # The name and the number of threads (one "model name" line each).
    names = re.findall(r'^model name\s*:\s*(.+)$', read(path), re.M)
    return {'name': names[0].strip() if names else '', 'threads': len(names)}


def memory(path='/proc/meminfo'):
    found = re.search(r'^MemTotal:\s*(\d+) kB', read(path), re.M)
    return f'{int(found[1]) / 1024 / 1024:.1f} GiB' if found else ''


def hyprland():
    try:
        version = json.loads(run(['hyprctl', 'version', '-j']) or '{}')
    except ValueError:
        return ''
    return str(version.get('tag') or version.get('version') or '').lstrip('v')


def quickshell():
    # "quickshell 0.3.0, revision …": the version number only.
    found = re.search(r'(\d+\.\d+(?:\.\d+)?)', run(['qs', '--version']))
    return found[1] if found else ''


def repository(repo=REPO):
    if not (repo / '.git').exists():
        return {'commit': '', 'date': '', 'changed': False, 'path': str(repo)}
    line = run(['git', '-C', str(repo), 'log', '-1', '--format=%h%x09%cs'])
    commit, _, date = line.partition('\t')
    changed = run(['git', '-C', str(repo), 'status', '--porcelain', '--untracked-files=no']) != ''
    return {'commit': commit, 'date': date, 'changed': changed, 'path': str(repo)}


def about():
    return {
        'distribution': os_release(),
        'model': model(),
        'kernel': platform.release(),
        'processor': processor(),
        'memory': memory(),
        'hyprland': hyprland() if os.environ.get('HYPRLAND_INSTANCE_SIGNATURE') else '',
        'quickshell': quickshell(),
        'repository': repository(),
    }


if __name__ == '__main__':
    print(json.dumps(about(), ensure_ascii=False))
