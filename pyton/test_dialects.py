#!/usr/bin/env python3
# test_dialects.py - the same program written in C, C++, C#, Java and JavaScript must do what
# the Python one does (pyton/examples/dialects/same.*).
#
#   python pyton/test_dialects.py
#
# Each is turned into PyTon by clike.py, compiled by py2asm for Windows, assembled, run; what it
# prints is compared with what Python prints for same.py. Also: a line that is not allowed in a
# dialect (a class with things of its own) must be refused.

import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
EX = os.path.join(HERE, 'examples', 'dialects')
OUT = os.path.join(EX, 'out')
sys.path.insert(0, HERE)
import clike                                                        # noqa: E402
import test as pytest_                                              # noqa: E402  (find_nasm)


def main():
    os.makedirs(OUT, exist_ok=True)
    nasm = pytest_.find_nasm()
    want = subprocess.run([sys.executable, os.path.join(EX, 'same.py')], capture_output=True, text=True).stdout.split('\n')
    failed = 0
    for name in ('same.c', 'same.cpp', 'same.cs', 'Same.java', 'same.js'):
        d = clike.DIALECTS[name.rsplit('.', 1)[1]]
        base = os.path.join(OUT, name.replace('.', '_'))
        try:
            py = clike.translate(open(os.path.join(EX, name), encoding='utf-8').read(), d, name)
        except clike.DialectError as e:
            print('%-10s NOT READ  %s' % (name, e))
            failed += 1
            continue
        open(base + '.py', 'w', encoding='utf-8', newline='\n').write(py)
        r = subprocess.run([sys.executable, os.path.join(HERE, 'py2asm.py'), base + '.py', '-o', base + '.asm'],
                           capture_output=True, text=True)
        if r.returncode != 0:
            print('%-10s NOT COMPILED  %s' % (name, (r.stderr or r.stdout).strip()[:300]))
            failed += 1
            continue
        r = subprocess.run([nasm, '-f', 'bin', '-I', HERE + os.sep, base + '.asm', '-o', base + '.exe'], capture_output=True, text=True)
        if r.returncode != 0:
            print('%-10s NASM STOPPED  %s' % (name, r.stderr[:300]))
            failed += 1
            continue
        got = subprocess.run([base + '.exe'], capture_output=True, timeout=30).stdout.decode('utf-8', 'replace').replace('\r', '').split('\n')
        if got == want:
            print('%-10s ok   (%d lines the same as Python)' % (name, len(want) - 1))
        else:
            failed += 1
            print('%-10s DIFFERENT' % name)
            for i in range(max(len(got), len(want))):
                a = want[i] if i < len(want) else '<nothing>'
                b = got[i] if i < len(got) else '<nothing>'
                if a != b:
                    print('     Python: %s\n     %-6s: %s' % (a, d, b))
    for text, d in (('class A { int x; void f() { this.x = 1; } }', 'java'), ('struct P { int x; };', 'c'),
                    ('class A extends B { }', 'js')):
        try:
            clike.translate(text, d)
            print('NOT REFUSED (%s): %s' % (d, text))
            failed += 1
        except clike.DialectError as e:
            print('refused, as it should be (%s): %s' % (d, str(e).split(': ', 2)[-1][:70]))
    print('%d of 5 the same' % (5 - min(failed, 5)) if not failed else '%d problem(s)' % failed)
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
