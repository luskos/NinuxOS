#!/usr/bin/env python3
# says.py - above every function of the kernel and of the suits: the texts it points at.
#
#   python tools/kdis/says.py            kernel/Kernel.kasm and kernel/suits/*.kasm
#
# The sources recovered from the compiled kernel have addresses for names (fn_0a059). Until each
# function has a name of its own, the texts it prints say what it is for. This writes them as
# comment lines above the function:
#       ; says: 'Built-in keyboard: it answered (the old kind, PS/2).'
# Only comments are added: the files assemble to the same bytes (the build shows it - nothing
# is listed as changed). It may be run again: lines it wrote before are replaced.

import glob
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
MARK = '; says: '
START = re.compile(r'^(fn_\w+|cmd_\w+|api_\w+|entry_\w+):')
LABEL = re.compile(r'^(\w+):')
POINTS = re.compile(r'\[rel (d_\w+|p_\w+)\]')
TEXT = re.compile(r"^\s+db '((?:[^']){4,})'")


def texts(lines):
    """the label of a text -> its first line"""
    out = {}
    for i, line in enumerate(lines):
        m = LABEL.match(line)
        if m and i + 1 < len(lines):
            t = TEXT.match(lines[i + 1])
            if t:
                out[m.group(1)] = t.group(1)
    return out


def annotate(path):
    lines = [x for x in open(path, encoding='utf-8').read().split('\n') if not x.startswith(MARK)]
    known = texts(lines)
    starts = [i for i, line in enumerate(lines) if START.match(line)]
    notes = {}
    for n, i in enumerate(starts):
        end = starts[n + 1] if n + 1 < len(starts) else len(lines)
        said = []
        for line in lines[i:end]:
            if LABEL.match(line) and line.startswith(('d_', 'p_')):
                break                           # the function's own data begin: its code is over
            for name in POINTS.findall(line):
                t = known.get(name)
                if t and t not in said:
                    said.append(t)
        if said:
            notes[i] = [MARK + "'" + t[:90] + "'" for t in said[:3]]
            if len(said) > 3:
                notes[i].append(MARK + '... and %d more texts' % (len(said) - 3))
    out = []
    for i, line in enumerate(lines):
        out.extend(notes.get(i, []))
        out.append(line)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(out))
    return len(starts), len(notes)


def main():
    for path in [os.path.join(ROOT, 'kernel', 'Kernel.kasm')] + sorted(glob.glob(os.path.join(ROOT, 'kernel', 'suits', '*.kasm'))):
        functions, noted = annotate(path)
        print('says: %s: %d functions, %d of them point at texts' % (os.path.relpath(path, ROOT), functions, noted))


if __name__ == '__main__':
    main()
