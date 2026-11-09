#!/usr/bin/env python3
"""The polkit PAM stacks (scripts/privileged/polkit-1.*): the fingerprint first, then the password.

Each stack runs through Linux-PAM itself (pam_start_confdir on a copy), with stand-ins where a test cannot act: the
fingerprint step and tablet mode are true or false, a right password makes pam_unix pam_permit, and pam_faildelay and
pam_faillock become pam_permit. A wrong password still goes to the real pam_unix. The fingerprint step itself
(desktop-fingerprint) runs against a stand-in fprintd-verify.
"""
import ctypes
import ctypes.util
import getpass
import os
from pathlib import Path
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[2]
PRIVILEGED = REPO / 'scripts/privileged'
FINGERPRINT = PRIVILEGED / 'desktop-fingerprint'
PROMPT_ECHO_OFF, PROMPT_ECHO_ON = 1, 2
# PAM_FAIL_DELAY: a function of ours instead of the sleep pam_unix asks for after a wrong password.
FAIL_DELAY = 10
NO_DELAY = ctypes.CFUNCTYPE(None, ctypes.c_int, ctypes.c_uint, ctypes.c_void_p)(lambda *_: None)


def load_pam():
    try:
        pam = ctypes.CDLL(ctypes.util.find_library('pam') or 'libpam.so.0')
        pam.pam_start_confdir
    except (OSError, AttributeError):
        return None
    return pam


PAM = load_pam()


class Message(ctypes.Structure):
    _fields_ = [('style', ctypes.c_int), ('text', ctypes.c_char_p)]


class Response(ctypes.Structure):
    _fields_ = [('text', ctypes.c_void_p), ('code', ctypes.c_int)]


CONVERSE = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.POINTER(Message)),
                            ctypes.POINTER(ctypes.POINTER(Response)), ctypes.c_void_p)


class Conversation(ctypes.Structure):
    _fields_ = [('converse', CONVERSE), ('data', ctypes.c_void_p)]


LIBC = ctypes.CDLL(None)
LIBC.calloc.restype = ctypes.c_void_p
LIBC.strdup.restype = ctypes.c_void_p


def authenticate(stack, answer):
    """True when the stack lets the user in with this answer, and the prompts it asked."""
    prompts = []

    def converse(count, messages, responses, _data):
        array = ctypes.cast(LIBC.calloc(count, ctypes.sizeof(Response)), ctypes.POINTER(Response))
        for index in range(count):
            message = messages[index].contents
            prompts.append(message.text.decode())
            if message.style in (PROMPT_ECHO_OFF, PROMPT_ECHO_ON):
                array[index].text = LIBC.strdup(answer.encode())
        responses[0] = array
        return 0

    conversation = Conversation(CONVERSE(converse), None)
    PAM.pam_start_confdir.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.POINTER(Conversation), ctypes.c_char_p,
                                      ctypes.POINTER(ctypes.c_void_p)]
    with tempfile.TemporaryDirectory() as folder:
        (Path(folder) / 'polkit-1').write_text(stack)
        handle = ctypes.c_void_p()
        status = PAM.pam_start_confdir(b'polkit-1', getpass.getuser().encode(), ctypes.byref(conversation),
                                       folder.encode(), ctypes.byref(handle))
        if status != 0:
            raise RuntimeError(f'pam_start_confdir: {status}')
        PAM.pam_set_item(handle, FAIL_DELAY, NO_DELAY)
        status = PAM.pam_authenticate(handle, 0)
        PAM.pam_end(handle, status)
    return status == 0, prompts


