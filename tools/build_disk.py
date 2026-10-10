#!/usr/bin/env python3
# build_disk.py - make disk.img from the project (NinuxOS v3).
#
#   python tools/build_disk.py [--out disk.img] [--base build/base/disk_v2.9.59.img] [--keep-version]
#
# What it does:
#   1. assembles boot/Boot.kasm (the boot sector) and kernel/Kernel.kasm (core + extension) with nasm
#   2. writes the version of the project (the file VERSION) into the texts of the kernel
#   3. takes the base image - the system as it came off the stick - and puts into it
#        the boot sector, the kernel, every object of build/ at its place
#        every object of build/add/*.asmo as a new object of the cabinet (or in the place of the
#        one with the same name) - this is how a program made by py2asm gets into the system
#   4. seals it, so that the system takes it for its own:
#        the SHA-256 the core keeps of the extension
#        the Sentinel's list: the SHA-256 of every system object and of the kernel, signed with
#        this project's own key (build/key/build.key - made at the first build, never in git);
#        the public half of the key goes into the kernel
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


def assemble(nasm, src, name):
    out = os.path.join(WORK, name)
    path = os.path.join(ROOT, src)
    r = subprocess.run([nasm, '-f', 'bin', '-w-all', '-I', os.path.dirname(path) + os.sep, '-o', out, path],
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


def meta(data, key):
    m = struct.unpack_from('<Q', data, 0x18)[0]
    for part in bytes(data[m:m + 4096]).split(b'\0'):
        if not part:
            break
        if part.startswith(key.encode() + b':'):
            return part[len(key) + 1:].decode('latin-1')
    return ''


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
        if object_size(img, off) and meta(img[off:off + 8192], 'type') == 'cabinet':
            data = off + struct.unpack_from('<Q', img, off + 0x10)[0]
            if img[data:data + 4] == b'DRWR':
                tables.append(Table(img, data))
    return tables


def add_object(img, tables, path):
    """a new object of the cabinet, or a new one in the place of the object with its name"""
    data = open(path, 'rb').read()
    if data[:4] != b'OMSA' or struct.unpack_from('<Q', data, 8)[0] != len(data) or data[-8:-4] != b'ASMO':
        sys.exit('build: %s is not a whole ASMO object' % os.path.relpath(path, ROOT))
    name = (meta(data, 'name') or os.path.splitext(os.path.basename(path))[0]).lower()[:15]
    kind = meta(data, 'type')
    top = tables[0]
    used = 490
    for t in tables:
        for e, n, lba, sectors, ident in t.entries(img):
            used = max(used, lba + sectors)
    sectors = (len(data) + SECTOR - 1) // SECTOR
    if (used + sectors) * SECTOR > len(img):
        img.extend(b'\0' * ((used + sectors) * SECTOR - len(img)))
    place = None
    for e, n, lba, sec, ident in top.entries(img):
        if n == name and (meta(img[lba * SECTOR:lba * SECTOR + 8192], 'type') == 'source') == (kind == 'source'):
            place = e
    what = 'in the place of the old one'
    if place is None:
        what = 'new'
        for i in range(TABLE_PLACES):
            if not img[top.at + 16 + 32 * i]:
                place = top.at + 16 + 32 * i
                break
        if place is None:
            sys.exit('build: the cabinet has no free place for %s (63 objects; put it in a drawer)' % name)
        top.count += 1
        struct.pack_into('<H', img, top.at + 6, top.count)
    img[used * SECTOR:used * SECTOR + sectors * SECTOR] = data + b'\0' * (sectors * SECTOR - len(data))
    img[place:place + 32] = (name.encode('latin-1').ljust(16, b'\0')
                             + struct.pack('<IIII', used, sectors, struct.unpack_from('<I', data, 0x4C)[0], 0))
    return '%s (%s, %d bytes, sector %d)' % (name, what, len(data), used)


SUITS = {'k_tools': 'Tools', 'k_usb12': 'USB12', 'k_net': 'Network', 'k_sound': 'Sound'}


def suits(img, tables):
    """the kernel suits of the cabinet: (name, where the DATA starts, its length)"""
    for t in tables:
        for e, name, lba, sectors, ident in t.entries(img):
            off = lba * SECTOR
            if object_size(img, off) and meta(img[off:off + object_size(img, off)], 'type') == 'kernel':
                yield name, off + struct.unpack_from('<Q', img, off + 0x10)[0], struct.unpack_from('<Q', img, off + 0x58)[0]


def suit_sources(nasm, img, tables, changed):
    """kernel/suits/NAME.kasm is the code of a suit: assembled and put into its object"""
    for name, data, length in list(suits(img, tables)):
        src = os.path.join('kernel', 'suits', SUITS.get(name, name) + '.kasm')
        if not os.path.exists(os.path.join(ROOT, src)):
            continue
        code = assemble(nasm, src, name + '.bin')
        size = struct.unpack_from('<Q', img, data + 72)[0]
        if len(code) != size:
            sys.exit('build: the suit %s is %d bytes now, its object holds %d - a suit of another size '
                     'cannot be put in yet (TODO.md)' % (name, len(code), size))
        if code != img[data + 96:data + 96 + size]:
            img[data + 96:data + 96 + size] = code
            changed.append('the suit %s (%s)' % (name, src.replace(os.sep, '/')))


def sign_suits(img, base, tables, seed, old_public):
    """a suit carries a signature over its slot, its size and its code: ours, since the key is ours"""
    done = 0
    for name, data, length in suits(img, tables):
        if not verify(old_public, bytes(base[data + 64:data + length]), bytes(base[data:data + 64])):
            print('build: the suit %s was not signed as expected in the base image - left as it is' % name)
            continue
        img[data:data + 64] = sign(seed, bytes(img[data + 64:data + length]))
        done += 1
    return done


def seal(img, base, tables, seed, old_public):
    """the Sentinel's list for this image, signed with our key; returns what it did"""
    sentinel = None
    for t in tables:
        for e, name, lba, sectors, ident in t.entries(img):
            if name == 'sentinel':
                sentinel = lba * SECTOR
    if sentinel is None:
        return 'no Sentinel list in this system - not signed'
    data = sentinel + struct.unpack_from('<Q', img, sentinel + 0x10)[0]
    length = struct.unpack_from('<Q', img, sentinel + 0x58)[0]
    body = bytes(base[data + 64:data + length])
    if body[:4] != b'NXSN' or not verify(old_public, body, bytes(base[data:data + 64])):
        return 'the Sentinel list of the base image is not as expected - left as it is'
    count = struct.unpack_from('<I', body, 4)[0]
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
    signature = sign(seed, bytes(new))
    if not verify(public_key(seed), bytes(new), signature):
        sys.exit('build: the signature just made does not check - not built')
    img[data:data + 64] = signature
    img[data + 64:data + length] = new
    return 'the Sentinel list: %d lines, %d written anew, %d left as they were; signed' % (count, fresh, kept)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=os.path.join(ROOT, 'disk.img'))
    ap.add_argument('--base', default=os.path.join(ROOT, 'build', 'base', 'disk_v2.9.59.img'))
    ap.add_argument('--keep-version', action='store_true', help='leave v2.9.59 in the texts of the kernel')
    ap.add_argument('--no-seal', action='store_true', help='do not sign: the Sentinel will call what changed CHANGED')
    a = ap.parse_args()

    if not os.path.exists(a.base):
        sys.exit('build: the base image is missing: ' + a.base)
    os.makedirs(WORK, exist_ok=True)
    base = open(a.base, 'rb').read()
    img = bytearray(base)
    nasm = find_nasm()
    changed = []

    boot = assemble(nasm, os.path.join('boot', 'Boot.kasm'), 'Boot.bin')
    if len(boot) != SECTOR or boot[510:512] != b'\x55\xAA':
        sys.exit('build: the boot sector must be 512 bytes that end in 55 AA')
    if boot != base[:SECTOR]:
        changed.append('the boot sector')
    img[0:SECTOR] = boot

    kernel = assemble(nasm, os.path.join('kernel', 'Kernel.kasm'), 'Kernel.bin')
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
    count = 0
    for row in csv.DictReader(open(table, encoding='utf-8-sig')):
        off = int(row['Offset'], 16)
        size = int(row['Size'])
        path = os.path.join(ROOT, row['Object'])
        if not os.path.exists(path):
            sys.exit('build: the object file is missing: ' + row['Object'])
        data = open(path, 'rb').read()
        if len(data) != size:
            sys.exit('build: %s is %d bytes, its place holds %d - put the new one into build/add/ instead'
                     % (row['Object'], len(data), size))
        if data[:4] != b'OMSA':
            sys.exit('build: %s is not an ASMO object (no OMSA at its start)' % row['Object'])
        if data != base[off:off + size]:
            changed.append(row['Object'])
        img[off:off + size] = data
        count += 1

    tables = all_tables(img)
    suit_sources(nasm, img, tables, changed)
    for path in sorted(glob.glob(os.path.join(ROOT, 'build', 'add', '*.asmo'))):
        changed.append('added: ' + add_object(img, tables, path))

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
        signed = sign_suits(img, base, tables, seed, old_public)
        sealed = '%d kernel suits signed; ' % signed + seal(img, base, tables, seed, old_public)

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
