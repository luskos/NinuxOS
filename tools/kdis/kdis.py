#!/usr/bin/env python3
# kdis.py - turn the compiled NinuxOS kernel back into NASM source (kernel/Kernel.kasm)
# that assembles to exactly the same bytes.
#
#   python tools/kdis/kdis.py
#
# reads   build/objects/Kernel.kasm      the compiled kernel: core + extension (220000 bytes)
#         tools/kdis/trace_addrs.txt     addresses QEMU saw running (one hex address a line)
#         tools/kdis/seeds.txt           optional: more code starts,  "ADDR BITS"
#         tools/kdis/names.txt           optional: names for addresses, "ADDR NAME"
# writes  kernel/Kernel.kasm             the source
#         tools/kdis/work/report.txt     what was found, what stayed as bytes
#
# How: code is followed from known starts (the entry, every call and jump target, the traced
# addresses), ndisasm decodes each instruction, targets become labels. The result is assembled
# with nasm and compared with the original; an instruction nasm encodes differently is written
# as its bytes (db) with the instruction in a comment, so the output is always byte-exact.

import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
KERNEL = os.path.join(ROOT, 'build', 'objects', 'Kernel.kasm')
OUT = os.path.join(ROOT, 'kernel', 'Kernel.kasm')
WORK = os.path.join(HERE, 'work')

CORE_VMA = 0x7E00                       # the boot sector reads the kernel here
CORE_SIZE = 61968
EXT_VMA = 0x50000                       # the core copies the extension here

# far jumps that change the processor mode: where from -> (where to, bits)
FAR = {0x7E56: (0x8360, 32), 0x8404: (0x840B, 64)}
ENTRIES = [(0x7E00, 16), (0x8360, 32), (0x840B, 64), (0x8423, 64)]


def find_tool(name):
    p = shutil.which(name)
    if p:
        return p
    for d in (os.environ.get('NASM_DIR', ''),
              os.path.expandvars(r'%LOCALAPPDATA%\bin\NASM'),
              r'C:\msys64\mingw64\bin', r'C:\msys64\ucrt64\bin', r'C:\Program Files\NASM'):
        if d and os.path.exists(os.path.join(d, name + '.exe')):
            return os.path.join(d, name + '.exe')
    sys.exit('cannot find ' + name)


NASM = find_tool('nasm')
NDISASM = find_tool('ndisasm')


class Section:
    def __init__(self, name, vma, off, size):
        self.name, self.vma, self.off, self.size = name, vma, off, size
        self.end = vma + size
        self.file = os.path.join(WORK, name + '.bin')


image = open(KERNEL, 'rb').read()
SECTIONS = [Section('core', CORE_VMA, 0, CORE_SIZE),
            Section('ext', EXT_VMA, CORE_SIZE, len(image) - CORE_SIZE)]


def section_of(vma):
    for s in SECTIONS:
        if s.vma <= vma < s.end:
            return s
    return None


def offset(vma):
    s = section_of(vma)
    return s.off + (vma - s.vma)


def default_bits(vma):
    if vma < 0x8360:
        return 16
    if vma < 0x840B:
        return 32
    return 64


# ---------------------------------------------------------------- decoding (ndisasm)

LINE = re.compile(r'^([0-9A-F]{8,})\s+([0-9A-F]+)\s+(.+)$')
CONT = re.compile(r'^\s+-([0-9A-F]+)\s*$')


