#!/usr/bin/env python3
# outline.py - what a recovered source is made of: a line a function.
#
#   python tools/kdis/outline.py objects/Desktop.asmo.kasm
#
# For every function: how many instructions, which functions of the system it calls (the places
# of the table a program is handed: [r15+0x18] is fill ...), which of its own functions it calls,
# and the texts it points at. This is the first thing to read before an object is written anew
# as source meant to be read (TODO.md, the order of work, 22).

import re
import sys

API = {0x00: 'print', 0x08: 'put_letter', 0x10: 'screen_size', 0x18: 'fill', 0x30: 'text', 0x38: 'window',
       0x40: 'poll', 0x48: 'cursor_show', 0x50: 'cursor_hide', 0x58: 'ob_count', 0x60: 'ob_by_number',
       0x68: 'ob_by_name', 0x70: 'ob_meta', 0x80: 'ob_call', 0x90: 'random', 0xA0: 'ticks', 0xB0: 'memory',
       0xC0: 'log', 0xE0: 'ob_save', 0x118: 'programs', 0x128: 'system_text', 0x138: 'sound',
       0x140: 'fill_round', 0x150: 'network'}


def main():
    lines = open(sys.argv[1], encoding='utf-8').read().split('\n')
    texts = {}
    for i, line in enumerate(lines[:-1]):
        m = re.match(r'^(\w+):', line)
        t = re.match(r"^\s+db '([^']{3,})'", lines[i + 1])
        if m and t:
            texts[m.group(1)] = t.group(1)
    starts = [i for i, line in enumerate(lines) if re.match(r'^(fn_|sock_|entry_)\w+:', line)]
    for n, i in enumerate(starts):
        end = starts[n + 1] if n + 1 < len(starts) else len(lines)
        body = []
        for line in lines[i + 1:end]:
            if re.match(r'^(d_|p_|r_)\w+:', line):
                break
            body.append(line)
        text = ' '.join(body)
        count = sum(1 for b in body if b.startswith('        ') and not b.strip().startswith(('db', 'dq', ';', 'times')))
        api = sorted(set(int(a, 16) for a in re.findall(r'\[r1[45]\+0x([0-9a-f]+)\]', text)))
        calls = sorted(set(re.findall(r'call (fn_\w+)', text)))
        says = []
        for name in re.findall(r'\[rel (\w+)\]', text):
            if name in texts and texts[name] not in says:
                says.append(texts[name])
        print('%-10s %4d | %s | %s | %s' % (
            lines[i].split(':')[0], count,
            ' '.join(API.get(a, '+%X' % a) for a in api),
            ' '.join(c[3:] for c in calls),
            ' / '.join(s[:30] for s in says[:8])))
    return 0


if __name__ == '__main__':
    sys.exit(main())
