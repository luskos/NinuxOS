#!/usr/bin/env python3
# qrun.py - start NinuxOS in QEMU and drive it from a script: type, click, wait for the log, take pictures.
#
#   python tools/qemu/qrun.py SCRIPT.txt [--img disk.img] [--out test/qemu/out] [--show]
#
# The disk image is opened with snapshot=on: nothing the system writes reaches the file.
# One command a line (the same words as the old test/qemu/q_*.txt scripts):
#   qemu ARGS            more arguments for QEMU (only as the first line; default: -smp 2 -m 512M)
#   waitlog TEXT [N]     wait until TEXT comes in the serial log, at most N seconds (default 30)
#   wait N               wait N seconds
#   type TEXT            type TEXT and press Enter
#   text TEXT            type TEXT, no Enter
#   enter / esc / tab / bksp
#   key NAME             one key by its QEMU name: f5, up, ctrl-c, alt-m, shift-a ...
#   snap NAME            save the screen as NAME.png
#   moveto X Y           move the mouse to the point X Y of the screen
#   click / rclick       press and let go the left / right button
#   drag X Y             hold the left button and move to X Y
#   # ...                a comment
# The serial log of the run is saved next to the pictures as serial.log.

import argparse
import os
import shutil
import socket
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))

KEYS = {' ': 'spc', '.': 'dot', ',': 'comma', '-': 'minus', '=': 'equal', '/': 'slash', ';': 'semicolon',
        "'": 'apostrophe', '[': 'bracket_left', ']': 'bracket_right', '\\': 'backslash', '`': 'grave_accent',
        '*': 'shift-8', '+': 'shift-equal', '_': 'shift-minus', ':': 'shift-semicolon', '"': 'shift-apostrophe',
        '(': 'shift-9', ')': 'shift-0', '!': 'shift-1', '?': 'shift-slash', '<': 'shift-comma', '>': 'shift-dot',
        '@': 'shift-2', '#': 'shift-3', '$': 'shift-4', '%': 'shift-5', '^': 'shift-6', '&': 'shift-7',
        '{': 'shift-bracket_left', '}': 'shift-bracket_right', '|': 'shift-backslash', '~': 'shift-grave_accent'}


def find_qemu():
    p = shutil.which('qemu-system-x86_64')
    if p:
        return p
    for d in (os.environ.get('QEMU_DIR', ''), r'C:\Program Files\qemu', r'C:\msys64\mingw64\bin'):
        if d and os.path.exists(os.path.join(d, 'qemu-system-x86_64.exe')):
            return os.path.join(d, 'qemu-system-x86_64.exe')
    sys.exit('cannot find qemu-system-x86_64')


