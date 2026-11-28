#!/usr/bin/env python3
"""The wallpapers of the desktop's own themes (Glass, Glass Light, Graphite, High Contrast), drawn by ffmpeg.

Each theme has four: the first moves, as in Omarchy (a loop that plays in its place and an intro that ends on it, see
components/WallpaperVideo.qml), the other three are stills. They are made here, from expressions of the pixel and of
time, in the colours of the theme, so they are ours to ship; the files live on the GitHub release TAG of this
repository, not in it, and the themes list them with their sha256 like the Omarchy ones.

  render OUT [--preview] [--only THEME]   draw what is missing into OUT (--preview: small stills, no videos)
  manifest OUT                            write the `wallpapers` of the four themes from the files in OUT
  publish OUT                             upload the files of OUT to the release TAG (created when missing)

A drawing is up to three masks (0 to 1) computed per pixel by geq in one pass, painted over the base colour by a
channel mixer: soft ones are computed small and scaled up, sharp ones at full size with edges one pixel wide. A loop
moves only by whole periods of LOOP seconds, so its last frame leads into its first; an intro is the still growing in
(p from 0 to 1) and ends on it.
"""
import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
THEMES = REPO / 'shell/.local/share/desktop/themes'
GITHUB = 'angelobdev/dotfiles'
TAG = 'wallpapers-1'
SIZE = (3840, 2400)
VIDEO = (2560, 1600)
FPS = 24
LOOP = 12
INTRO = 5
# JPEG with full colour: WebP leaves faint rings in these smooth gradients.
STILL = '.jpg'

# The coordinates of an expression: x across, 0 to 1, and y down in the same unit (0 to 0.625 at 16:10), so circles
# stay round; ONE is a pixel in that unit.
x, y, ONE = '(X/W)', '(Y/W)', '(1/W)'


def angle(t, turns=1, phase=0):
    return f'(2*PI*{turns}*{t}/{LOOP}+{phase})'


def blob(cx, cy, r):
    return f'exp(-(pow({x}-({cx}),2)+pow({y}-({cy}),2))/({r}))'


def disc(cx, cy, r):
    return f'clip((({r})-hypot({x}-({cx}),{y}-({cy})))*W+0.5,0,1)'


def line(distance, width=1.5):
    """A line where distance (in x units) is 0, width pixels wide."""
    return f'clip(1-abs({distance})*W/{width},0,1)'


def contours(field, levels, width=0.07):
    return f'clip(1-abs(sin(PI*(({field})*{levels})))/{width},0,1)'


def hexrgb(value):
    return [int(value[i:i + 2], 16) for i in (1, 3, 5)]


class Design:
    """One wallpaper: masks(t, p) gives up to three expressions over the base colour, each painted in its colour.
    soft: computed at this width and scaled up (blurred); grain: noise against banding; moving: has videos."""

    def __init__(self, name, base, colors, masks, soft=0, grain=2, moving=False):
        self.name, self.base, self.colors, self.masks = name, hexrgb(base), [hexrgb(c) for c in colors], masks
        self.soft, self.grain, self.moving = soft, grain, moving

    def filters(self, size, t, p, video=False):
        masks = (self.masks(t, p) + ['0', '0'])[:3]
        width, height = size
        work = (self.soft, round(self.soft * height / width)) if self.soft else size
        planes = ':'.join(f"{plane}='255*clip({mask},0,1)'" for plane, mask in zip('rgb', masks))
        # Each output channel adds the masks' distance from the base (dark base) or takes it away (light base), so
        # the mixer needs only positive weights.
        mixer, lut = [], []
        for channel, name in enumerate('rgb'):
            base = self.base[channel]
            lighter = base < 128
            for mask, plane in enumerate('rgb'):
                color = self.colors[mask][channel] if mask < len(self.colors) else base
                weight = max(0, (color - base) if lighter else (base - color)) / 255
                mixer.append(f'{name}{plane}={weight:.4f}')
            lut.append(f"{name}='clip({base}{'+' if lighter else '-'}val,0,255)'")
        chain = [f'geq={planes}', 'colorchannelmixer=' + ':'.join(mixer), 'lutrgb=' + ':'.join(lut)]
        if self.soft:
            chain += [f'scale={width}:{height}:flags=bicubic', f'gblur=sigma={width / self.soft * 2:.1f}']
        if self.grain:
            chain.append(f'noise=alls={self.grain}:allf=t' if video else f'noise=alls={self.grain}')
        return work, ','.join(chain)


def ffmpeg(size, filters, duration, output, frames=None):
    source = f'color=c=black:s={size[0]}x{size[1]}:r={FPS}:d={duration},format=gbrp,{filters}'
    command = ['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', source]
    if frames:
        command += ['-frames:v', str(frames), str(output)]
    else:
        command += ['-vf', 'format=yuv420p', '-c:v', 'libx264', '-preset', 'slow', '-crf', '23', '-movflags', '+faststart',
                    str(output)]
    subprocess.run(command, check=True)