@unittest.skipIf(PAM is None, 'Linux-PAM with pam_start_confdir is not here')
class Stacks(unittest.TestCase):
    def stack(self, distro, finger, right_password=False, tablet=False):
        text = (PRIVILEGED / f'polkit-1.{distro}').read_text()
        for stand_in in ('pam_faildelay.so delay=2000000', 'pam_faillock.so preauth', 'pam_faillock.so authfail', 'pam_faillock.so authsucc'):
            text = text.replace(stand_in, 'pam_permit.so')
        text = text.replace('/usr/local/libexec/desktop-fingerprint', '/usr/bin/true' if finger else '/usr/bin/false')
        text = text.replace('/usr/local/libexec/desktop-tablet-mode', '/usr/bin/true' if tablet else '/usr/bin/false')
        if right_password:
            text = text.replace('pam_unix.so nullok', 'pam_permit.so')
        return text

    def check(self, distro, stack, answer, admitted, prompts):
        got, asked = authenticate(stack, answer)
        self.assertEqual(got, admitted, f'{distro}, answer {answer!r}')
        self.assertEqual(len(asked), prompts, asked)

    def test_both_distributions(self):
        for distro in ('fedora', 'arch'):
            with self.subTest(distro):
                # The fingerprint first: a match needs no password at all.
                self.check(distro, self.stack(distro, finger=True), 'not-the-password', True, 0)
                # Then the password: the reader gave up, or Use password stopped it. (The right password's stand-in,
                # pam_permit, asks nothing; the real pam_unix asks once.)
                self.check(distro, self.stack(distro, finger=False, right_password=True), 'the-password', True, 0)
                self.check(distro, self.stack(distro, finger=False), 'not-the-password', False, 1)
                # Tablet mode never asks the reader.
                self.check(distro, self.stack(distro, finger=True, tablet=True), 'not-the-password', False, 1)
                self.check(distro, self.stack(distro, finger=True, right_password=True, tablet=True), 'the-password', True, 0)


class FingerprintStep(unittest.TestCase):
    """desktop-fingerprint against a stand-in fprintd-verify, with the Use password file in a temporary folder."""

    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        self.skip = self.root / 'polkit-password'
        self.calls = self.root / 'calls'
        script = FINGERPRINT.read_text().replace('/run/user/$uid/desktop-shell/polkit-password', str(self.skip))
        self.script = self.root / 'desktop-fingerprint'
        self.script.write_text(script)
        (self.root / 'bin').mkdir()

    def verify(self, body):
        tool = self.root / 'bin/fprintd-verify'
        tool.write_text(f'#!/bin/sh\necho "$*" >> {self.calls}\n{body}\n')
        tool.chmod(0o755)

    def step(self, timeout=20):
        import subprocess
        environment = {'PATH': f'{self.root / "bin"}:/usr/bin:/bin', 'PAM_USER': getpass.getuser()}
        started = __import__('time').monotonic()
        status = subprocess.run(['sh', str(self.script)], env=environment, timeout=timeout).returncode
        return status, __import__('time').monotonic() - started

    def called(self):
        return self.calls.read_text().splitlines() if self.calls.exists() else []

    def test_a_match(self):
        self.verify('exit 0')
        self.assertEqual(self.step()[0], 0)
        self.assertEqual(self.called(), ['-- ' + getpass.getuser()])

    def test_three_scans_that_do_not_match(self):
        self.verify('exit 1')
        self.assertEqual(self.step()[0], 1)
        self.assertEqual(len(self.called()), 3)

    def test_use_password_before_it_starts(self):
        self.verify('exit 0')
        self.skip.touch()
        self.assertEqual(self.step()[0], 1)
        self.assertEqual(self.called(), [])

    def test_use_password_while_it_waits_for_a_finger(self):
        import subprocess
        self.verify('sleep 20; exit 0')
        environment = {'PATH': f'{self.root / "bin"}:/usr/bin:/bin', 'PAM_USER': getpass.getuser()}
        running = subprocess.Popen(['sh', str(self.script)], env=environment)
        __import__('time').sleep(0.6)
        self.skip.touch()
        self.assertEqual(running.wait(timeout=5), 1)
        self.assertEqual(len(self.called()), 1)

    def test_an_unknown_user(self):
        self.verify('exit 0')
        import subprocess
        status = subprocess.run(['sh', str(self.script)], env={'PATH': f'{self.root / "bin"}:/usr/bin:/bin', 'PAM_USER': 'no-such-user-here'}).returncode
        self.assertEqual(status, 1)
        self.assertEqual(self.called(), [])

if __name__ == '__main__':
    unittest.main()
