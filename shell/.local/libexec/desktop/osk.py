#!/usr/bin/env python3
"""Key events for the on-screen keyboard, through the Wayland virtual keyboard protocol.

run: a persistent virtual keyboard with the same XKB keymap as the physical one (Hyprland input:kb_layout),
so keys mean what the layout drawn by the shell says. One command per stdin line:
    key CODE MODS      press and release evdev CODE with the modifier mask MODS held
    press CODE / release CODE
check CODE MODS: prints {"keysym", "text"} for that key in the current layout.
The client speaks the Wayland wire protocol itself, so it needs nothing beyond the standard library and
libxkbcommon.
"""
from i18n import tr
import ctypes
import json
import os
import socket
import struct
import subprocess
import sys
import time

# Modifier masks of the evdev XKB keymaps: Shift, Lock, Control, Mod1 (Alt), Mod4 (Super), Mod5 (AltGr).
MASKS = {'shift': 1, 'lock': 2, 'ctrl': 4, 'alt': 8, 'super': 64, 'altgr': 128}


class RuleNames(ctypes.Structure):
    _fields_ = [(name, ctypes.c_char_p) for name in ('rules', 'model', 'layout', 'variant', 'options')]


class Xkb:
    def __init__(self, layout, variant='', options=''):
        self.lib = ctypes.CDLL('libxkbcommon.so.0')
        self.libc = ctypes.CDLL(None)
        lib = self.lib
        lib.xkb_context_new.restype = ctypes.c_void_p
        lib.xkb_context_new.argtypes = [ctypes.c_int]
        lib.xkb_keymap_new_from_names.restype = ctypes.c_void_p
        lib.xkb_keymap_new_from_names.argtypes = [ctypes.c_void_p, ctypes.POINTER(RuleNames), ctypes.c_int]
        lib.xkb_keymap_get_as_string.restype = ctypes.c_void_p
        lib.xkb_keymap_get_as_string.argtypes = [ctypes.c_void_p, ctypes.c_int]
        lib.xkb_state_new.restype = ctypes.c_void_p
        lib.xkb_state_new.argtypes = [ctypes.c_void_p]
        lib.xkb_state_update_mask.argtypes = [ctypes.c_void_p] + [ctypes.c_uint32] * 6
        lib.xkb_state_key_get_one_sym.restype = ctypes.c_uint32
        lib.xkb_state_key_get_one_sym.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
        lib.xkb_state_key_get_utf8.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_char_p, ctypes.c_size_t]
        lib.xkb_keysym_get_name.argtypes = [ctypes.c_uint32, ctypes.c_char_p, ctypes.c_size_t]
        self.libc.free.argtypes = [ctypes.c_void_p]
        context = lib.xkb_context_new(0)
        names = RuleNames(b'evdev', b'pc105', layout.encode(), variant.encode(), options.encode())
        self.keymap = lib.xkb_keymap_new_from_names(context, ctypes.byref(names), 0)
        if not self.keymap:
            raise ValueError(tr('osk.errors.keymap', [layout]))

    def text(self):
        pointer = self.lib.xkb_keymap_get_as_string(self.keymap, 1)
        try:
            return ctypes.string_at(pointer)
        finally:
            self.libc.free(pointer)

    def lookup(self, code, mods):
        state = self.lib.xkb_state_new(self.keymap)
        self.lib.xkb_state_update_mask(state, mods, 0, 0, 0, 0, 0)
        name, text = ctypes.create_string_buffer(64), ctypes.create_string_buffer(16)
        self.lib.xkb_keysym_get_name(self.lib.xkb_state_key_get_one_sym(state, code + 8), name, 64)
        self.lib.xkb_state_key_get_utf8(state, code + 8, text, 16)
        return {'keysym': name.value.decode(), 'text': text.value.decode()}


def layout():
    values = []
    for option in ('input:kb_layout', 'input:kb_variant', 'input:kb_options'):
        try:
            value = json.loads(subprocess.check_output(['hyprctl', '-j', 'getoption', option], text=True)).get('str', '')
        except (OSError, ValueError, subprocess.CalledProcessError):
            value = ''
        # Hyprland reports an unset option as [[EMPTY]].
        values.append('' if value == '[[EMPTY]]' else value)
    return values[0] or 'us', values[1], values[2]