def ease():
    return f'(0.5-0.5*cos(PI*min(T/{INTRO},1)))'


def glass(name_prefix, base, palette, light=False):
    aurora, mesh, silk, horizon = palette

    def aurora_masks(t, p):
        a = angle(t)
        grow = f'(0.3+0.7*{p})'
        return [f'{p}*' + blob(f'0.28+0.12*sin({a})', f'0.26+0.06*cos({a})', f'0.030*{grow}'),
                f'{p}*' + blob(f'0.72+0.10*cos({a})', f'0.36+0.07*sin({angle(t, 2)})', f'0.035*{grow}'),
                f'{p}*' + blob(f'0.52+0.15*sin({angle(t, 1, 2)})', f'0.14+0.05*sin({angle(t, 1, 1)})', f'0.015*{grow}')]

    def silk_masks(t, p):
        return [f'exp(-pow(({y}-(0.24+0.05*sin({x}*5.1+0.6)+0.03*sin({x}*2.3)))/0.035,2))',
                f'exp(-pow(({y}-(0.33+0.06*sin({x}*4.3+2.1)+0.02*sin({x}*7.7)))/0.05,2))',
                f'exp(-pow(({y}-(0.42+0.04*sin({x}*6.2+4.0)+0.03*sin({x}*3.1)))/0.03,2))']

    def horizon_masks(t, p):
        return [f'exp(-(pow(({x}-0.5)/0.7,2)+pow(({y}-0.66)/0.18,2)))',
                line(f'{y}-0.52', 2) + f'*exp(-pow(({x}-0.5)/0.35,2))']

    return [
        Design('01-aurora', base, aurora, aurora_masks, soft=480, moving=True),
        Design('02-mesh', base, mesh, lambda t, p: [blob(0.15, 0.10, 0.09), blob(0.90, 0.55, 0.08), blob(0.20, 0.60, 0.05)], soft=480),
        Design('03-silk', base, silk, silk_masks, soft=1280),
        Design('04-horizon', base, horizon, horizon_masks),
    ]


def graphite():
    base = '#121316'

    def field(t):
        a = angle(t)
        return (f'(0.55*sin(3.3*{x}+1.2*sin({a})+0.4)+0.45*cos(4.1*{y}-0.9*cos({a})+1.7*sin(1.3*{x}))'
                f'+0.25*sin(5.7*({x}+{y})+0.5*sin({angle(t, 1, 1)})))')

    def contour_masks(t, p):
        # The levels flow by one whole step per loop; the intro brings them in from further along.
        flowing = f'({field(t)}+({t}/{LOOP}+1.5*(1-{p}))/4)'
        return [f'{p}*' + contours(flowing, 4) + f'*(0.55+0.45*exp(-pow(hypot({x}-0.6,{y}-0.3)/0.5,2)))',
                blob(0.62, 0.28, 0.08)]

    def rings(t, p):
        r = f'hypot({x}-1.05,{y}-0.7)'
        return [contours(r, 22, 0.05) + f'*exp(-{r}*1.2)', blob(1.0, 0.65, 0.15)]

    def folds(t, p):
        shade = f'(0.5+0.5*sin(({x}*1.4+{y})*9+0.8*sin({y}*5+{x}*2)))'
        return [f'pow({shade},3)', f'pow({shade},30)']

    return [
        Design('01-contours', base, ['#6e737c', '#23252a'], contour_masks, moving=True),
        Design('02-grain', base, ['#2c2f35'], lambda t, p: [blob(0.5, 0.25, 0.12)], soft=480, grain=7),
        Design('03-rings', base, ['#868b95', '#24262b'], rings),
        Design('04-folds', base, ['#2e3137', '#3f434a'], folds, soft=1280),
    ]


def high_contrast():
    base, yellow, white = '#000000', '#ffd400', '#ffffff'

    def sun(t, p):
        cy = f'(0.30+0.45*(1-{p}))'
        radius = 0.17
        # Slits across the lower half of the sun, thicker further down, drifting by one whole period per loop.
        depth = f'clip(({y}-{cy}+0.02)/{radius},0,1)'
        slit = f'clip((sin(2*PI*({y}*16-{t}/{LOOP}))-(0.95-1.1*{depth}))*6,0,1)*gt({depth},0)'
        horizon = 0.49
        below = f'lt({y},{horizon})'
        return [disc(0.5, cy, radius) + f'*(1-{slit})*{below}', f'{p}*' + line(f'{y}-{horizon}', 3)]

    def dots(t, p):
        step = 0.025
        d = f'hypot(mod({x},{step})-{step / 2},mod({y},{step})-{step / 2})'
        big = disc(0.78, 0.42, 0.06)
        return [big, f'clip((0.0035-{d})*W+0.5,0,1)*(1-{big})']

    def split(t, p):
        edge = f'({x}+0.9*{y}-1.05)'
        return [f'clip({edge}*W+0.5,0,1)', line(f'{edge}+0.07', 3)]

    def rings(t, p):
        r = f'hypot({x}-0.12,{y}-0.6)'
        return [f'clip((sin(2*PI*{r}*7)-0.6)*W/40,0,1)*gt({r},0.05)']

    return [
        Design('01-sun', base, [yellow, white], sun, grain=0, moving=True),
        Design('02-dots', base, [yellow, white], dots, grain=0),
        Design('03-split', base, [yellow, white], split, grain=0),
        Design('04-rings', base, [yellow], rings, grain=0),
    ]


