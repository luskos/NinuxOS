#!/usr/bin/env python3
# build_disk.py - make disk.img from the project (NinuxOS v3).
#
#   python tools/build_disk.py [--out disk.img] [--base build/base/disk_v2.9.59.img]
#                              [--keep-version] [--no-seal] [--old-boot] [--plain-kernel]
#
# What it does:
#   1. assembles boot/Boot.kasm (the boot sector) and kernel/Kernel.kasm (core + extension) with nasm
#   2. writes the version of the project (the file VERSION) into the texts of the kernel
#   3. takes the base image - the system as it came off the stick - and puts into it
#        the boot sector, the kernel, every object of build/ at its place
#        what the sources say now, where they differ from the objects (v3.0.11):
#          pages/*.asmo, scripts/*.asmo, apps/*.asmo   the text is the DATA of its object
#          objects/NAME.asmo.kasm                      assembled, it is the object
#          kernel/suits/NAME.kasm                      assembled, it is the code of the suit
#          a page of pages/ that the cabinet does not have becomes a new page object
#          apps/py2asm.txt                             the programs compiled by pyton/py2asm.py
#                                                      into build/add/
#        every object of build/add/*.asmo as a new object of the cabinet (or in the place of the
#        one with the same name) - this is how a program made by py2asm gets into the system
#        An object that grew is moved behind the last one; its place in the table follows it.
#   4. seals it, so that the system takes it for its own:
#        the SHA-256 the core keeps of the extension
#        the Sentinel's list: the SHA-256 of every system object and of the kernel, signed with
#        this project's own key (build/key/build.key - made at the first build, never in git);
#        the public half of the key goes into the kernel. Objects the build added get lines of
#        their own, so that the system takes their code for genuine.
#        every kernel suit (kernel/suits/*.kasm is its code): signed with the same key
#   5. packs the whole source next to it (tools/source_container.py)
#
# The disk, as read from v2.9.59 (docs/NinuxOS_Architecture.tex has it in full):
#   sector 0          the boot sector
#   sectors 1..480    the kernel: core, extension, free room
#   sector 481..      the table of the cabinet: 'CABN', version, how many, its sectors (4), flags,
#                     the screen; then 32 bytes an object: name (16), sector, sectors, identity, address
#   sector 490..      the objects; a drawer is an object whose DATA is such a table ('DRWR', 63 places)
# An object and its place in the table carry the same identity; 0 in either is not checked, so
# a new object goes in with 0.

import argparse
import csv
import glob
import hashlib
import os
import shutil
import struct
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..'))
WORK = os.path.join(ROOT, 'build', 'work')
KEY = os.path.join(ROOT, 'build', 'key', 'build.key')

SECTOR = 512
KERNEL_SECTORS = 480                    # boot/Boot.kasm: kernel_sectors
KERNEL_ROOM = KERNEL_SECTORS * SECTOR
BASE_KERNEL = 220000                    # v2.9.59: the kernel, of which
CORE_SIZE = 61968                       # the core; the extension follows it
KERNEL_SAYS = b'v2.9.59'                # the version written in the kernel's texts
EXT_HASH_AT = 0xF058                    # in the v2.9.59 kernel: the SHA-256 the extension must have (ext_sha256)
PUBLIC_KEY_AT = 0x2D280                 # in the v2.9.59 kernel: the key the lists are checked with (build_public_key)
TABLE_AT = 481 * SECTOR                 # the table of the cabinet
TABLE_PLACES = 63


def find_nasm():
    p = shutil.which('nasm')
    if p:
        return p
    for d in (os.environ.get('NASM_DIR', ''),
              os.path.expandvars(r'%LOCALAPPDATA%\bin\NASM'),
              r'C:\msys64\mingw64\bin', r'C:\msys64\ucrt64\bin', r'C:\Program Files\NASM'):
        if d and os.path.exists(os.path.join(d, 'nasm.exe')):
            return os.path.join(d, 'nasm.exe')
    sys.exit('build: cannot find nasm (put it on the PATH or set NASM_DIR)')


