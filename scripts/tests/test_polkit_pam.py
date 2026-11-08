#!/usr/bin/env python3
"""The polkit PAM stacks (scripts/privileged/polkit-1.*): the password at once, the fingerprint on an empty answer.

Each stack runs through Linux-PAM itself (pam_start_confdir on a copy), with stand-ins where a test cannot act: the
reader (pam_fprintd) and a right password (the password path's pam_unix) become pam_permit or pam_deny, tablet mode is
true or false, and pam_faildelay and pam_faillock become pam_permit. A wrong password still goes to the real pam_unix.
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
WANTED = PRIVILEGED / 'desktop-fingerprint-wanted'
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
        text = (PRIVILEGED / f'polkit-1.{distro}').read_text().replace('/usr/local/libexec/desktop-fingerprint-wanted', str(WANTED))
        for stand_in in ('pam_faildelay.so delay=2000000', 'pam_faillock.so preauth', 'pam_faillock.so authfail', 'pam_faillock.so authsucc'):
            text = text.replace(stand_in, 'pam_permit.so')
        text = text.replace('pam_fprintd.so', 'pam_permit.so' if finger else 'pam_deny.so')
        text = text.replace('/usr/local/libexec/desktop-tablet-mode', '/usr/bin/true' if tablet else '/usr/bin/false')
        if right_password:
            # The password path's pam_unix, the last of the two.
            head, _, tail = text.rpartition('pam_unix.so use_first_pass nullok')
            text = head + 'pam_permit.so' + tail
        return text

    def check(self, distro, stack, answer, admitted):
        got, prompts = authenticate(stack, answer)
        self.assertEqual(got, admitted, f'{distro}, answer {answer!r}')
        self.assertEqual(len(prompts), 1, prompts)

    def test_both_distributions(self):
        for distro in ('fedora', 'arch'):
            with self.subTest(distro):
                self.check(distro, self.stack(distro, finger=True), 'not-the-password', False)
                self.check(distro, self.stack(distro, finger=False, right_password=True), 'the-password', True)
                self.check(distro, self.stack(distro, finger=True), '', True)
                # An empty answer never reaches the password check, even when that would pass.
                self.check(distro, self.stack(distro, finger=False, right_password=True), '', False)
                self.check(distro, self.stack(distro, finger=True, right_password=True, tablet=True), '', False)

    def test_an_empty_answer_is_told_from_a_password(self):
        import subprocess
        for data, wanted in ((b'', True), (b'\0', True), (b'x', False), (b'x\0', False), (b'\0x', False)):
            status = subprocess.run(['sh', str(WANTED)], input=data).returncode
            self.assertEqual(status == 0, wanted, data)


if __name__ == '__main__':
    unittest.main()
