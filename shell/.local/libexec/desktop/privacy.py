#!/usr/bin/env python3
"""Who has a camera open, for the shell's privacy indicator.

watch: prints that list (below) at start and again whenever a camera device is opened or closed, from inotify on
/dev/video* and /dev (new devices): nothing runs in between. Scanning /proc every 3 s cost 2% of a core.
cameras: prints a JSON list of the process names holding a /dev/video* device open, the user's own processes
only (others' file descriptors are not readable). PipeWire itself shows up as "pipewire" when an app reads the
camera through it; the shell names that app from PipeWire's video streams.
"""
from i18n import tr
import ctypes
import json
import os
import select
import struct
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


# inotify(7): opened, closed (written or not), and in /dev a device added or removed.
IN_OPEN, IN_CLOSE_WRITE, IN_CLOSE_NOWRITE, IN_CREATE, IN_DELETE = 0x20, 0x08, 0x10, 0x100, 0x200


def watch(dev='/dev'):
    libc = ctypes.CDLL(None, use_errno=True)
    fd = libc.inotify_init1(os.O_CLOEXEC)
    if fd < 0:
        raise OSError(ctypes.get_errno(), 'inotify_init1')

    def add(path, mask):
        libc.inotify_add_watch(fd, os.fsencode(path), mask)
    add(dev, IN_CREATE | IN_DELETE)
    for name in os.listdir(dev):
        if name.startswith('video'):
            add(f'{dev}/{name}', IN_OPEN | IN_CLOSE_WRITE | IN_CLOSE_NOWRITE)
    previous = None
    while True:
        names = cameras()
        if names != previous:
            print(json.dumps(names), flush=True)
            previous = names
        # Wait for an event, or for the shell to go (stdin closes).
        ready, _, _ = select.select([fd, sys.stdin], [], [])
        if sys.stdin in ready and not sys.stdin.readline():
            return
        if fd in ready:
            data = os.read(fd, 65536)
            offset = 0
            while offset < len(data):
                _, mask, _, length = struct.unpack_from('iIII', data, offset)
                name = data[offset + 16:offset + 16 + length].rstrip(b'\0').decode(errors='replace')
                if mask & IN_CREATE and name.startswith('video'):
                    add(f'{dev}/{name}', IN_OPEN | IN_CLOSE_WRITE | IN_CLOSE_NOWRITE)
                offset += 16 + length


def main():
    if sys.argv[1:] == ['watch']:
        watch()
        return 0
    if sys.argv[1:] != ['cameras']:
        print(tr('privacy.errors.usage'), file=sys.stderr)
        return 2
    print(json.dumps(cameras()))
    return 0


if __name__ == '__main__':
    sys.exit(main())
