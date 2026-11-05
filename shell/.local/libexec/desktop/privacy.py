#!/usr/bin/env python3
"""Who has a camera open, for the shell's privacy indicator.

cameras: prints a JSON list of the process names holding a /dev/video* device open, the user's own processes
only (others' file descriptors are not readable). PipeWire itself shows up as "pipewire" when an app reads the
camera through it; the shell names that app from PipeWire's video streams.
"""
from i18n import tr
import json
import os
import sys


def cameras(proc='/proc'):
    names = set()
    for pid in os.listdir(proc):
        if not pid.isdigit():
            continue
        try:
            fds = os.listdir(f'{proc}/{pid}/fd')
        except OSError:
            continue
        for fd in fds:
            try:
                target = os.readlink(f'{proc}/{pid}/fd/{fd}')
            except OSError:
                continue
            if target.startswith('/dev/video'):
                try:
                    with open(f'{proc}/{pid}/comm', encoding='utf-8') as comm:
                        names.add(comm.read().strip())
                except OSError:
                    names.add(pid)
                break
    return sorted(names)


def main():
    if sys.argv[1:] != ['cameras']:
        print(tr('privacy.errors.usage'), file=sys.stderr)
        return 2
    print(json.dumps(cameras()))
    return 0


if __name__ == '__main__':
    sys.exit(main())
