#!/usr/bin/env python3
# numbers.py - which numbers in kernel/Kernel.kasm are still addresses of the kernel itself.
#
#   python tools/kdis/numbers.py            count them and show some
#
# The source recovered from the compiled kernel assembles to the same bytes, but it cannot be
# moved yet: with one `nop` put in, the system stops (tried in QEMU, v3.0.17). The reason is
# addresses that are still written as numbers - `cmp rdi,0x154b8` where 0x154B8 is d_154b8.
# This lists every number in an instruction that lies inside the kernel (the core 0x7E00..,
# the extension 0x50000..), and says whether a name stands at exactly that address.
# It needs build/work/Kernel.map (the build makes it).

import collections
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
CORE = (0x7E00, 0x17010)
EXT = (0x50000, 0x76950)


def inside(v):
    return CORE[0] <= v < CORE[1] or EXT[0] <= v < EXT[1]


def names():
    out = {}
    for line in open(os.path.join(ROOT, 'build', 'work', 'Kernel.map')):
        p = line.split()
        if len(p) == 3 and re.fullmatch('[0-9A-F]+', p[0]) and re.fullmatch('[0-9A-F]+', p[1]):
            out.setdefault(int(p[1], 16), p[2])
    return out


def main():
    at = names()
    src = open(os.path.join(ROOT, 'kernel', 'Kernel.kasm'), encoding='utf-8').read().split('\n')
    found = collections.defaultdict(list)
    for i, line in enumerate(src):
        t = line.strip()
        if not line.startswith((' ', '\t')) or t.startswith((';', '%', 'times', 'db ')):
            continue
        kind = 'data' if t.startswith(('dq ', 'dd ', 'dw ')) else 'code'
        for m in re.finditer(r'(?<![\w.])0x([0-9a-fA-F]{4,5})\b', t.split(';')[0]):
            v = int(m.group(1), 16)
            if inside(v):
                found[(kind, 'a name is there' if v in at else 'no name there')].append((i + 1, t, at.get(v, '')))
    for key in sorted(found):
        rows = found[key]
        print('== %s, %s: %d' % (key[0], key[1], len(rows)))
        step = max(1, len(rows) // 25)
        for n, t, name in rows[::step][:25]:
            print('   %6d  %-46s %s' % (n, t, name))
    return 0


if __name__ == '__main__':
    sys.exit(main())