class Machine:
    def __init__(self, img, out, extra, show):
        self.out = out
        os.makedirs(out, exist_ok=True)
        self.log = os.path.join(out, 'serial.log')
        if os.path.exists(self.log):
            os.remove(self.log)
        s = socket.socket()
        s.bind(('127.0.0.1', 0))
        port = s.getsockname()[1]
        s.close()
        args = [find_qemu()] + (extra or ['-smp', '2', '-m', '512M']) + [
            '-drive', 'file=%s,format=raw,snapshot=on' % img, '-serial', 'file:' + self.log,
            '-monitor', 'tcp:127.0.0.1:%d,server,nowait' % port, '-no-reboot']
        if not show:
            args += ['-display', 'none']
        self.proc = subprocess.Popen(args)
        self.mon = None
        for _ in range(100):
            try:
                self.mon = socket.create_connection(('127.0.0.1', port), timeout=5)
                break
            except OSError:
                time.sleep(0.1)
        if self.mon is None:
            sys.exit('QEMU did not start')
        self.read()
        self.x = self.y = None

    def read(self):
        data = b''
        self.mon.settimeout(5)
        try:
            while not data.rstrip().endswith(b'(qemu)'):
                part = self.mon.recv(65536)
                if not part:
                    break
                data += part
        except socket.timeout:
            pass
        return data.decode('latin-1')

    def cmd(self, line):
        self.mon.sendall(line.encode() + b'\n')
        return self.read()

    def key(self, name, pause=0.06):
        self.cmd('sendkey ' + name)
        time.sleep(pause)

    def text(self, t):
        for ch in t:
            if ch in KEYS:
                self.key(KEYS[ch])
            elif ch.isupper():
                self.key('shift-' + ch.lower())
            else:
                self.key(ch)

    def waitlog(self, text, seconds):
        end = time.time() + seconds
        while time.time() < end:
            try:
                if text in open(self.log, errors='replace').read():
                    return True
            except OSError:
                pass
            time.sleep(0.2)
        print('  !! not in the log after %d s: %s' % (seconds, text))
        return False

    def snap(self, name):
        path = os.path.join(self.out, name + '.png')
        self.cmd('screendump %s -f png' % path.replace('\\', '/'))
        time.sleep(0.3)

    def moveto(self, x, y):
        # the PS/2 mouse only knows "so much further": go to the top left corner first, then out
        if self.x is None:
            for _ in range(12):
                self.cmd('mouse_move -200 -200')
                time.sleep(0.02)
            self.x = self.y = 0
        dx, dy = x - self.x, y - self.y
        while dx or dy:
            sx = max(-40, min(40, dx))
            sy = max(-40, min(40, dy))
            self.cmd('mouse_move %d %d' % (sx, sy))
            time.sleep(0.02)
            dx -= sx
            dy -= sy
        self.x, self.y = x, y

    def button(self, b):
        self.cmd('mouse_button %d' % b)
        time.sleep(0.12)

    def stop(self):
        try:
            self.mon.sendall(b'quit\n')
        except OSError:
            pass
        try:
            self.proc.wait(5)
        except subprocess.TimeoutExpired:
            self.proc.kill()


def run(script, img, out, show):
    lines = [l.rstrip('\n') for l in open(script, encoding='utf-8-sig')]
    lines = [l for l in lines if l.strip() and not l.lstrip().startswith('#')]
    extra = None
    if lines and lines[0].startswith('qemu'):
        extra = lines.pop(0).split()[1:]
    m = Machine(img, out, extra, show)
    try:
        for line in lines:
            word, _, rest = line.strip().partition(' ')
            if word == 'waitlog':
                parts = rest.rsplit(' ', 1)
                if len(parts) == 2 and parts[1].isdigit():
                    m.waitlog(parts[0], int(parts[1]))
                else:
                    m.waitlog(rest, 30)
            elif word == 'wait':
                time.sleep(float(rest))
            elif word == 'type':
                m.text(rest)
                m.key('ret', 0.3)
            elif word == 'text':
                m.text(rest)
            elif word in ('enter', 'esc', 'tab', 'bksp'):
                m.key({'enter': 'ret', 'bksp': 'backspace'}.get(word, word), 0.2)
            elif word == 'key':
                m.key(rest, 0.2)
            elif word == 'snap':
                m.snap(rest)
            elif word == 'moveto':
                x, y = rest.split()
                m.moveto(int(x), int(y))
            elif word == 'click':
                m.button(1)
                m.button(0)
            elif word == 'rclick':
                m.button(4)
                m.button(0)
            elif word == 'drag':
                x, y = rest.split()
                m.button(1)
                m.moveto(int(x), int(y))
                m.button(0)
            else:
                print('  ?? unknown line: ' + line)
    finally:
        m.stop()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('script')
    ap.add_argument('--img', default=os.path.join(ROOT, 'disk.img'))
    ap.add_argument('--out', default=os.path.join(ROOT, 'test', 'qemu', 'out'))
    ap.add_argument('--show', action='store_true', help='open the QEMU window')
    a = ap.parse_args()
    run(a.script, a.img, a.out, a.show)


if __name__ == '__main__':
    main()
