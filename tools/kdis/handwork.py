#!/usr/bin/env python3
# handwork.py - after kdis.py has read the kernel again: put back what was written by hand.
#
#   python tools/kdis/kdis.py                        reads the compiled kernel -> kernel/Kernel.kasm
#   python tools/kdis/handwork.py OLD.kasm           OLD.kasm: the source as it was before that
#
# kdis.py makes kernel/Kernel.kasm from the compiled kernel of v2.9.59, so everything written
# into the kernel since then is not in what it writes. This takes from the old source and puts
# into the new one:
#   1. every place where old code was changed:   %ifdef PLAIN_KERNEL / the old lines / %else /
#      the new lines / %endif - found again in the new source by the line above it and the old lines
#   2. the labels written by hand in the middle of old code (mux_begin_rest)
#   3. the block of new code at the end of the extension, in front of ext_end
#   4. the addresses of the kernel that instructions use as numbers get their names
#      ([rcx*8+0x5b920] -> [rcx*8+d_5b920]); kdis does not do that yet
# then says.py writes its comments, and the result is assembled: it must be the very bytes the
# old source gives. If not, nothing is kept.

import bisect
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
sys.path.insert(0, HERE)
import build_disk                                                   # noqa: E402
import says                                                         # noqa: E402

SRC = os.path.join(ROOT, 'kernel', 'Kernel.kasm')
WORK = os.path.join(ROOT, 'build', 'work')
HAND_LABELS = ['mux_begin_rest']
CORE = (0x7E00, 0x17010)
EXT = (0x50000, 0x76950)