class Wayland:
    def __init__(self):
        path = os.path.join(os.environ['XDG_RUNTIME_DIR'], os.environ.get('WAYLAND_DISPLAY', 'wayland-0'))
        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.socket.connect(path)
        self.next_id = 2
        self.buffer = b''
        self.globals = {}
        self.listeners = {}
        self.registry = self.new_id()
        self.send(1, 1, struct.pack('<I', self.registry))
        self.roundtrip()

    def new_id(self):
        value = self.next_id
        self.next_id += 1
        return value

    def send(self, obj, opcode, payload=b'', fds=()):
        message = struct.pack('<II', obj, (8 + len(payload)) << 16 | opcode) + payload
        if fds:
            self.socket.sendmsg([message], [(socket.SOL_SOCKET, socket.SCM_RIGHTS, struct.pack('<%di' % len(fds), *fds))])
        else:
            self.socket.sendall(message)

    @staticmethod
    def string(value):
        data = value.encode() + b'\0'
        return struct.pack('<I', len(data)) + data + b'\0' * (-len(data) % 4)

    def read(self):
        data = self.socket.recv(65536)
        if not data:
            raise ConnectionError('wayland')
        self.buffer += data
        while len(self.buffer) >= 8:
            obj, word = struct.unpack('<II', self.buffer[:8])
            size = word >> 16
            if len(self.buffer) < size:
                break
            body, self.buffer = self.buffer[8:size], self.buffer[size:]
            self.event(obj, word & 0xffff, body)

    def event(self, obj, opcode, body):
        if obj == 1 and opcode == 0:
            _, code, length = struct.unpack('<III', body[:12])
            raise ConnectionError(body[12:12 + length - 1].decode())
        if obj == self.registry and opcode == 0:
            name, length = struct.unpack('<II', body[:8])
            interface = body[8:8 + length - 1].decode()
            version = struct.unpack('<I', body[8 + (length + 3 & ~3):][:4])[0]
            self.globals[interface] = (name, version)
        handler = self.listeners.get(obj)
        if handler:
            handler(opcode, body)

    def roundtrip(self):
        callback = self.new_id()
        done = []
        self.listeners[callback] = lambda opcode, body: done.append(True)
        self.send(1, 0, struct.pack('<I', callback))
        while not done:
            self.read()
        del self.listeners[callback]

    def bind(self, interface, version):
        if interface not in self.globals:
            raise ValueError(tr('osk.errors.protocol', [interface]))
        name, available = self.globals[interface]
        obj = self.new_id()
        self.send(self.registry, 0, struct.pack('<I', name) + self.string(interface) + struct.pack('<II', min(version, available), obj))
        return obj


class VirtualKeyboard:
    def __init__(self, xkb):
        self.wayland = Wayland()
        seat = self.wayland.bind('wl_seat', 7)
        manager = self.wayland.bind('zwp_virtual_keyboard_manager_v1', 1)
        self.keyboard = self.wayland.new_id()
        self.wayland.send(manager, 0, struct.pack('<II', seat, self.keyboard))
        keymap = xkb.text() + b'\0'
        fd = os.memfd_create('desktop-osk-keymap', os.MFD_CLOEXEC)
        os.write(fd, keymap)
        self.wayland.send(self.keyboard, 0, struct.pack('<II', 1, len(keymap)), [fd])
        os.close(fd)
        self.wayland.roundtrip()
        self.start = time.monotonic()

    def time(self):
        return int((time.monotonic() - self.start) * 1000) & 0xffffffff

    def modifiers(self, mask):
        self.wayland.send(self.keyboard, 2, struct.pack('<IIII', mask, 0, 0, 0))

    def key(self, code, pressed):
        self.wayland.send(self.keyboard, 1, struct.pack('<III', self.time(), code, 1 if pressed else 0))

    def tap(self, code, mods):
        if mods:
            self.modifiers(mods)
        self.key(code, True)
        self.key(code, False)
        if mods:
            self.modifiers(0)


def run():
    keyboard = VirtualKeyboard(Xkb(*layout()))
    print(json.dumps({'status': 'ready'}), flush=True)
    for line in sys.stdin:
        words = line.split()
        try:
            if len(words) == 3 and words[0] == 'key':
                keyboard.tap(int(words[1]), int(words[2]))
            elif len(words) == 2 and words[0] in ('press', 'release'):
                keyboard.key(int(words[1]), words[0] == 'press')
        except ValueError:
            continue


def main():
    arguments = sys.argv[1:]
    if arguments == ['run']:
        run()
    elif len(arguments) == 3 and arguments[0] == 'check':
        print(json.dumps(Xkb(*layout()).lookup(int(arguments[1]), int(arguments[2])), ensure_ascii=False))
    else:
        raise ValueError(tr('osk.errors.usage'))


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, ConnectionError) as error:
        print(error, file=sys.stderr)
        sys.exit(1)
