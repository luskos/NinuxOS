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
#         tools/kdis/pointers.txt        optional: where pointers to code lie in the data, "ADDR"
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
import struct
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

# set by a tool that uses this file for something else than the kernel (tools/kdis/odis.py)
POINTERS = {}                           # address -> (bytes, the address kept there, what is added to it)
GIVEN = {}                              # address -> name
BLOBS = None                            # (folder, name): long runs of plain data go into files there
EXTERNAL = {}                           # address outside the image -> name (a suit calling the kernel)
VARIABLES = False                       # name the memory outside the image the code points at (the kernel)
SIZES = {}                              # a number in the code that is a size of the image -> how to say it
HEADER = [
    '; Kernel.kasm - the NinuxOS v2.9.59 kernel: the core (with the loader in front) and the extension.',
    '; Recovered from the compiled kernel by tools/kdis/kdis.py; it assembles to the same 220000 bytes:',
    ';   nasm -f bin Kernel.kasm -o Kernel.bin',
    ';',
    '; fn_ADDR  a function (something calls it)      L_ADDR  a place jumped to',
    '; d_ADDR   data the code points at              ADDR is the address in memory',
    '; A line that is "db ... ; instruction" is an instruction nasm would encode in another way.',
    '',
]
DIRECTIVES = {'core': 'section .core vstart=0x7E00 align=1',
              'ext': 'section .ext vstart=0x50000 follows=.core align=1'}


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
# an address written as a plain number: in memory brackets, in a pointer register of the 16- and 32-bit
# loader, in a far jump (the 64-bit code points relative to itself, and is caught by RELREF)
ABSREF = re.compile(r'(\[(?:[cdefgs]s:)?(?:abs )?|\b(?:mov|lea) (?:e?si|e?di|e?bx|e?bp),|:d?word )0x([0-9a-f]+)(?=\]|$)')
ENDS = {'ret', 'retq', 'retw', 'retd', 'retf', 'retfq', 'retn', 'iret', 'iretw', 'iretd', 'iretq', 'jmp', 'ud2',
        'sysret', 'sysretq'}
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
        self.outside = set()                    # what the code points at beyond the image: the kernel's variables
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
            self.jumps.add(FAR[a][0])
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
            else:
                self.outside.add(t)
        for lead, r in ABSREF.findall(text):
            t = int(r, 16)
            if section_of(t) and (bits != 64 or 'abs ' in lead):
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
    if BLOBS and b - a >= 8192 and (data[:4096].count(0) > 40 or sum(1 for x in data[:4096] if 0x20 <= x <= 0x7E) < 2400):
        folder, name = BLOBS                    # pixels and the like: kept as they are, beside the source
        os.makedirs(folder, exist_ok=True)
        blob = '%s.%05x.bin' % (name, a)
        with open(os.path.join(folder, blob), 'wb') as f:
            f.write(data)
        return [Item(a, b - a, 'incbin "%s/%s"' % (os.path.basename(folder), blob), False)]
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
        self.given = dict(GIVEN)
        path = os.path.join(HERE, 'names.txt')
        if os.path.exists(path) and not GIVEN and not POINTERS:
            for line in open(path):
                f = line.split('#')[0].split()
                if len(f) == 2:
                    self.given[int(f[0], 16)] = f[1]
        for p in POINTERS.values():
            self.names[p[1]] = 'p_%05x' % p[1]
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
        self.variables()                        # gives the outside addresses their names
        self.items = []
        for s in SECTIONS:
            self.items.append(self.build(s))

    def name(self, t):
        return self.names.get(t)

    def build(self, sec):
        k = self.k
        items = []
        cuts = set(t for t in self.names if sec.vma <= t <= sec.end and t not in self.inside)
        for a, p in POINTERS.items():
            cuts.update((a, a + p[0]))
        cuts = sorted(cuts)
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
                if a in POINTERS and a + POINTERS[a][0] <= end:     # an address is kept here: by its name
                    size, t, plus = POINTERS[a][:3]
                    text = '%s %s' % ('dq' if size == 8 else 'dd', self.pointer_name(t))
                    text += ' + 0x%X' % plus if plus else ''
                    items.append(Item(a, size, POINTERS[a][3] if len(POINTERS[a]) > 3 else text, False))
                    a += size
                    continue
                items.extend(data_items(a, b))
                a = b
            pos = end
        return items

    def variables(self):
        """what the code points at outside the image - the memory the kernel keeps its variables in -
        gets names too (v_ADDR)"""
        out = sorted(t for t in self.k.outside if not section_of(t) and not any(t == s.end for s in SECTIONS)
                     and (t not in EXTERNAL or EXTERNAL[t] == 'v_%05x' % t))
        if not out or not VARIABLES:
            return []
        lines = ['', '; ---- memory outside the file: the variables of the kernel, in the order they lie']
        for t in out:
            EXTERNAL[t] = 'v_%05x' % t
            lines.append('v_%05x equ 0x%X' % (t, t))
        return lines
    def pointer_name(self, t):
        if t in self.inside:
            return '%s + %d' % (self.names[self.inside[t]], t - self.inside[t])
        return self.names[t]

    def render(self, it):
        n, text, bits = self.k.code[it.addr]
        raw = image[offset(it.addr):offset(it.addr) + n]
        if it.fallback:
            return db_bytes(raw) + '    ; ' + text
        m = BRANCH.match(text)
        if m and (self.name(int(m.group(3), 16)) or int(m.group(3), 16) in EXTERNAL):
            target = self.name(int(m.group(3), 16)) or EXTERNAL[int(m.group(3), 16)]
            mn = m.group(2)
            op = opcode(raw, bits)
            if mn == 'jmp':
                size = 'short ' if op[0] == 0xEB else 'near '
            elif mn == 'call' or mn.startswith('loop') or mn in ('jcxz', 'jecxz', 'jrcxz'):
                size = ''
            else:
                size = 'short ' if 0x70 <= op[0] <= 0x7F else 'near '
            return '%s%s %s%s' % (m.group(1), mn, size, target)

        def rel(m):
            t = int(m.group(1), 16)
            if self.name(t):
                return '[rel %s]' % self.name(t)
            if t in EXTERNAL:                   # a fixed place in memory: said from the start of this code,
                base = SECTIONS[0]              # so that nasm keeps it relative to the instruction
                return '[rel %s + (%s - 0x%X)]' % (self.names[base.vma], EXTERNAL[t], base.vma)
            return m.group(0)

        def absolute(m):
            t = int(m.group(2), 16)
            if self.name(t) and (bits != 64 or 'abs ' in m.group(1)):
                return m.group(1) + self.name(t)
            return m.group(0)
        text = ABSREF.sub(absolute, RELREF.sub(rel, text))
        for value, say in SIZES.items():
            text = re.sub(r'(?<![\w\[])0x%x\b' % value, say, text)
        return text

    def write(self, path):
        k = self.k
        lines = list(HEADER)
        by_inside = {}
        for t, s in self.inside.items():
            by_inside.setdefault(s, []).append(t)
        for sec, items in zip(SECTIONS, self.items):
            lines.append('')
            lines.append(DIRECTIVES[sec.name])
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
        lines.extend(self.variables())
        with open(path, 'w', newline='\n') as f:
            f.write('\n'.join(lines) + '\n')
        return len(lines)


