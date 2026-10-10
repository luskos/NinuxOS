#!/usr/bin/env python3
# rename.py - give functions and data of the kernel the names they deserve.
#
#   python tools/kdis/rename.py            applies tools/kdis/renames.txt to the kernel and the suits
#   python tools/kdis/rename.py objects/Desktop.asmo.kasm tools/kdis/renames_desktop.txt
#                                          the same for one object written as source, with its own list
#
# renames.txt:  OLD NEW   ; what it does       (a line a name; # starts a comment line)
# The recovered kernel has addresses for names (fn_53fdf). When it is understood what a function
# does, a line goes into renames.txt and this puts the new name everywhere the old one stands:
# kernel/Kernel.kasm, kernel/Kernel.sym.inc, the kernel suits (kernel/suits/*.kasm) and
# tools/kdis/names.txt (so that reading the kernel again keeps it). What the line says after the
# ';' is written above the function as a comment.
# Nothing but names changes: the kernel and the suits are assembled before and after, and if a
# single byte differs everything is put back.

import glob
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import build_disk                                                   # noqa: E402

WORK = os.path.join(ROOT, 'build', 'work')
KERNEL = os.path.join(ROOT, 'kernel', 'Kernel.kasm')
FILES = [KERNEL, os.path.join(ROOT, 'kernel', 'Kernel.sym.inc'), os.path.join(HERE, 'names.txt')] \
    + sorted(glob.glob(os.path.join(ROOT, 'kernel', 'suits', '*.kasm')))


SOURCES = [KERNEL] + sorted(glob.glob(os.path.join(ROOT, 'kernel', 'suits', '*.kasm')))
LIST = os.path.join(HERE, 'renames.txt')


def assemble_all():
    out = []
    for src in SOURCES:
        o = os.path.join(WORK, 'rename.bin')
        r = subprocess.run([build_disk.find_nasm(), '-f', 'bin', '-w-all', '-I', os.path.dirname(src) + os.sep, '-o', o, src],
                           capture_output=True, text=True)
        if r.returncode != 0:
            return None, '%s\n%s' % (os.path.relpath(src, ROOT), r.stderr[:1500])
        out.append(open(o, 'rb').read())
    return out, ''


def main():
    global KERNEL, FILES, SOURCES, LIST
    if len(sys.argv) == 3:                      # one object and its own list
        KERNEL = os.path.abspath(sys.argv[1])
        FILES = SOURCES = [KERNEL]
        LIST = sys.argv[2]
    pairs = []
    for line in open(LIST, encoding='utf-8'):
        if line.strip() and not line.startswith('#'):
            names, _, what = line.partition(';')
            f = names.split()
            if len(f) == 2:
                pairs.append((f[0], f[1], what.strip()))
    texts = {p: open(p, encoding='utf-8').read() for p in FILES}
    todo = [(a, b, w) for a, b, w in pairs if re.search(r'\b%s\b' % re.escape(a), texts[KERNEL])]
    if not todo:
        print('rename: nothing to do (%d names are in place already)' % len(pairs))
        return 0
    for a, b, w in todo:
        if re.search(r'\b%s\b' % re.escape(b), texts[KERNEL]):
            sys.exit('rename: the name %s is already used' % b)
    before, err = assemble_all()
    if before is None:
        sys.exit('rename: does not assemble as it is: ' + err)
    for p in FILES:
        shutil.copyfile(p, p + '.keep')
        s = texts[p]
        for a, b, w in todo:
            if p == KERNEL and w:
                s = re.sub(r'(?m)^%s:' % re.escape(a), '; %s\n%s:' % (w, a), s, count=1)
            s = re.sub(r'\b%s\b' % re.escape(a), b, s)
        with open(p, 'w', encoding='utf-8', newline='\n') as f:
            f.write(s)
    after, err = assemble_all()
    same = after == before
    for p in FILES:
        if not same:
            shutil.copyfile(p + '.keep', p)
        os.remove(p + '.keep')
    if not same:
        sys.exit('rename: the bytes did not stay the same - everything was put back\n' + err)
    print('rename: %d names given; %d file(s) assembled to the same bytes' % (len(todo), len(before)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
