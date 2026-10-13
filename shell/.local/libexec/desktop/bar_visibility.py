#!/usr/bin/env python3
"""Watch compositor-hidden bars without unmapping their layer surfaces.

Hyprspace fades top layers to zero but leaves their exclusive zone and input
region intact. Keep the surfaces mapped so its restoration of alpha is observable.
"""
import json
import os
from pathlib import Path
import socket
import sys
import time


def hidden_bars(layers):
    result = []
    for monitor, data in layers.items():
        bars = [layer for group in data.get('levels', {}).values() for layer in group
                if layer.get('namespace') == 'desktop-bar']
        if bars and all(float(layer.get('alpha', 1)) <= 0.001 for layer in bars):
            result.append(monitor)
    return sorted(result)


def watch():
    instance = os.environ.get('HYPRLAND_INSTANCE_SIGNATURE')
    runtime = os.environ.get('XDG_RUNTIME_DIR')
    if not instance or not runtime:
        print('[]', flush=True)
        return
    path = Path(runtime) / 'hypr' / instance / '.socket.sock'
    previous = None
    while True:
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
                connection.settimeout(1)
                connection.connect(str(path))
                connection.sendall(b'j/layers')
                response = bytearray()
                while chunk := connection.recv(65536):
                    response.extend(chunk)
                    if len(response) > 4 * 1024 * 1024:
                        raise ValueError('Layer IPC response too large')
            state = hidden_bars(json.loads(response))
        except (OSError, ValueError, TypeError, AttributeError):
            state = []  # Release the suppression if the compositor disconnects.
        if state != previous:
            print(json.dumps(state), flush=True)
            previous = state
        time.sleep(0.1)


if __name__ == '__main__':
    try:
        watch()
    except (BrokenPipeError, KeyboardInterrupt):
        sys.exit(0)