# ---------------------------------------------------------------- the tables of addresses in the kernel's data

API_TABLE = 0x110C8                     # what a program gets in rsi: the functions of the system, 8 bytes each
API_NAMES = {0x00: 'print', 0x08: 'put_letter', 0x10: 'screen_size', 0x18: 'fill', 0x30: 'text', 0x38: 'window',
             0x40: 'poll', 0x48: 'cursor_show', 0x50: 'cursor_hide', 0x58: 'ob_count', 0x60: 'ob_by_number',
             0x68: 'ob_by_name', 0x70: 'ob_meta', 0x90: 'random', 0xA0: 'ticks', 0xB0: 'memory', 0xC0: 'log',
             0xE0: 'ob_save', 0x118: 'programs', 0x128: 'system_text', 0x138: 'sound', 0x140: 'fill_round',
             0x150: 'network'}
STARTS = (0x53, 0x55, 0x41, 0x48, 0x50, 0x51, 0x52, 0x56, 0x57)


def text_at(v):
    o = offset(v)
    return o > 0 and image[o - 1] == 0 and all(32 <= c < 127 for c in image[o:o + 4])


def find_pointers(k):
    """8-byte values in the data that are addresses inside the kernel: tables of texts and of
    functions (the shell's commands, the functions a program may call ...). A value counts when it
    has a neighbour of the same kind 8 or 16 bytes away, or points at a function already known.
    What a table points at is followed as code, so the tables also show where more code is."""
    while True:
        cands = {}
        for sec in SECTIONS:
            for a in range(sec.vma, sec.end - 7):
                o = offset(a)
                if any(k.owner[o:o + 8]):
                    continue
                v = struct.unpack_from('<Q', image, o)[0]
                if v >> 20 == 0 and section_of(v) and k.owner[offset(v)] != 2 \
                        and not any((a + i) in k.refs for i in range(1, 8)):     # no name falls inside it
                    cands[a] = v
        good = {a: v for a, v in cands.items()
                if any((a + d) in cands for d in (-16, -8, 8, 16)) or v in k.calls}
        before = len(k.code)
        for a, v in sorted(good.items()):
            if k.owner[offset(v)] == 0 and not text_at(v):
                in_table = any((a + d) in good for d in (-16, -8, 8, 16))
                if in_table or image[offset(v)] in STARTS:
                    k.follow(v, 64)
        if len(k.code) == before:
            break
    out = {}
    last = -8
    for a in sorted(good):
        if a >= last + 8 and not any(k.owner[offset(a):offset(a) + 8]):
            out[a] = (8, good[a], 0)
            last = a
    return out


