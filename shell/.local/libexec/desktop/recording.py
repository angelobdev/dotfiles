#!/usr/bin/env python3
"""Own a recorder child and finalize its file on shell exit or a stop request."""
from i18n import tr
import argparse
from collections import deque
from datetime import datetime
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import uuid


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', required=True)
    p.add_argument('--geometry', default='')
    p.add_argument('--audio', choices=('none', 'output', 'input'), default='none')
    p.add_argument('--codec', default='libvpx-vp9')
    p.add_argument('--fps', type=int, default=30)
    a = p.parse_args()
    os.umask(0o077)
    if a.geometry and not re.fullmatch(r'-?\d+,-?\d+ [1-9]\d*x[1-9]\d*', a.geometry):
        p.error(tr('Area non valida'))
    monitors = json.loads(subprocess.run(['hyprctl', '-j', 'monitors'], capture_output=True, text=True, check=True).stdout)
    output = next((m for m in monitors if m['name'] == a.output), None)
    if output is None:
        p.error(tr('Monitor non disponibile'))
    if a.geometry:
        x, y, w, h = map(int, re.findall(r'-?\d+', a.geometry))
        width, height = output['width'], output['height']
        if output.get('transform', 0) % 2:
            width, height = height, width
        width, height = round(width/output['scale']), round(height/output['scale'])
        if x < output['x'] or y < output['y'] or x+w > output['x']+width or y+h > output['y']+height:
            p.error(tr('L’area deve essere contenuta in un solo monitor'))
    folder = subprocess.run(['xdg-user-dir', 'VIDEOS'], capture_output=True, text=True, check=True).stdout.strip()
    directory = Path(folder or Path.home()/'Videos')/'Recordings'
    directory.mkdir(parents=True, exist_ok=True)
    destination = directory/(datetime.now().strftime('%Y-%m-%d_%H-%M-%S_')+uuid.uuid4().hex[:6]+'.mkv')
    # Reserve a new filename; never overwrite an existing user recording.
    command = ['wf-recorder', '--output', a.output, '--file', str(destination), '--codec', a.codec,
               '--framerate', str(max(1, min(60, a.fps))), '--overwrite']
    if a.codec == 'libvpx-vp9':
        command += ['--codec-param', 'deadline=realtime', '--codec-param', 'cpu-used=6']
    if a.geometry:
        command += ['--geometry', a.geometry]
    if a.audio != 'none':
        kind = 'sink' if a.audio == 'output' else 'source'
        device = subprocess.run(['pactl', 'get-default-'+kind], capture_output=True, text=True, check=True).stdout.strip()
        command += ['--audio='+device+('.monitor' if a.audio == 'output' else ''), '--audio-codec', 'libopus']
    destination.touch(exist_ok=False, mode=0o600)
    child = None
    stopped = False
    def stop(*_):
        nonlocal stopped
        stopped = True
        if child and child.poll() is None:
            child.send_signal(signal.SIGINT)
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    try:
        child = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        if stopped: stop()
        print(json.dumps({'recording': True, 'path': str(destination)}), flush=True)
        # Drain continuously to avoid a full pipe blocking the encoder.
        tail = deque(child.stderr, maxlen=12)
        code = child.wait()
        if destination.stat().st_size == 0:
            destination.unlink()
            print(json.dumps({'recording': False, 'error': tr('Registrazione non avviata: ')+''.join(tail)[-1200:]}), flush=True)
            return 1
        print(json.dumps({'recording': False, 'path': str(destination), 'error': '' if stopped or code == 0 else tr('Registrazione interrotta: ')+''.join(tail)[-1200:]}), flush=True)
        return 0 if stopped or code == 0 else 1
    finally:
        if child and child.poll() is None:
            stop()
            try: child.wait(timeout=15)
            except subprocess.TimeoutExpired:
                child.kill(); child.wait()
        if destination.exists() and destination.stat().st_size == 0:
            destination.unlink()


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(json.dumps({'recording': False, 'error': tr('Registrazione non riuscita: ')+str(error)}), flush=True)
        sys.exit(1)
