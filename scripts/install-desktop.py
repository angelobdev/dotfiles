#!/usr/bin/env python3
"""Turn an installed distribution into this desktop, or back: dry-run shows the work, apply does it, post ends it after login."""
from argparse import ArgumentParser
import os
from pathlib import Path
import subprocess
import sys

# The installer's modules (scripts/install), which the guided installer imports too.
sys.path.insert(0, str(Path(__file__).resolve().parent / 'install'))
import install_paths  # noqa: E402
import install_pins  # noqa: E402
import install_plan  # noqa: E402
import install_removal  # noqa: E402
import install_run  # noqa: E402
import install_undo  # noqa: E402


def main(argv=None):
    parser = ArgumentParser(description=__doc__)
    parser.add_argument('action', nargs='?', choices=('dry-run', 'apply', 'post', 'pins'), default='dry-run',
                        help='pins: newer commits than the manifest pins, of AUR packages and clones (from any distribution)')
    parser.add_argument('--update', action='store_true', help='with pins: pin those newer commits in the manifest')
    parser.add_argument('--firmware', metavar='DIR', help='directory searched (by hash) for the vendor firmware the manifest lists')
    parser.add_argument('--profiles', help=f'comma separated, from {", ".join(install_paths.PROFILES)} and their parts, as profile.part (default: '
                        f'{install_paths.DEFAULT_PROFILES} with their default parts, and tablet on a 2-in-1)')
    parser.add_argument('--uninstall', action='store_true', help='undo what apply set up, from its record (dry-run shows it, apply does it)')
    parser.add_argument('--remove', metavar='PROFILES', help='undo what only these profiles set up (comma separated, not core), '
                        'leaving what the other installed profiles need')
    parser.add_argument('--keep', metavar='UNITS', help='with --remove: units on this system without a record of them, which stay and '
                        'are recorded from now on (Settings passes what it finds installed)')
    args = parser.parse_args(argv)
    if (args.uninstall or args.remove) and args.action in ('post', 'pins'):
        parser.error('--uninstall and --remove go with dry-run or apply.')
    if args.uninstall and args.remove:
        parser.error('--uninstall removes every profile: leave --remove out.')
    removed = tuple(args.remove.split(',')) if args.remove else ()
    kept = tuple(args.keep.split(',')) if args.keep else ()
    if kept and (not removed or set(kept) - set(install_plan.manifest_units())):
        parser.error(f'--keep goes with --remove, and takes {", ".join(install_plan.manifest_units()[1:])}.')
    if args.remove and not install_removal.removable_profiles(removed):
        parser.error(f'--remove takes {", ".join(install_plan.manifest_units()[1:])}; core goes only with --uninstall.')
    # Removing a profile removes its parts.
    removed = install_plan.with_parts(removed)
    if args.update and args.action != 'pins':
        parser.error('--update goes with pins.')
    profiles = tuple((args.profiles or install_plan.default_profiles()).split(','))
    if not install_plan.valid_profiles(profiles):
        parser.error(f'--profiles needs core, and takes only {", ".join(install_plan.manifest_units())}.')
    # A part brings its profile.
    profiles = install_plan.normalized(profiles)
    if os.geteuid() == 0:
        sys.exit('Run as the desktop user: the script asks sudo for each system change.')
    if args.action == 'pins':
        return install_pins.pins(args.update)
    plan = install_plan.load_plan(profiles, firmware=args.firmware, any_version=args.uninstall)
    plan.distro.remember_answers()
    if removed:
        install_run.refuse(plan)
        if args.action == 'apply' and 'plugins' in removed:
            install_run.refuse_uninstall()
        plan = install_removal.removal_plan(plan, removed, preview=args.action == 'dry-run', keep=kept)
        for note in install_run.record_notes(plan):
            print('Note: ' + note)
        done = install_run.run_steps(plan, args.action == 'dry-run', install_removal.PROFILE_UNSTEPS)
        if not done:
            print('Nothing to do.')
        elif args.action == 'apply':
            print(f'Done: {", ".join(removed)} removed. Not undone: what you changed by hand.')
        return 0
    if args.uninstall:
        install_run.refuse(plan)
        if args.action == 'apply':
            install_run.refuse_uninstall()
        plan = install_undo.uninstall_plan(plan, preview=args.action == 'dry-run')
        for note in install_run.record_notes(plan):
            print('Note: ' + note)
        done = install_run.run_steps(plan, args.action == 'dry-run', install_undo.UNSTEPS)
        if args.action == 'apply':
            install_run.after_uninstall(plan, done)
        elif not done:
            print('Nothing to do.')
        return 0
    install_run.preflight(plan)
    if args.action == 'post':
        install_run.post(plan)
        return 0
    for note in install_run.recording_notes(plan):
        print('Note: ' + note)
    done = install_run.run_steps(plan, args.action == 'dry-run')
    if args.action == 'apply':
        install_run.next_steps(plan, done)
    elif not done:
        print('Nothing to do.')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (subprocess.CalledProcessError, RuntimeError, OSError) as error:
        sys.exit(str(error))