def table_names(pointers):
    """names from the tables: the functions a program may call, and the shell's commands"""
    given = {API_TABLE: 'api_table'}
    for at, name in API_NAMES.items():
        if API_TABLE + at in pointers:
            given.setdefault(pointers[API_TABLE + at][1], 'api_' + name)
    for a in sorted(pointers):                  # a text and, right after it, the function for it
        v = pointers[a][1]
        if text_at(v) and a + 8 in pointers and not text_at(pointers[a + 8][1]):
            o = offset(v)
            word = image[o:o + 24].split(b'\0')[0].decode('latin-1')
            if word.isidentifier() and word.islower():
                given.setdefault(pointers[a + 8][1], 'cmd_' + word)
    return given


# ---------------------------------------------------------------- assemble and compare

LST = re.compile(r'^\s*(\d+)\s+([0-9A-F]{8})\s+\S')
ERR = re.compile(r':(\d+): (?:error|fatal)')


def assemble(src):
    out = os.path.join(WORK, 'Kernel.bin')
    lst = os.path.join(WORK, 'Kernel.lst')
    r = subprocess.run([NASM, '-f', 'bin', '-w-all', '-I', os.path.dirname(os.path.abspath(src)) + os.sep,
                        '-o', out, '-l', lst, src], capture_output=True, text=True)
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

    # pointers.txt: addresses where 8 bytes of a pointer to code lie that the search below does not
    # find by itself (tables whose pointers stand 24 or 48 bytes apart): what they point at is code
    told = {}
    path = os.path.join(HERE, 'pointers.txt')
    if os.path.exists(path):
        for line in open(path):
            f = line.split('#')[0].split()
            if f:
                a = int(f[0], 16)
                told[a] = struct.unpack_from('<Q', image, offset(a))[0]
                k.follow(told[a], 64)

    global POINTERS, GIVEN, VARIABLES, SIZES
    POINTERS = find_pointers(k)
    for a, v in told.items():
        if a not in POINTERS and not any(k.owner[offset(a):offset(a) + 8]) \
                and not any((a + i) in POINTERS for i in range(-7, 8)):
            POINTERS[a] = (8, v, 0)
    GIVEN = table_names(POINTERS)
    # names.txt: the names the source already uses (the suits and the code written by hand call
    # the kernel by them), so that reading the kernel again does not rename anything
    path = os.path.join(HERE, 'names.txt')
    if os.path.exists(path):
        for line in open(path):
            f = line.split('#')[0].split()
            if len(f) == 2 and section_of(int(f[0], 16)):
                GIVEN.setdefault(int(f[0], 16), f[1])
    VARIABLES = True
    # the size of the extension stands in its own header and, as a number, in the core that checks it
    ext = SECTIONS[1]
    GIVEN[ext.end] = 'ext_end'
    GIVEN[ext.vma] = 'ext_start'
    GIVEN[SECTIONS[0].vma] = 'core_start'
    POINTERS[ext.vma + 8] = (8, ext.end, 0, 'dq ext_end - ext_start')
    SIZES = {ext.size: '(ext_end - ext_start)'}
    GIVEN[CORE_VMA + 0xF058] = 'ext_sha256'           # the SHA-256 the extension must have (the build fills it)
    GIVEN[EXT_VMA + 0x2D280 - CORE_SIZE] = 'build_public_key'   # the key the Sentinel's list and the suits are checked with

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
    # the names of the kernel, for what is assembled apart from it and calls it (the kernel suits)
    with open(os.path.join(os.path.dirname(OUT), 'Kernel.sym.inc'), 'w', newline='\n') as f:
        f.write('; Kernel.sym.inc - where everything in kernel/Kernel.kasm is; made by tools/kdis/kdis.py.\n')
        for addr in sorted(w.names):
            if section_of(addr):
                f.write('%s equ 0x%X\n' % (w.names[addr], addr))
        for addr in sorted(EXTERNAL):
            f.write('%s equ 0x%X\n' % (EXTERNAL[addr], addr))

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
        'addresses in the data, now names: %d (the shell commands and the functions for programs among them)' % len(POINTERS),
        'targets inside another instruction: %d, runs that walked into data: %d' % (len(k.conflicts), k.dropped),
        'rounds: ' + '; '.join(rounds),
        'ndisasm runs: %d' % k.dec.spawns,
        '',
        'kept as bytes:',
    ] + ['  %05x  %s' % (it.addr, k.code[it.addr][1]) for it in fb]
    with open(os.path.join(WORK, 'report.txt'), 'w') as f:
        f.write('\n'.join(rep) + '\n')
    print('\n'.join(rep[:10]))
    return 0 if same else 1


if __name__ == '__main__':
    sys.exit(main())
