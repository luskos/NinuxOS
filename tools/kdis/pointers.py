#!/usr/bin/env python3
# pointers.py - addresses of the kernel that lie in its data as plain bytes, given names.
#
#   python tools/kdis/pointers.py ADDRESS [ADDRESS ...]     hex, where the 8 bytes of a pointer lie
#   python tools/kdis/pointers.py --find                    what looks like one (to be judged by eye)
#
# kernel/Kernel.kasm assembles to the same bytes as the compiled kernel, but it can be moved
# only if every address in it is a name. Some pointers to code sat inside rows of `db` (the
# multiplexer's table of the system functions it takes over, for one). For each ADDRESS this
# cuts the row of bytes there into bytes, `dq NAME`, bytes - and puts the name (h_ADDR) in front
# of the instruction the pointer points at, if no name stands there yet.
# The kernel must come out the same, byte for byte: the tool checks it and puts the file back
# if it does not.

import os
import re
import shutil
import struct
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import build_disk                                                   # noqa: E402

SRC = os.path.join(ROOT, 'kernel', 'Kernel.kasm')
WORK = os.path.join(ROOT, 'build', 'work')
BASES = {'.core': 0x7E00, '.ext': 0x50000}


def assemble(listing=None):
    out = os.path.join(WORK, 'Kernel.ptr.bin')
    cmd = [build_disk.find_nasm(), '-f', 'bin', '-w-all', '-I', os.path.dirname(SRC) + os.sep, '-o', out, SRC]
    if listing:
        cmd += ['-l', listing]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr[:1500])
        return None
    return open(out, 'rb').read()


def addresses():
    """the number of a line of the source -> the address its first byte has (lines that give bytes)"""
    listing = os.path.join(WORK, 'Kernel.lst')
    assemble(listing)
    src = open(SRC, encoding='utf-8').read().split('\n')
    base = BASES['.core']
    where = {}
    for line in open(listing, encoding='utf-8', errors='replace'):
        m = re.match(r'\s*(\d+) ([0-9A-F]{8}) [0-9A-F\[\]\(\)]', line)
        if m:
            n = int(m.group(1))
            for k in range(n - 1, -1, -1):          # which section this line is in
                s = re.match(r'section (\.\w+)', src[k] if k < len(src) else '')
                if s:
                    base = BASES[s.group(1)]
                    break
            where.setdefault(n, base + int(m.group(2), 16))
    return where


def find(image):
    core = image.find(b'NXEXT1')
    out = []
    off = 0
    while off < len(image) - 8:
        v = struct.unpack_from('<Q', image, off)[0]
        if 0x50010 <= v < 0x50000 + len(image) - core and v & 0xFFF not in (0, 0x800, 0x005, 0x805, 0xA05):
            out.append((0x7E00 + off if off < core else 0x50000 + off - core, v))
            off += 8
        else:
            off += 1
    return out


def main():
    before = assemble()
    if before is None:
        sys.exit('pointers: kernel/Kernel.kasm does not assemble')
    if sys.argv[1:] == ['--find']:
        for at, v in find(before):
            print('0x%X: 0x%X' % (at, v))
        return 0
    wanted = sorted(int(a, 16) for a in sys.argv[1:])
    if not wanted:
        sys.exit(__doc__)
    core = before.find(b'NXEXT1')

    def byte_at(addr):
        return before[addr - 0x7E00] if addr < 0x50000 else before[core + addr - 0x50000]

    where = addresses()
    lines = sorted(where)                               # line numbers that give bytes, in order
    start = {where[n]: n for n in reversed(lines)}      # an address -> the first line that starts there
    src = open(SRC, encoding='utf-8').read().split('\n')
    labels = {}                                         # line number -> a label to put in front of it
    cuts = {}                                           # line number -> [(address, target)]
    for at in wanted:
        target = struct.unpack('<Q', bytes(byte_at(at + k) for k in range(8)))[0]
        row = max(n for n in lines if where[n] <= at)
        if not src[row - 1].strip().startswith('db '):
            sys.exit('pointers: 0x%X is not in a row of bytes: %s' % (at, src[row - 1].strip()))
        cuts.setdefault(row, []).append((at, 8, target))
        if target not in start:                         # it points into a row of bytes (code not read
            trow = max(n for n in lines if where[n] <= target)      # as code yet): the row is cut there
            if not src[trow - 1].strip().startswith('db '):
                sys.exit('pointers: 0x%X holds 0x%X, which is inside an instruction - not a pointer' % (at, target))
            labels[target] = 'h_%05x' % target
            if (target, 0, target) not in cuts.setdefault(trow, []):
                cuts[trow].append((target, 0, target))
            continue
        t = start[target]
        k = t - 2
        named = None
        while k >= 0 and re.match(r'^\w+:', src[k]):    # the names that stand right above
            named = src[k].split(':')[0]
            k -= 1
        labels[target] = named or 'h_%05x' % target
        if not named:
            labels[('new', t)] = 'h_%05x' % target
    out = []
    eaten = set()                                       # rows whose bytes went into the row before
    for i, line in enumerate(src):
        n = i + 1
        if n in eaten:
            continue
        if ('new', n) in labels:
            out.append(labels[('new', n)] + ':                               ; (a table points here: pointers.py)')
        if n in cuts:
            k = lines.index(n) + 1
            a, end = where[n], where[lines[k]]
            while max(at + size for at, size, target in cuts[n]) > end:     # a pointer runs into the next row
                if lines[k] != lines[k - 1] + 1 or not src[lines[k] - 1].strip().startswith('db ') or lines[k] in cuts:
                    sys.exit('pointers: the pointer at line %d runs into something that is not a plain row of bytes' % n)
                eaten.add(lines[k])
                k += 1
                end = where[lines[k]]
            for at, size, target in sorted(cuts[n]):
                if at > a:
                    out.append('        db ' + ', '.join('0x%02X' % byte_at(x) for x in range(a, at)))
                if size:
                    out.append('        dq ' + labels[target])
                else:
                    out.append(labels[target] + ':                               ; (a table points here: pointers.py)')
                a = at + size
            if end > a:
                out.append('        db ' + ', '.join('0x%02X' % byte_at(x) for x in range(a, end)))
            continue
        out.append(line)
    shutil.copyfile(SRC, SRC + '.keep')
    with open(SRC, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(out))
    after = assemble()
    if after != before:
        if after:
            d = [i for i in range(min(len(after), len(before))) if after[i] != before[i]]
            print('pointers: %d and %d bytes; they differ first at byte 0x%X' % (len(before), len(after), d[0] if d else -1))
        shutil.copyfile(SRC, os.path.join(WORK, 'Kernel.tried.kasm'))
        shutil.copyfile(SRC + '.keep', SRC)
        os.remove(SRC + '.keep')
        sys.exit('pointers: the kernel did not come out the same - the file was put back')
    os.remove(SRC + '.keep')
    print('pointers: %d pointers named; the kernel is the same %d bytes' % (len(wanted), len(after)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