def assemble(path, out, extra=()):
    r = subprocess.run([build_disk.find_nasm(), '-f', 'bin', '-w-all', '-I', os.path.join(ROOT, 'kernel') + os.sep]
                       + list(extra) + ['-o', out, path], capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit('handwork: nasm stopped on %s\n%s' % (path, r.stderr[:3000]))
    return open(out, 'rb').read()


def plain(lines):
    return [x for x in lines if not x.startswith(says.MARK)]


def name_numbers(lines):
    """instructions that use an address of the kernel as a number get its name"""
    probe = os.path.join(WORK, 'Kernel.hand.kasm')
    with open(probe, 'w', encoding='utf-8', newline='\n') as f:
        f.write('[map symbols %s]\n' % os.path.join(WORK, 'Kernel.hand.map').replace('\\', '/') + '\n'.join(lines))
    shutil.copyfile(probe, os.path.join(ROOT, 'kernel', 'Kernel.hand.kasm'))
    try:
        assemble(os.path.join(ROOT, 'kernel', 'Kernel.hand.kasm'), os.path.join(WORK, 'Kernel.hand.bin'))
    finally:
        os.remove(os.path.join(ROOT, 'kernel', 'Kernel.hand.kasm'))
    at = {}
    for line in open(os.path.join(WORK, 'Kernel.hand.map')):
        p = line.split()
        if len(p) == 3 and re.fullmatch('[0-9A-F]+', p[0]) and re.fullmatch('[0-9A-F]+', p[1]):
            at.setdefault(int(p[1], 16), p[2])
    addrs = sorted(at)
    done = 0
    for i, line in enumerate(lines):
        t = line.strip()
        if not line.startswith((' ', '\t')) or t.startswith((';', '%', 'times', 'db ', 'dq ', 'dd ', 'dw ')) or 'core_start' in line:
            continue

        def fix(m):
            nonlocal done
            inner = m.group(1)
            k = re.search(r'0x([0-9a-fA-F]{4,5})\b', inner)
            v = int(k.group(1), 16)
            if not (CORE[0] <= v < CORE[1] or EXT[0] <= v < EXT[1]):
                return m.group(0)
            if v in at:
                name = at[v]
            elif '*' in inner or inner.count('+') > 1:
                b = addrs[bisect.bisect_right(addrs, v) - 1]
                name = '%s+0x%x' % (at[b], v - b)
            else:
                return m.group(0)
            done += 1
            return '[' + inner.replace(k.group(0), name) + ']'
        new = re.sub(r'\[([^\]]*\+0x[0-9a-fA-F]{4,5})\]', fix, line)
        if new != line:
            lines[i] = new + '            ; (an address of the kernel, by its name)'
        elif t == 'cmp rdi,0x154b8':
            lines[i] = line.replace('0x154b8', 'd_154b8')
            done += 1
    return done


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    old = plain(open(sys.argv[1], encoding='utf-8').read().split('\n'))
    new = plain(open(SRC, encoding='utf-8').read().split('\n'))
    text = '\n'.join(new)

    # 1. the places where old code was changed
    changed = 0
    i = 0
    while i < len(old):
        if old[i].strip() == '%ifdef PLAIN_KERNEL':
            e = old.index('%else', i)
            end = old.index('%endif', e)
            above, was = old[i - 1], old[i + 1:e]
            key = '\n'.join([above] + was) + '\n'
            if text.count(key) != 1:
                sys.exit('handwork: the old lines of a changed place are %d times in the new source:\n%s' % (text.count(key), key))
            text = text.replace(key, '\n'.join([above] + old[i:end + 1]) + '\n')
            changed += 1
            i = end
        i += 1
    # 2. labels written by hand
    for label in HAND_LABELS:
        k = old.index(label + ':' + old[[x.split(':')[0] for x in old].index(label)].split(':', 1)[1])
        key = old[k - 1] + '\n' + old[k + 1] + '\n'
        if text.count(key) != 1:
            sys.exit('handwork: the place of the label %s is %d times in the new source' % (label, text.count(key)))
        text = text.replace(key, old[k - 1] + '\n' + old[k] + '\n' + old[k + 1] + '\n')
    # 3. the new code at the end of the extension
    a = old.index('%ifndef PLAIN_KERNEL')
    b = old.index('ext_end:')
    block = '\n'.join(old[a:b]) + '\n'
    if text.count('\next_end:\n') != 1:
        sys.exit('handwork: ext_end is not once in the new source')
    text = text.replace('\next_end:\n', '\n' + block + 'ext_end:\n')
    lines = text.split('\n')
    # 4. numbers that are addresses
    named = name_numbers(lines)

    keep = SRC + '.kdis'
    shutil.copyfile(SRC, keep)
    with open(SRC, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(lines))
    says.annotate(SRC)
    shutil.copyfile(sys.argv[1], os.path.join(ROOT, 'kernel', 'Kernel.old.kasm'))
    try:
        want = assemble(os.path.join(ROOT, 'kernel', 'Kernel.old.kasm'), os.path.join(WORK, 'Kernel.old.bin'))
        want_plain = assemble(os.path.join(ROOT, 'kernel', 'Kernel.old.kasm'), os.path.join(WORK, 'Kernel.old.bin'), ['-DPLAIN_KERNEL'])
    finally:
        os.remove(os.path.join(ROOT, 'kernel', 'Kernel.old.kasm'))
    got = assemble(SRC, os.path.join(WORK, 'Kernel.new.bin'))
    got_plain = assemble(SRC, os.path.join(WORK, 'Kernel.new.bin'), ['-DPLAIN_KERNEL'])
    if got != want or got_plain != want_plain:
        shutil.copyfile(SRC, os.path.join(WORK, 'Kernel.tried.kasm'))
        shutil.copyfile(keep, SRC)
        os.remove(keep)
        sys.exit('handwork: the kernel did not come out as from the old source (%d and %d bytes) - not kept'
                 % (len(got), len(want)))
    os.remove(keep)
    print('handwork: %d changed places, %d labels, the new code at the end, %d numbers named;' % (changed, len(HAND_LABELS), named))
    print('handwork: the kernel is the same %d bytes as from the old source (and the same without the new code)' % len(got))
    return 0


if __name__ == '__main__':
    sys.exit(main())