class Decoder:
    def __init__(self):
        self.cache = {16: {}, 32: {}, 64: {}}
        self.spawns = 0

    def run(self, vma, bits, limit):
        sec = section_of(vma)
        cache = self.cache[bits]
        self.spawns += 1
        p = subprocess.Popen([NDISASM, '-b', str(bits), '-o', hex(vma), '-e', str(vma - sec.vma), sec.file],
                             stdout=subprocess.PIPE, text=True)
        cur = None
        count = 0
        for line in p.stdout:
            m = CONT.match(line)
            if m and cur:
                cur[1] += m.group(1)
                continue
            m = LINE.match(line)
            if not m:
                continue
            if cur:
                if not self.store(cache, cur) and limit:
                    cur = None
                    break                       # joined what is already known
                count += 1
                if limit and count >= limit:
                    cur = None
                    break
            cur = [int(m.group(1), 16), m.group(2), m.group(3).strip()]
        if cur:
            self.store(cache, cur)
        p.kill()
        p.wait()

    @staticmethod
    def store(cache, cur):
        addr, hexbytes, text = cur
        if addr in cache:
            return False
        cache[addr] = (len(hexbytes) // 2, text)
        return True

    def get(self, vma, bits):
        cache = self.cache[bits]
        if vma not in cache:
            self.run(vma, bits, 400)
        return cache.get(vma)


# ---------------------------------------------------------------- following the code

PREFIX_WORDS = {'rep', 'repe', 'repne', 'repz', 'repnz', 'lock', 'o16', 'o32', 'o64', 'a16', 'a32', 'a64',
                'cs', 'ds', 'es', 'fs', 'gs', 'ss', 'wait', 'xacquire', 'xrelease', 'bnd'}
BRANCH = re.compile(r'^((?:\w+\s+)*?)(call|jmp|j[a-z]+|loop[a-z]*)\s+(?:short\s+|near\s+)?0x([0-9a-f]+)$')
RELREF = re.compile(r'\[rel 0x([0-9a-f]+)\]')
ENDS = {'ret', 'retf', 'retn', 'iret', 'iretw', 'iretd', 'iretq', 'jmp', 'ud2', 'sysret', 'sysretq'}
LEGACY = {0x66, 0x67, 0x2E, 0x3E, 0x26, 0x36, 0x64, 0x65, 0xF0, 0xF2, 0xF3}


def mnemonic(text):
    for w in text.split():
        if w not in PREFIX_WORDS:
            return w
    return ''


RARE = {'outsb', 'outsw', 'outsd', 'insb', 'insw', 'insd', 'arpl', 'bound', 'aaa', 'aas', 'aam', 'aad',
        'daa', 'das', 'into', 'salc', 'icebp', 'int1', 'xlatb', 'les', 'lds'}


def unlikely(text):
    """an instruction real code hardly has: a sign that data is being read as code"""
    words = text.split()
    if words[0].startswith('rex') or words[-1] in PREFIX_WORDS:
        return True
    m = mnemonic(text)
    if m in RARE and words[0] not in ('rep', 'repe', 'repne'):
        return True
    return False


class Kernel:
    def __init__(self):
        self.dec = Decoder()
        self.code = {}                          # vma -> (length, text, bits)
        self.owner = bytearray(len(image))      # per byte: 0 not code, 1 an instruction starts, 2 inside one
        self.calls, self.jumps, self.refs = set(), set(), set()
        self.conflicts, self.bad = set(), set()

        self.work = []
        self.dropped = 0

    def commit(self, a, n, text, bits):
        """make the instruction at a part of the code; returns False when nothing runs on after it"""
        o = offset(a)
        self.owner[o] = 1
        for i in range(1, n):
            self.owner[o + i] = 2
        self.code[a] = (n, text, bits)
        if a in FAR:
            self.work.append(FAR[a])
            return False
        m = BRANCH.match(text)
        if m:
            t = int(m.group(3), 16)
            if section_of(t):
                (self.calls if m.group(2) == 'call' else self.jumps).add(t)
                self.work.append((t, bits))
        for r in RELREF.findall(text):
            t = int(r, 16)
            if section_of(t) or any(t == s.end for s in SECTIONS):
                self.refs.add(t)
        return mnemonic(text) not in ENDS

    def certain(self, a, bits):
        """an address that was seen running: an instruction starts here, whatever follows"""
        sec = section_of(a)
        o = offset(a)
        if self.owner[o] == 1:
            return
        ins = self.dec.get(a, bits)
        if self.owner[o] == 2 or ins is None or ins[1].startswith('db ') or a + ins[0] > sec.end \
                or any(self.owner[o:o + ins[0]]):
            self.conflicts.add(a)
            return
        if self.commit(a, ins[0], ins[1], bits):
            self.work.append((a + ins[0], bits))

    def run(self, start, bits):
        """follow the code from start until it ends; a run that walks into data is not kept"""
        run = []
        a = start
        ok = False
        text_bytes = text_ins = 0
        while True:
            sec = section_of(a)
            if sec is None:
                break
            o = offset(a)
            if self.owner[o] == 1:
                ok = True
                break
            if self.owner[o] == 2:
                self.conflicts.add(a)
                break
            ins = self.dec.get(a, bits)
            if ins is None or ins[1].startswith('db ') or unlikely(ins[1]):
                self.bad.add(a)
                break
            n, text = ins
            if a + n > sec.end or any(self.owner[o:o + n]):
                self.conflicts.add(a)
                break
            run.append((a, n, text))
            if all(0x20 <= x <= 0x7E for x in image[o:o + n]):
                text_bytes += n
                text_ins += 1
                if text_bytes >= 14 and text_ins >= 4:      # this is a text, not code
                    break
            else:
                text_bytes = text_ins = 0
            if a in FAR or mnemonic(text) in ENDS:
                ok = True
                break
            a += n
        if not ok:
            self.dropped += 1
            last_call = -1
            for i, (a, n, text) in enumerate(run):
                if mnemonic(text) == 'call':
                    last_call = i
            run = run[:last_call + 1]           # up to a call that does not come back, or nothing
        for a, n, text in run:
            self.commit(a, n, text, bits)

    def follow(self, start, bits):
        self.work.append((start, bits))
        while self.work:
            a, bits = self.work.pop()
            self.run(a, bits)


# ---------------------------------------------------------------- writing the source

class Item:
    __slots__ = ('addr', 'length', 'text', 'code', 'fallback', 'line')

    def __init__(self, addr, length, text, code):
        self.addr, self.length, self.text, self.code = addr, length, text, code
        self.fallback = False
        self.line = 0


def db_bytes(data):
    return 'db ' + ', '.join('0x%02X' % b for b in data)


def is_text(b):
    return 0x20 <= b <= 0x7E or b in (9, 10, 13)


def db_text(data):
    parts, run = [], ''
    for b in data:
        if 0x20 <= b <= 0x7E and b != 0x27:
            run += chr(b)
        else:
            if run:
                parts.append("'" + run + "'")
                run = ''
            parts.append(str(b))
    if run:
        parts.append("'" + run + "'")
    return 'db ' + ', '.join(parts)


def data_items(a, b):
    """the bytes [a, b) that are not code, cut into readable pieces"""
    items = []
    base = offset(a)
    data = image[base:base + (b - a)]
    i, n = 0, len(data)
    while i < n:
        j = i                                   # a long run of one byte
        while j < n and data[j] == data[i]:
            j += 1
        if j - i >= 16:
            items.append(Item(a + i, j - i, 'times %d db 0x%02X' % (j - i, data[i]), False))
            i = j
            continue
        j = i                                   # a text
        while j < n and is_text(data[j]) and j - i < 120:
            j += 1
            if data[j - 1] == 10:
                break
        printable = sum(1 for x in data[i:j] if 0x20 <= x <= 0x7E)
        if printable >= 4 and 0x20 <= data[i] <= 0x7E and (j == n or data[j] == 0 or data[j - 1] == 10 or j - i >= 120):
            if j < n and data[j] == 0:
                j += 1
            items.append(Item(a + i, j - i, db_text(data[i:j]), False))
            i = j
            continue
        j = i + 1                               # plain bytes, up to 16, stopping before a text or a run
        while j < n and j - i < 16:
            if 0x20 <= data[j] <= 0x7E and all(0x20 <= x <= 0x7E for x in data[j:j + 5]) and j + 5 <= n:
                break
            if j + 16 <= n and data[j:j + 16] == bytes([data[j]]) * 16:
                break
            j += 1
        items.append(Item(a + i, j - i, db_bytes(data[i:j]), False))
        i = j
    return items


def opcode(raw, bits):
    i = 0
    while i < len(raw) and raw[i] in LEGACY:
        i += 1
    if bits == 64 and i < len(raw) and 0x40 <= raw[i] <= 0x4F:
        i += 1
    return raw[i:]


class Writer:
    def __init__(self, k):
        self.k = k
        self.names = {}
        self.given = {}
        path = os.path.join(HERE, 'names.txt')
        if os.path.exists(path):
            for line in open(path):
                f = line.split('#')[0].split()
                if len(f) == 2:
                    self.given[int(f[0], 16)] = f[1]
        for t in k.refs:
            self.names[t] = 'd_%05x' % t
        for t in k.jumps:
            self.names[t] = 'L_%05x' % t
        for t in k.calls:
            self.names[t] = 'fn_%05x' % t
        for s in SECTIONS:
            self.names.setdefault(s.vma, s.name + '_start')
        # a label that falls inside an instruction is written as (the instruction's label + n)
        self.inside = {}
        for t in list(self.names):
            if section_of(t) and k.owner[offset(t)] == 2:
                s = t
                while k.owner[offset(s)] != 1:
                    s -= 1
                self.inside[t] = s
                self.names.setdefault(s, 'L_%05x' % s)
        self.names.update(self.given)
        self.items = []
        for s in SECTIONS:
            self.items.append(self.build(s))

    def name(self, t):
        return self.names.get(t)

    def build(self, sec):
        k = self.k
        items = []
        cuts = sorted(t for t in self.names if sec.vma <= t <= sec.end and t not in self.inside)
        ci = 0
        pos = sec.vma
        while pos < sec.end:
            if pos in k.code:
                n, text, bits = k.code[pos]
                it = Item(pos, n, text, True)
                items.append(it)
                pos += n
                continue
            end = pos + 1
            while end < sec.end and k.owner[offset(end)] == 0:
                end += 1
            while ci < len(cuts) and cuts[ci] <= pos:
                ci += 1
            cj = ci
            a = pos
            while a < end:                      # cut the data at every label
                while cj < len(cuts) and cuts[cj] <= a:
                    cj += 1
                b = min(end, cuts[cj]) if cj < len(cuts) else end
                items.extend(data_items(a, b))
                a = b
            pos = end
        return items

    def render(self, it):
        n, text, bits = self.k.code[it.addr]
        raw = image[offset(it.addr):offset(it.addr) + n]
        if it.fallback:
            return db_bytes(raw) + '    ; ' + text
        m = BRANCH.match(text)
        if m and self.name(int(m.group(3), 16)):
            mn = m.group(2)
            op = opcode(raw, bits)
            if mn == 'jmp':
                size = 'short ' if op[0] == 0xEB else 'near '
            elif mn == 'call' or mn.startswith('loop') or mn in ('jcxz', 'jecxz', 'jrcxz'):
                size = ''
            else:
                size = 'short ' if 0x70 <= op[0] <= 0x7F else 'near '
            return '%s%s %s%s' % (m.group(1), mn, size, self.name(int(m.group(3), 16)))

        def rel(m):
            nm = self.name(int(m.group(1), 16))
            return '[rel %s]' % nm if nm else m.group(0)
        return RELREF.sub(rel, text)

    def write(self, path):
        k = self.k
        lines = [
            '; Kernel.kasm - the NinuxOS v2.9.59 kernel: the core (with the loader in front) and the extension.',
            '; Recovered from the compiled kernel by tools/kdis/kdis.py; it assembles to the same 220000 bytes:',
            ';   nasm -f bin Kernel.kasm -o Kernel.bin',
            ';',
            '; fn_ADDR  a function (something calls it)      L_ADDR  a place jumped to',
            '; d_ADDR   data the code points at              ADDR is the address in memory',
            '; A line that is "db ... ; instruction" is an instruction nasm would encode in another way.',
            '',
        ]
        by_inside = {}
        for t, s in self.inside.items():
            by_inside.setdefault(s, []).append(t)
        for sec, items in zip(SECTIONS, self.items):
            lines.append('')
            if sec.name == 'core':
                lines.append('section .core vstart=0x%X align=1' % sec.vma)
            else:
                lines.append('section .ext vstart=0x%X follows=.core align=1' % sec.vma)
            bits = 0
            for it in items:
                if it.code:
                    b = k.code[it.addr][2]
                    if b != bits:
                        bits = b
                        lines.append('[bits %d]' % bits)
                nm = self.name(it.addr)
                if nm and it.addr not in self.inside:
                    if nm.startswith('fn_') or it.addr in self.given:
                        lines.append('')
                    lines.append(nm + ':')
                for t in by_inside.get(it.addr, ()):
                    lines.append('%s equ %s + %d' % (self.names[t], self.names[it.addr], t - it.addr))
                it.line = len(lines) + 1
                lines.append('        ' + (self.render(it) if it.code else it.text))
            nm = self.name(sec.end)
            if nm and not section_of(sec.end):
                lines.append(nm + ':')
        with open(path, 'w', newline='\n') as f:
            f.write('\n'.join(lines) + '\n')
        return len(lines)


# ---------------------------------------------------------------- assemble and compare

LST = re.compile(r'^\s*(\d+)\s+([0-9A-F]{8})\s+\S')
ERR = re.compile(r':(\d+): (?:error|fatal)')


def assemble(src):
    out = os.path.join(WORK, 'Kernel.bin')
    lst = os.path.join(WORK, 'Kernel.lst')
    r = subprocess.run([NASM, '-f', 'bin', '-w-all', '-o', out, '-l', lst, src], capture_output=True, text=True)
    errors = sorted(set(int(m.group(1)) for m in ERR.finditer(r.stderr)))
    return out, lst, errors, r.stderr


def verify(w, src):
    """one round: returns the number of instructions newly turned into bytes (0 = nothing left to fix)"""
    out, lst, errors, stderr = assemble(src)
    by_line = {}
    for items in w.items:
        for it in items:
            by_line[it.line] = it
    if errors:
        n = 0
        for ln in errors:
            it = by_line.get(ln)
            if it and it.code and not it.fallback:
                it.fallback = True
                n += 1
        if n == 0:
            sys.exit('nasm fails on lines the tool cannot fix:\n' + stderr[:3000])
        return n, 'nasm refused %d' % n
    offs = {}
    for line in open(lst, errors='replace'):
        m = LST.match(line)
        if m and int(m.group(1)) not in offs:
            offs[int(m.group(1))] = int(m.group(2), 16)
    n = 0
    for sec, items in zip(SECTIONS, w.items):
        for i, it in enumerate(items):
            if it.line not in offs:
                if it.code and not it.fallback:     # nasm made no bytes from it
                    it.fallback = True
                    n += 1
                continue
            nxt = None
            for j in range(i + 1, len(items)):
                if items[j].line in offs:
                    nxt = offs[items[j].line]
                    break
            if nxt is None:
                continue
            if nxt - offs[it.line] != sum(x.length for x in items[i:j]):
                if not it.code or it.fallback:
                    sys.exit('line %d (%x) is plain bytes and still has the wrong length: %s' % (it.line, it.addr, it.text[:80]))
                it.fallback = True
                n += 1
    if n:
        return n, '%d of another length' % n
    built = open(out, 'rb').read()
    if len(built) != len(image):
        sys.exit('the sizes differ (%d, not %d) though every line has its length' % (len(built), len(image)))
    for items in w.items:
        for it in items:
            o = offset(it.addr)
            if built[o:o + it.length] != image[o:o + it.length]:
                if it.code and not it.fallback:
                    it.fallback = True
                    n += 1
                else:
                    sys.exit('bytes differ at %x in a line that is already plain bytes' % it.addr)
    return n, '%d of other bytes' % n


def main():
    os.makedirs(WORK, exist_ok=True)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    for s in SECTIONS:
        with open(s.file, 'wb') as f:
            f.write(image[s.off:s.off + s.size])
    if image[CORE_SIZE:CORE_SIZE + 6] != b'NXEXT1':
        sys.exit('the extension does not start where expected')

    k = Kernel()
    k.dec.run(0x840B, 64, 0)                    # one long pass each; the rest is decoded when asked for
    k.dec.run(EXT_VMA + 16, 64, 0)

    traced = []
    path = os.path.join(HERE, 'trace_addrs.txt')
    if os.path.exists(path):
        traced = [int(x, 16) for x in open(path).read().split()]
    for a in traced:                            # what really ran is certain: first
        k.certain(a, default_bits(a))
    k.follow(ENTRIES[0][0], ENTRIES[0][1])
    for a, bits in ENTRIES:
        k.follow(a, bits)
    path = os.path.join(HERE, 'seeds.txt')
    if os.path.exists(path):
        for line in open(path):
            f = line.split('#')[0].split()
            if len(f) == 2:
                k.follow(int(f[0], 16), int(f[1]))

    w = Writer(k)
    rounds = []
    for _ in range(40):
        w.write(OUT)
        n, what = verify(w, OUT)
        rounds.append(what)
        if n == 0:
            break
    else:
        sys.exit('still not the same after 40 rounds: ' + '; '.join(rounds))
    w.write(OUT)
    out, lst, errors, stderr = assemble(OUT)
    same = open(out, 'rb').read() == image

    code_bytes = sum(1 for x in k.owner if x)
    ins = [it for items in w.items for it in items if it.code]
    fb = [it for it in ins if it.fallback]
    kinds = {}
    for it in fb:
        kinds[mnemonic(k.code[it.addr][1])] = kinds.get(mnemonic(k.code[it.addr][1]), 0) + 1
    rep = [
        'assembles to the same bytes: %s' % ('YES' if same else 'NO'),
        'kernel: %d bytes (core %d, extension %d)' % (len(image), CORE_SIZE, len(image) - CORE_SIZE),
        'recognised as code: %d bytes (%.1f%%), %d instructions' % (code_bytes, 100.0 * code_bytes / len(image), len(ins)),
        'functions: %d, jump labels: %d, data labels: %d' % (len(k.calls), len(k.jumps), len(k.refs)),
        'instructions kept as bytes: %d' % len(fb),
        '  by kind: ' + ', '.join('%s %d' % kv for kv in sorted(kinds.items(), key=lambda kv: -kv[1])[:40]),
        'targets inside another instruction: %d, runs that walked into data: %d' % (len(k.conflicts), k.dropped),
        'rounds: ' + '; '.join(rounds),
        'ndisasm runs: %d' % k.dec.spawns,
        '',
        'kept as bytes:',
    ] + ['  %05x  %s' % (it.addr, k.code[it.addr][1]) for it in fb]
    with open(os.path.join(WORK, 'report.txt'), 'w') as f:
        f.write('\n'.join(rep) + '\n')
    print('\n'.join(rep[:9]))
    return 0 if same else 1


if __name__ == '__main__':
    sys.exit(main())
