#!/usr/bin/env python3
# test.py - is PyTon still Python? Every program in pyton/examples is run twice: by real Python and
# compiled by py2asm (as a Windows program); the two outputs must be the same.
#
#   python pyton/test.py [name ...]        all the examples, or only the named ones
#
# Needs nasm. The compiled programs are left in pyton/examples/out.

import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
EX = os.path.join(HERE, 'examples')
OUT = os.path.join(EX, 'out')


def find_nasm():
    p = shutil.which('nasm')
    if p:
        return p
    for d in (os.environ.get('NASM_DIR', ''), os.path.expandvars(r'%LOCALAPPDATA%\bin\NASM'),
              r'C:\msys64\mingw64\bin', r'C:\Program Files\NASM'):
        if d and os.path.exists(os.path.join(d, 'nasm.exe')):
            return os.path.join(d, 'nasm.exe')
    sys.exit('test: cannot find nasm')


def lines(text):
    return [l.rstrip() for l in text.replace('\r', '').split('\n')]


def main():
    os.makedirs(OUT, exist_ok=True)
    nasm = find_nasm()
    names = sys.argv[1:] or sorted(f[:-3] for f in os.listdir(EX) if f.endswith('.py'))
    failed = 0
    for name in names:
        src = os.path.join(EX, name + '.py')
        asm = os.path.join(OUT, name + '.asm')
        exe = os.path.join(OUT, name + '.exe')
        want = subprocess.run([sys.executable, src], capture_output=True, text=True, encoding='utf-8')
        r = subprocess.run([sys.executable, os.path.join(HERE, 'py2asm.py'), src, '-o', asm],
                           capture_output=True, text=True)
        if r.returncode != 0:
            print('%-12s NOT COMPILED  %s' % (name, (r.stderr or r.stdout).strip()))
            failed += 1
            continue
        r = subprocess.run([nasm, '-f', 'bin', '-I', HERE + os.sep, asm, '-o', exe], capture_output=True, text=True)
        if r.returncode != 0:
            print('%-12s NASM STOPPED\n%s' % (name, r.stderr[:1500]))
            failed += 1
            continue
        try:
            got = subprocess.run([exe], capture_output=True, timeout=30)
        except subprocess.TimeoutExpired:
            print('%-12s DOES NOT END' % name)
            failed += 1
            continue
        a, b = lines(want.stdout), lines(got.stdout.decode('utf-8', errors='replace'))
        if a == b and got.returncode == want.returncode:
            print('%-12s ok   (%d lines, %d bytes)' % (name, len(a) - 1, os.path.getsize(exe)))
            continue
        failed += 1
        print('%-12s DIFFERENT  (exit %d, Python %d)' % (name, got.returncode, want.returncode))
        shown = 0
        for i in range(max(len(a), len(b))):
            x = a[i] if i < len(a) else '<nothing>'
            y = b[i] if i < len(b) else '<nothing>'
            if x != y:
                print('   line %d\n     Python: %s\n     PyTon:  %s' % (i + 1, x[:200], y[:200]))
                shown += 1
                if shown == 6:
                    break
    print('%d of %d the same' % (len(names) - failed, len(names)))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
