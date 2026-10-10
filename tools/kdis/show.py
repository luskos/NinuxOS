#!/usr/bin/env python3
# show.py - read a function of a recovered source, or how a system function is called.
#
#   python tools/kdis/show.py kernel/Kernel.kasm mux_turn [LINES]     the function, compactly
#   python tools/kdis/show.py objects/Desktop.asmo.kasm +28 [N]        the 12 lines before each of the
#                                                                      first N calls of [r15+0x28]
import re
import sys


def main():
    lines = open(sys.argv[1], encoding='utf-8').read().split('\n')
    what = sys.argv[2]
    n = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    if what.startswith('+'):
        pat = re.compile(r'\[r1[45]\+0x%x\]' % int(what[1:], 16))
        shown = 0
        for i, line in enumerate(lines):
            if pat.search(line):
                print('-- line %d' % (i + 1))
                print('   ' + ' | '.join(x.strip() for x in lines[max(0, i - 12):i + 1] if x.strip()))
                shown += 1
                if shown >= (n or 3):
                    break
        return 0
    for i, line in enumerate(lines):
        if line.startswith(what + ':'):
            out = []
            for x in lines[i + 1:]:
                t = x.strip()
                if re.match(r'^(fn_|api_|cmd_|sock_)\w+:', x) or len(out) >= (n or 60):
                    break
                if t and not t.startswith(';'):
                    out.append(t)
            print(' | '.join(out))
            return 0
    sys.exit('show: no %s in %s' % (what, sys.argv[1]))


if __name__ == '__main__':
    sys.exit(main())