DESIGNS = {
    'glass': glass('glass', '#0a0b12', [['#3d5afe', '#9b3fe0', '#22b8ff'], ['#1d3fa8', '#7a2fc0', '#0f7c9c'],
                                         ['#2f6bff', '#6a5cff', '#26c0ff'], ['#2b55ff', '#9fc4ff']]),
    'glass-light': glass('glass-light', '#f3f4f8', [['#8fb0ff', '#caa6f5', '#93dcff'], ['#a9c1ff', '#e0b8f0', '#a8e3e0'],
                                                     ['#7ea6ff', '#b3a8ff', '#8fd6ff'], ['#a9c4ff', '#3d6fe0']], light=True),
    'graphite': graphite(),
    'high-contrast': high_contrast(),
}


def asset(theme, design, kind):
    return f'{theme}-{design.name}' + (STILL if kind == 'still' else f'-{kind}.mp4')


def render(out, preview=False, only=None):
    out.mkdir(parents=True, exist_ok=True)
    for theme, designs in DESIGNS.items():
        if only and theme != only:
            continue
        for design in designs:
            still = out / (asset(theme, design, 'still').replace(STILL, '.png') if preview else asset(theme, design, 'still'))
            if not still.is_file():
                size = (480, 300) if preview else SIZE
                work, chain = design.filters(size, '0', '1')
                with tempfile.TemporaryDirectory() as folder:
                    png = still if preview else Path(folder) / 'still.png'
                    ffmpeg(work, chain, 1, png, frames=1)
                    if not preview:
                        subprocess.run(['magick', str(png), '-quality', '92', '-sampling-factor', '4:4:4', str(still)], check=True)
                print('drawn', still.name, flush=True)
            if preview or not design.moving:
                continue
            for kind, t, p, duration in (('loop', 'T', '1', LOOP), ('intro', '0', ease(), INTRO)):
                target = out / asset(theme, design, kind)
                if not target.is_file():
                    work, chain = design.filters(VIDEO, t, p, video=True)
                    ffmpeg(work, chain, duration, target)
                    print('drawn', target.name, flush=True)


def url(name):
    return f'https://github.com/{GITHUB}/releases/download/{TAG}/{name}'


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def manifest(out):
    for theme, designs in DESIGNS.items():
        path = THEMES / theme / 'theme.json'
        data = json.loads(path.read_text(encoding='utf-8'))
        entries = []
        for design in designs:
            still = out / asset(theme, design, 'still')
            entry = {'file': design.name + STILL, 'url': url(still.name), 'sha256': sha256(still), 'source': 'desktop'}
            if design.moving:
                for kind in ('loop', 'intro'):
                    video = out / asset(theme, design, kind)
                    entry[kind] = {'url': url(video.name), 'sha256': sha256(video)}
            entries.append(entry)
        data.pop('wallpaperDirectories', None)
        data['wallpapers'] = entries
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
        print('listed', theme, len(entries), 'wallpapers')


def publish(out):
    files = sorted(str(path) for path in out.iterdir() if path.suffix in (STILL, '.mp4'))
    exists = subprocess.run(['gh', 'release', 'view', TAG, '--repo', GITHUB], capture_output=True).returncode == 0
    if not exists:
        subprocess.run(['gh', 'release', 'create', TAG, '--repo', GITHUB, '--title', 'Wallpapers of the desktop themes',
                        '--notes', 'The wallpapers of Glass, Glass Light, Graphite and High Contrast, drawn by '
                        'scripts/wallpapers.py. Downloaded by the desktop at login; not a release of the desktop.',
                        '--latest=false', '--target', 'develop'], check=True)
    subprocess.run(['gh', 'release', 'upload', TAG, '--repo', GITHUB, '--clobber'] + files, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('command', choices=('render', 'manifest', 'publish'))
    parser.add_argument('out', type=Path)
    parser.add_argument('--preview', action='store_true')
    parser.add_argument('--only', choices=sorted(DESIGNS))
    arguments = parser.parse_args()
    if arguments.command == 'render':
        render(arguments.out, arguments.preview, arguments.only)
    elif arguments.command == 'manifest':
        manifest(arguments.out)
    else:
        publish(arguments.out)
    return 0


if __name__ == '__main__':
    sys.exit(main())