def assemble(nasm, src, name, define=()):
    out = os.path.join(WORK, name)
    path = os.path.join(ROOT, src)
    r = subprocess.run([nasm, '-f', 'bin', '-w-all'] + ['-D' + d for d in define]
                       + ['-I', os.path.dirname(path) + os.sep, '-o', out, path],
                       capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit('build: nasm stopped on %s\n%s' % (src, r.stderr[:4000]))
    return open(out, 'rb').read()


# ---------------------------------------------------------------- Ed25519 (the Sentinel's signature)

P = 2 ** 255 - 19
ORDER = 2 ** 252 + 27742317777372353535851937790883648493
D = -121665 * pow(121666, P - 2, P) % P
ROOT_M1 = pow(2, (P - 1) // 4, P)


def _x(y):
    xx = (y * y - 1) * pow(D * y * y + 1, P - 2, P)
    x = pow(xx, (P + 3) // 8, P)
    if (x * x - xx) % P != 0:
        x = x * ROOT_M1 % P
    if (x * x - xx) % P != 0:
        return None
    return P - x if x % 2 else x


_BY = 4 * pow(5, P - 2, P) % P
BASE = (_x(_BY), _BY, 1, _x(_BY) * _BY % P)


def _add(a, b):
    x1, y1, z1, t1 = a
    x2, y2, z2, t2 = b
    e = (y1 - x1) * (y2 - x2) % P
    f = (y1 + x1) * (y2 + x2) % P
    g = t1 * 2 * D * t2 % P
    h = z1 * 2 * z2 % P
    return ((f - e) * (h - g) % P, (h + g) * (f + e) % P, (h - g) * (h + g) % P, (f - e) * (f + e) % P)


def _mul(s, p):
    q = (0, 1, 1, 0)
    while s > 0:
        if s & 1:
            q = _add(q, p)
        p = _add(p, p)
        s >>= 1
    return q


def _encode(p):
    x, y, z, t = p
    zi = pow(z, P - 2, P)
    x, y = x * zi % P, y * zi % P
    return (y | ((x & 1) << 255)).to_bytes(32, 'little')


def _decode(s):
    y = int.from_bytes(s, 'little')
    sign = y >> 255
    y &= (1 << 255) - 1
    x = _x(y) if y < P else None
    if x is None:
        return None
    if (x & 1) != sign:
        x = P - x
    return (x, y, 1, x * y % P)


def _secret(seed):
    h = hashlib.sha512(seed).digest()
    a = int.from_bytes(h[:32], 'little')
    a &= (1 << 254) - 8
    a |= 1 << 254
    return a, h[32:]


def public_key(seed):
    return _encode(_mul(_secret(seed)[0], BASE))


def sign(seed, message):
    a, prefix = _secret(seed)
    pub = _encode(_mul(a, BASE))
    r = int.from_bytes(hashlib.sha512(prefix + message).digest(), 'little') % ORDER
    big_r = _encode(_mul(r, BASE))
    k = int.from_bytes(hashlib.sha512(big_r + pub + message).digest(), 'little') % ORDER
    return big_r + ((r + k * a) % ORDER).to_bytes(32, 'little')


def verify(pub, message, signature):
    a = _decode(pub)
    s = int.from_bytes(signature[32:], 'little')
    if a is None or s >= ORDER:
        return False
    k = int.from_bytes(hashlib.sha512(signature[:32] + pub + message).digest(), 'little') % ORDER
    minus_a = (P - a[0], a[1], 1, (P - a[0]) * a[1] % P)
    return _encode(_add(_mul(s, BASE), _mul(k, minus_a))) == signature[:32]


def build_key():
    """this project's own signing key: made once, kept out of git"""
    if os.path.exists(KEY):
        return bytes.fromhex(open(KEY).read().split()[0])
    seed = os.urandom(32)
    os.makedirs(os.path.dirname(KEY), exist_ok=True)
    with open(KEY, 'w') as f:
        f.write(seed.hex() + '\n# The key the builds of this project are signed with. Keep it; do not give it away.\n'
                '# If it is lost a new one is made at the next build - sticks built before stay as they are.\n')
    print('build: a new signing key was made: build/key/build.key (keep a copy; it is not in git)')
    return seed


# ---------------------------------------------------------------- objects and the tables of the cabinet

def object_size(img, off):
    if img[off:off + 4] != b'OMSA':
        return 0
    return struct.unpack_from('<Q', img, off + 8)[0]


def object_hash(img, off):
    """what the Sentinel's list keeps of an object: the SHA-256 of all of it after the header"""
    return hashlib.sha256(img[off + 0x68:off + object_size(img, off)]).digest()


def type_at(img, lba):
    """the type of the object that lies at this sector"""
    off = lba * SECTOR
    return meta(img[off:off + object_size(img, off)], 'type') if object_size(img, off) else ''


def meta(data, key):
    m = struct.unpack_from('<Q', data, 0x18)[0]
    for part in bytes(data[m:m + 4096]).split(b'\0'):
        if not part:
            break
        if part.startswith(key.encode() + b':'):
            return part[len(key) + 1:].decode('latin-1')
    return ''


def q(data, at):
    return struct.unpack_from('<Q', data, at)[0]


def object_data(obj):
    return bytes(obj[q(obj, 0x10):q(obj, 0x10) + q(obj, 0x58)])


def rebuild_object(old, data, what='an object'):
    """the same object with other DATA: the header and META stay, what lies behind the DATA moves"""
    old = bytes(old[:q(old, 8)])
    meta_at, length = q(old, 0x18), q(old, 0x58)
    tables = [q(old, at) for at in (0x20, 0x28, 0x30)]
    if q(old, 0x10) != 0x68 or meta_at < 0x68 + length:
        sys.exit('build: %s keeps its DATA behind its code - it cannot be given other DATA' % what)
    head = bytearray(old[:0x68])
    tight = length % 8 == 0 and meta_at == 0x68 + length    # a picture: no zero kept behind the DATA
    if not any(tables):                         # DATA and META only: a page, a text, a list
        new_meta = (len(data) + 0x6F) & ~7 if tight else (len(data) + 0x70) & ~7
        m = old[meta_at:len(old) - 16]
        end = m.find(b'\0\0')
        m = m[:end + 2] if end >= 0 else m
        total = (new_meta + len(m) + 0x17) & ~7
        body = bytes(data).ljust(new_meta - 0x68, b'\0') + m
        body = body.ljust(total - 0x68 - 16, b'\0')
    else:                                       # META, then the tables of the sockets and their stub
        packed = meta_at == 0x68 + length
        new_meta = 0x68 + len(data) if packed else (len(data) + 0x70) & ~7
        delta = new_meta - meta_at
        tail = bytearray(old[meta_at:len(old) - 16].rstrip(b'\x90'))
        if min(t for t in tables if t) < meta_at:
            sys.exit('build: %s has its tables before its META - it cannot be given other DATA' % what)
        for t in tables[1:]:
            if t and q(tail, t - meta_at):
                sys.exit('build: %s has sockets of its own - it cannot be given other DATA' % what)
        if tables[0]:
            for i in range(9):
                at = tables[0] - meta_at + 8 * i
                if q(tail, at):
                    struct.pack_into('<Q', tail, at, q(tail, at) + delta)
        for at, t in zip((0x20, 0x28, 0x30), tables):
            if t:
                struct.pack_into('<Q', head, at, t + delta)
        body = bytes(data).ljust(new_meta - 0x68, b'\0') + bytes(tail)
        body += b'\x90' * (-(0x68 + len(body)) % 16)
        total = 0x68 + len(body) + 16
    struct.pack_into('<Q', head, 0x08, total)
    struct.pack_into('<Q', head, 0x18, new_meta)
    struct.pack_into('<Q', head, 0x58, len(data))
    return bytes(head) + body + struct.pack('<Q', total) + b'ASMO\0\0\0\0'


def make_object(data, meta_lines, level=5):
    """a new object of DATA and META only (a page, a text)"""
    m = b''.join(line.encode('latin-1') + b'\0' for line in meta_lines) + b'\0'
    meta_at = (len(data) + 0x70) & ~7
    total = (meta_at + len(m) + 0x17) & ~7
    head = bytearray(0x68)
    head[0:4] = b'OMSA'
    struct.pack_into('<IQQQ', head, 4, 4, total, 0x68, meta_at)
    struct.pack_into('<Q', head, 0x38, 1)
    struct.pack_into('<III', head, 0x48, 1, 0, level)
    struct.pack_into('<Q', head, 0x58, len(data))
    body = (bytes(data).ljust(meta_at - 0x68, b'\0') + m).ljust(total - 0x68 - 16, b'\0')
    return bytes(head) + body + struct.pack('<Q', total) + b'ASMO\0\0\0\0'


class Table:
    """a table of objects: the cabinet's ('CABN') or a drawer's ('DRWR'); at is where it lies in the image"""

    def __init__(self, img, at):
        self.at = at
        self.magic = bytes(img[at:at + 4])
        self.count = struct.unpack_from('<H', img, at + (6 if self.magic == b'CABN' else 4))[0]

    def entries(self, img):
        for i in range(TABLE_PLACES):
            e = self.at + 16 + 32 * i
            if img[e]:
                name = bytes(img[e:e + 16]).split(b'\0')[0].decode('latin-1')
                lba, sectors, ident = struct.unpack_from('<III', img, e + 16)
                yield e, name, lba, sectors, ident


def all_tables(img):
    top = Table(img, TABLE_AT)
    if top.magic != b'CABN':
        sys.exit('build: the table of the cabinet is not at sector 481 of the base image')
    tables = [top]
    for e, name, lba, sectors, ident in top.entries(img):
        off = lba * SECTOR
        if type_at(img, lba) == 'cabinet':
            data = off + struct.unpack_from('<Q', img, off + 0x10)[0]
            if img[data:data + 4] == b'DRWR':
                tables.append(Table(img, data))
    return tables


def free_sector(img, tables):
    """the first sector behind every object the tables know"""
    used = 490
    for t in tables:
        for e, n, lba, sectors, ident in t.entries(img):
            used = max(used, lba + sectors)
    return used


def entry_at(img, tables, off):
    """the place of a table that speaks of the object lying at off"""
    for t in tables:
        for e, n, lba, sectors, ident in t.entries(img):
            if lba * SECTOR == off:
                return e
    return None


def put(img, tables, e, data):
    """the object of the place e becomes data: where it lies if it fits, else behind the last one"""
    lba, sectors = struct.unpack_from('<II', img, e + 16)
    need = (len(data) + SECTOR - 1) // SECTOR
    if need > sectors:
        lba = free_sector(img, tables)
        if (lba + need) * SECTOR > len(img):
            img.extend(b'\0' * ((lba + need) * SECTOR - len(img)))
        sectors = need
    img[lba * SECTOR:(lba + sectors) * SECTOR] = bytes(data).ljust(sectors * SECTOR, b'\0')
    struct.pack_into('<II', img, e + 16, lba, need)
    return lba


def add_object(img, tables, data, name=None):
    """a new object of the cabinet, or a new one in the place of the object with its name;
    returns what it did, and the name of its line in the Sentinel's list with its place in the table"""
    data = bytes(data)
    if data[:4] != b'OMSA' or q(data, 8) != len(data) or data[-8:-4] != b'ASMO':
        sys.exit('build: %s is not a whole ASMO object' % name)
    name = (meta(data, 'name') or name).lower()[:15]
    source = meta(data, 'type') == 'source'
    place = None
    for t in tables:                            # the drawers too
        for e, n, lba, sec, ident in t.entries(img):
            if n == name and (type_at(img, lba) == 'source') == source:
                place = e
    what = 'in the place of the old one'
    if place is None:
        what = 'new'
        top = tables[0]
        for i in range(TABLE_PLACES):
            if not img[top.at + 16 + 32 * i]:
                place = top.at + 16 + 32 * i
                break
        if place is None:
            sys.exit('build: the cabinet has no free place for %s (63 objects; put it in a drawer)' % name)
        top.count += 1
        struct.pack_into('<H', img, top.at + 6, top.count)
        img[place:place + 32] = name.encode('latin-1').ljust(16, b'\0') + bytes(16)
    # the identity: an object and its place carry the same one. A new object made outside the
    # system has none (0, which is not checked); one that takes the place of another takes its
    # identity too, so that everything that knew the old one finds the new one the same
    ident = struct.unpack_from('<I', data, 0x4C)[0] or struct.unpack_from('<I', img, place + 24)[0]
    data = data[:0x4C] + struct.pack('<I', ident) + data[0x50:]
    lba = put(img, tables, place, data)
    struct.pack_into('<I', img, place + 24, ident)
    line = (name + '/source')[:15] if source else name
    return '%s (%s, %d bytes, sector %d)' % (name, what, len(data), lba), (line, place)


def programs(nasm):
    """apps/py2asm.txt: the programs compiled by the new py2asm into build/add/"""
    listing = os.path.join(ROOT, 'apps', 'py2asm.txt')
    if not os.path.exists(listing):
        return
    os.makedirs(os.path.join(ROOT, 'build', 'add'), exist_ok=True)
    for line in open(listing):
        parts = line.split('#')[0].split()
        if len(parts) != 2:
            continue
        asm = os.path.join(WORK, parts[1] + '.asm')
        r = subprocess.run([sys.executable, os.path.join(ROOT, 'pyton', 'py2asm.py'), os.path.join(ROOT, 'apps', parts[0]),
                            '--target', 'ninux', '--name', parts[1], '-o', asm], capture_output=True, text=True)
        if r.returncode != 0:
            sys.exit('build: py2asm stopped on apps/%s\n%s' % (parts[0], (r.stderr or r.stdout)[:4000]))
        r = subprocess.run([nasm, '-f', 'bin', '-w-all', '-I', os.path.join(ROOT, 'pyton') + os.sep,
                            '-o', os.path.join(ROOT, 'build', 'add', parts[1] + '.asmo'), asm],
                           capture_output=True, text=True)
        if r.returncode != 0:
            sys.exit('build: nasm stopped on the program %s\n%s' % (parts[1], r.stderr[:4000]))


SUITS = {'k_tools': 'Tools', 'k_usb12': 'USB12', 'k_net': 'Network', 'k_sound': 'Sound'}


SUIT_ROOM = {0x30000: 0x20000, 0x80000: 0x2000, 0x82000: 0x4000, 0x86000: 0x1A000}   # the slot: what fits


def suits(img, tables):
    """the kernel suits of the cabinet: (name, where the DATA starts, its length, its place in the table)"""
    for t in tables:
        for e, name, lba, sectors, ident in t.entries(img):
            off = lba * SECTOR
            if object_size(img, off) and meta(img[off:off + object_size(img, off)], 'type') == 'kernel':
                yield name, off + q(img, off + 0x10), q(img, off + 0x58), e


def suit_sources(nasm, img, tables, changed):
    """kernel/suits/NAME.kasm is the code of a suit: assembled and put into its object"""
    for name, data, length, e in list(suits(img, tables)):
        src = os.path.join('kernel', 'suits', SUITS.get(name, name) + '.kasm')
        if not os.path.exists(os.path.join(ROOT, src)):
            continue
        code = assemble(nasm, src, name + '.bin')
        slot, size = q(img, data + 64), q(img, data + 72)
        if code == img[data + 96:data + 96 + size]:
            continue
        if len(code) == size:
            img[data + 96:data + 96 + size] = code
        else:                                   # another size: the object is made anew around it
            if len(code) > SUIT_ROOM.get(slot, size):
                sys.exit('build: the suit %s is %d bytes now; at 0x%X there is room for %d'
                         % (name, len(code), slot, SUIT_ROOM.get(slot, size)))
            off = struct.unpack_from('<I', img, e + 16)[0] * SECTOR
            old = bytes(img[off:off + object_size(img, off)])
            new = bytes(img[data:data + 72]) + struct.pack('<Q', len(code)) + bytes(img[data + 80:data + 96]) + code
            put(img, tables, e, rebuild_object(old, new, 'the suit ' + name))
        changed.append('the suit %s (%s, %d bytes)' % (name, src.replace(os.sep, '/'), len(code)))


def sign_suits(img, tables, seed):
    """a suit carries a signature over its slot, its size and its code: ours, since the key is ours"""
    done = 0
    for name, data, length, e in suits(img, tables):
        img[data:data + 64] = sign(seed, bytes(img[data + 64:data + length]))
        done += 1
    return done


def seal(img, base, tables, seed, old_public, added):
    """the Sentinel's list for this image, signed with our key; returns what it did.
    added: (the name of a line, the place in a table) of the objects the build put in"""
    place = None
    for t in tables:
        for e, name, lba, sectors, ident in t.entries(base):
            if name == 'sentinel':
                place = e
    if place is None:
        return 'no Sentinel list in this system - not signed'
    sentinel = struct.unpack_from('<I', base, place + 16)[0] * SECTOR
    data = sentinel + q(base, sentinel + 0x10)
    length = q(base, sentinel + 0x58)
    body = bytes(base[data + 64:data + length])
    if body[:4] != b'NXSN' or not verify(old_public, body, bytes(base[data:data + 64])):
        return 'the Sentinel list of the base image is not as expected - left as it is'
    count = struct.unpack_from('<I', body, 4)[0]
    # the objects the build added get lines of their own. The list grows, so its object grows:
    # it is given its new place first (a place in a drawer changes the drawer, which may be listed)
    listed = set(body[12 + 48 * i:28 + 48 * i].split(b'\0')[0] for i in range(count))
    more = [(n, e) for n, e in added if n.encode('latin-1') not in listed]
    old_object = bytes(base[sentinel:sentinel + object_size(base, sentinel)])
    if more:
        blank = rebuild_object(old_object, bytes(64 + len(body) + 48 * len(more)), 'the Sentinel list')
        put(img, tables, place, blank)
    # which place of which table each line of the list speaks of: found by the hash it has now
    by_hash = {}
    for t in tables:
        for e, name, lba, sectors, ident in Table(base, t.at).entries(base):
            if object_size(base, lba * SECTOR):
                by_hash[object_hash(base, lba * SECTOR)] = e
    new = bytearray(body)
    fresh = kept = 0
    for i in range(count):
        at = 12 + 48 * i
        name = body[at:at + 16].split(b'\0')[0]
        old = body[at + 16:at + 48]
        if name == b'@kernel':
            h = hashlib.sha256(img[SECTOR:SECTOR + KERNEL_ROOM]).digest()
        elif old in by_hash:
            lba = struct.unpack_from('<I', img, by_hash[old] + 16)[0]
            h = object_hash(img, lba * SECTOR)
        else:
            h = old                             # the list did not match this object before either
            kept += 1
        if h != old:
            fresh += 1
        new[at + 16:at + 48] = h
    for n, e in more:
        lba = struct.unpack_from('<I', img, e + 16)[0]
        new += n.encode('latin-1').ljust(16, b'\0') + object_hash(img, lba * SECTOR)
    struct.pack_into('<I', new, 4, count + len(more))
    signature = sign(seed, bytes(new))
    if not verify(public_key(seed), bytes(new), signature):
        sys.exit('build: the signature just made does not check - not built')
    put(img, tables, place, rebuild_object(old_object, signature + bytes(new), 'the Sentinel list'))
    return ('the Sentinel list: %d lines (%d new), %d written anew, %d left as they were; signed'
            % (count + len(more), len(more), fresh, kept))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=os.path.join(ROOT, 'disk.img'))
    ap.add_argument('--base', default=os.path.join(ROOT, 'build', 'base', 'disk_v2.9.59.img'))
    ap.add_argument('--keep-version', action='store_true', help='leave v2.9.59 in the texts of the kernel')
    ap.add_argument('--no-seal', action='store_true', help='do not sign: the Sentinel will call what changed CHANGED')
    ap.add_argument('--plain-kernel', action='store_true',
                    help='the kernel without the code written after the recovery (Alt + *): the 220000 bytes of v2.9.59')
    ap.add_argument('--old-boot', action='store_true', help='the boot sector of v2.9.59 (a FAT12 diskette to Windows)')
    a = ap.parse_args()

    if not os.path.exists(a.base):
        sys.exit('build: the base image is missing: ' + a.base)
    os.makedirs(WORK, exist_ok=True)
    base = open(a.base, 'rb').read()
    img = bytearray(base)
    nasm = find_nasm()
    changed = []

    boot = assemble(nasm, os.path.join('boot', 'Boot.kasm'), 'Boot.bin')
    if a.old_boot:
        boot = base[:SECTOR]
    if len(boot) != SECTOR or boot[510:512] != b'\x55\xAA':
        sys.exit('build: the boot sector must be 512 bytes that end in 55 AA')
    if boot != base[:SECTOR]:
        changed.append('the boot sector')
    img[0:SECTOR] = boot

    kernel = assemble(nasm, os.path.join('kernel', 'Kernel.kasm'), 'Kernel.bin',
                      ['PLAIN_KERNEL'] if a.plain_kernel else [])
    if len(kernel) > KERNEL_ROOM:
        sys.exit('build: the kernel is %d bytes, the boot sector reads only %d' % (len(kernel), KERNEL_ROOM))
    base_kernel = base[SECTOR:SECTOR + len(kernel)]
    if kernel != base_kernel:
        changed.append('the kernel (kernel/Kernel.kasm)')
    version = ('v' + open(os.path.join(ROOT, 'VERSION')).read().strip()).encode()
    if not a.keep_version:
        if len(version) != len(KERNEL_SAYS):
            print('build: VERSION must be as long as %s (3.0.04) - the version is not written' % KERNEL_SAYS.decode())
        elif version != KERNEL_SAYS:
            n = kernel.count(KERNEL_SAYS)
            kernel = kernel.replace(KERNEL_SAYS, version)
            changed.append('the version the system says (%s, %d places)' % (version.decode(), n))

    table = os.path.join(ROOT, 'docs', 'cabinet_objects.csv')
    tables = all_tables(img)
    count = 0
    grown = []                                  # (where it lay, the object): put in when the rest lies
    have = set()                                # the sources the cabinet has objects for
    for row in csv.DictReader(open(table, encoding='utf-8-sig')):
        off = int(row['Offset'], 16)
        size = int(row['Size'])
        path = os.path.join(ROOT, row['Object'])
        if not os.path.exists(path):
            sys.exit('build: the object file is missing: ' + row['Object'])
        data = open(path, 'rb').read()
        if data[:4] != b'OMSA':
            sys.exit('build: %s is not an ASMO object (no OMSA at its start)' % row['Object'])
        said = row['Object']
        # the source is what counts: a text that is the DATA of its object ...
        text = os.path.join(ROOT, row['Source']) if row['Source'] else ''
        if text and os.path.exists(text):
            have.add(os.path.normcase(os.path.abspath(text)))
            now = open(text, 'rb').read()
            if now != object_data(data):
                data = rebuild_object(data, now, row['Source'])
                said = '%s (from %s)' % (row['Object'], row['Source'].replace(os.sep, '/'))
        # ... or the object written as source, assembled
        kasm = os.path.join('objects', os.path.basename(row['Object']) + '.kasm')
        if os.path.exists(os.path.join(ROOT, kasm)):
            made = assemble(nasm, kasm, os.path.basename(row['Object']))
            if made != data:
                data = made
                said = '%s (from %s)' % (row['Object'], kasm.replace(os.sep, '/'))
        if data != base[off:off + size]:
            changed.append(said)
        if len(data) == size:
            img[off:off + size] = data
        else:
            grown.append((off, data, said))
        count += 1
    for off, data, said in grown:
        e = entry_at(img, tables, off)
        if e is None:
            print('build: %s is an old copy no table speaks of - its changed source is not put in' % said)
            changed.remove(said)
            continue
        put(img, tables, e, data)

    suit_sources(nasm, img, tables, changed)
    programs(nasm)
    added = []                                  # what the build puts in: lines for the Sentinel's list
    for path in sorted(glob.glob(os.path.join(ROOT, 'pages', '*.asmo'))):
        if os.path.normcase(os.path.abspath(path)) in have:
            continue                            # a page the cabinet does not have: a new object
        name = os.path.splitext(os.path.basename(path))[0].lower()
        page = make_object(open(path, 'rb').read(),
                           ['type:page', 'name:' + name, 'label:' + name, 'kind:page', 'lang:html',
                            'data:HTML page (CSS inside or linked)', 'desktop:no', 'made:build_disk.py'])
        said, line = add_object(img, tables, page, name)
        changed.append('a new page: ' + said)
        added.append(line)
    for path in sorted(glob.glob(os.path.join(ROOT, 'build', 'add', '*.asmo'))):
        said, line = add_object(img, tables, open(path, 'rb').read(), os.path.splitext(os.path.basename(path))[0])
        changed.append('added: ' + said)
        added.append(line)


    # the two places the build fills in are found by what the source still holds there - the key
    # and the hash of v2.9.59 - so they are found wherever a changed kernel has them
    base_k = base[SECTOR:SECTOR + BASE_KERNEL]
    old_public = base_k[PUBLIC_KEY_AT:PUBLIC_KEY_AT + 32]
    old_hash = hashlib.sha256(base_k[CORE_SIZE:]).digest()
    if base_k[EXT_HASH_AT:EXT_HASH_AT + 32] != old_hash:
        sys.exit('build: the base image is not v2.9.59 as it came off the stick - not built')
    key_at, hash_at, ext_at = kernel.find(old_public), kernel.find(old_hash), kernel.find(b'NXEXT1\0\0')
    if min(key_at, hash_at, ext_at) < 0:
        sys.exit('build: kernel/Kernel.kasm no longer has build_public_key, ext_sha256 or the extension as they were')
    sealed = None
    if changed and not a.no_seal:
        seed = build_key()
        kernel = kernel[:key_at] + public_key(seed) + kernel[key_at + 32:]
    ext_size = struct.unpack_from('<Q', kernel, ext_at + 8)[0]
    new_hash = hashlib.sha256(kernel[ext_at:ext_at + ext_size]).digest()
    if new_hash != old_hash:
        kernel = kernel[:hash_at] + new_hash + kernel[hash_at + 32:]
    img[SECTOR:SECTOR + len(kernel)] = kernel
    if changed and not a.no_seal:
        signed = sign_suits(img, tables, seed)
        sealed = '%d kernel suits signed; ' % signed + seal(img, base, tables, seed, old_public, added)

    with open(a.out, 'wb') as f:
        f.write(img)
    try:                                    # the whole source goes with every build
        import source_container
        source_container.pack()
    except Exception as e:
        print('build: the source container was not made (%s)' % e)
    print('build: boot sector %d bytes, kernel %d bytes, %d objects' % (len(boot), len(kernel), count))
    print('build: %s  %d bytes  SHA-256 %s' % (a.out, len(img), hashlib.sha256(img).hexdigest()))
    if not changed:
        print('build: the same as the base image (v2.9.59)')
    else:
        for c in changed:
            print('build:   ' + c)
        print('build: ' + (sealed or 'NOT signed (--no-seal): the Sentinel will call what changed CHANGED'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
