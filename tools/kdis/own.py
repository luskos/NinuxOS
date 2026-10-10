#!/usr/bin/env python3
# own.py - what in the kernel belongs to one thing only (NinuxOS v3.0.37).
#
#   python tools/kdis/own.py fn_73d22 [fn_6dcff ...]        one entry or several, in the kernel
#   python tools/kdis/own.py --suit kernel/suits/Tools.kasm entry_05 ...     in a kernel suit
#
# Photon, Puffer, Tuner and META are not programs: each is a function of the kernel's extension
# that the desktop asks for. To take one out of the kernel (TODO.md, the order of work, 20) it
# must be known what is *its own* - the functions and data nothing else in the kernel uses - and
# what it shares with the rest (drawing, memory, the disk ...), which it would have to reach as
# a program reaches the system.
# For each entry this prints: how much it reaches in all, how much of that is its own (code
# and data, in bytes), and the functions of the kernel it calls that are not its own.
# It reads kernel/Kernel.kasm, kernel/New.kasm and build/work/Kernel.map (the build makes it).

import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
LABEL = re.compile(r'^([A-Za-z_]\w*):')
NAME = re.compile(r'\b([A-Za-z_]\w*)\b')


def load(suit=None):
    lines = []
    addr = {}
    if suit:                                    # a kernel suit: its labels carry their addresses in their names
        lines = open(suit, encoding='utf-8').read().split('\n')
        last = None
        for line in reversed(lines):
            m = LABEL.match(line)
            if m:
                h = re.search(r'_([0-9a-f]{5})$', m.group(1))
                if h:
                    last = int(h.group(1), 16)
                    addr[m.group(1)] = last
                elif last is not None:
                    addr[m.group(1)] = last     # entry_NN, suit_start: where the next label is
    else:
        for f in ('Kernel.kasm', 'New.kasm'):
            lines += open(os.path.join(ROOT, 'kernel', f), encoding='utf-8').read().split('\n')
        for line in open(os.path.join(ROOT, 'build', 'work', 'Kernel.map')):
            p = line.split()
            if len(p) == 3 and re.fullmatch('[0-9A-F]+', p[0]) and re.fullmatch('[0-9A-F]+', p[1]):
                addr[p[2]] = int(p[1], 16)
    # blocks: from a label that starts a function or a piece of data to the next such label
    starts = []
    for i, line in enumerate(lines):
        m = LABEL.match(line)
        if m and not m.group(1).startswith('L_') and m.group(1) in addr:
            starts.append((i, m.group(1)))
    blocks = {}
    order = []
    for k, (i, name) in enumerate(starts):
        end = starts[k + 1][0] if k + 1 < len(starts) else len(lines)
        body = lines[i + 1:end]
        code = any(b.startswith('        ') and not b.strip().startswith(('db ', 'dq ', 'dd ', 'dw ', 'times', ';', '%'))
                   for b in body)
        uses = set()
        for b in body:
            t = b.split(';')[0]
            for w in NAME.findall(t):
                if w in addr and w != name and w not in ('suit_start', 'core_start', 'ext_start'):
                    uses.add(w)
        blocks[name] = (code, uses)
        order.append(name)
    # L_ labels belong to the block they lie in: a use of an L_ label is a use of that block
    inside = {}
    cur = None
    for line in lines:
        m = LABEL.match(line)
        if m:
            if m.group(1) in blocks:
                cur = m.group(1)
            elif cur:
                inside[m.group(1)] = cur
    for name in blocks:
        code, uses = blocks[name]
        blocks[name] = (code, set(inside.get(u, u) for u in uses) - {name})
    size = {}
    by_addr = sorted(blocks, key=lambda n: addr[n])
    for k, name in enumerate(by_addr):
        nxt = addr[by_addr[k + 1]] if k + 1 < len(by_addr) else addr[name]
        size[name] = nxt - addr[name] if 0 <= nxt - addr[name] < 0x40000 else 0
    return blocks, size, addr


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    suit = None
    args = sys.argv[1:]
    if args[0] == '--suit':                     # own.py --suit kernel/suits/Tools.kasm entry_05 ...
        suit = args[1]
        args = args[2:]
    blocks, size, addr = load(suit)
    takes = {}
    if suit:                                    # what a suit takes from the kernel: the names of Kernel.sym.inc
        kernel = set()
        for line in open(os.path.join(ROOT, 'kernel', 'Kernel.sym.inc')):
            if ' equ ' in line:
                kernel.add(line.split()[0])
        cur = None
        for line in open(suit, encoding='utf-8').read().split('\n'):
            m = LABEL.match(line)
            if m and m.group(1) in blocks:
                cur = m.group(1)
            elif cur:
                for w in NAME.findall(line.split(';')[0]):
                    if w in kernel:
                        takes.setdefault(cur, set()).add(w)
    used_by = {}
    for name, (code, uses) in blocks.items():
        for u in uses:
            used_by.setdefault(u, set()).add(name)
    for entry in args:
        if entry not in blocks:
            print('%s: not a function or data of the kernel' % entry)
            continue
        reach = set()
        todo = [entry]
        while todo:
            n = todo.pop()
            if n in reach or n not in blocks:
                continue
            reach.add(n)
            todo.extend(blocks[n][1])
        own = set(reach)
        changed = True
        while changed:                          # what something outside also uses is not its own
            changed = False
            for n in list(own):
                if n != entry and not used_by.get(n, set()) <= own:
                    own.discard(n)
                    changed = True
        code = sum(size[n] for n in own if blocks[n][0])
        data = sum(size[n] for n in own if not blocks[n][0])
        shared = sorted(set(u for n in own for u in blocks[n][1]) - own)
        shared_code = [u for u in shared if u in blocks and blocks[u][0]]
        shared_data = [u for u in shared if u in blocks and not blocks[u][0]]
        print('%s (at 0x%X)' % (entry, addr[entry]))
        print('   reaches %d functions and pieces of data in all' % len(reach))
        print('   its own: %d functions, %d bytes of code; %d pieces of data, %d bytes'
              % (sum(1 for n in own if blocks[n][0]), code, sum(1 for n in own if not blocks[n][0]), data))
        print('   of the rest of the kernel it calls %d functions and uses %d pieces of data' % (len(shared_code), len(shared_data)))
        print('      functions: ' + ' '.join(shared_code[:40]) + (' ...' if len(shared_code) > 40 else ''))
        print('      data: ' + ' '.join(shared_data[:30]) + (' ...' if len(shared_data) > 30 else ''))
        if suit:
            k = sorted(set(w for n in own for w in takes.get(n, ())))
            fns = [w for w in k if not w.startswith(('d_', 'v_', 'L_'))]
            print('   of the kernel itself it uses %d names, %d of them functions: %s'
                  % (len(k), len(fns), ' '.join(fns[:45]) + (' ...' if len(fns) > 45 else '')))
    return 0


if __name__ == '__main__':
    sys.exit(main())
