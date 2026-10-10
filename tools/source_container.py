#!/usr/bin/env python3
# source_container.py - the whole source of the project in one container that travels with every
# build, so that a stick alone is enough to get the project back (NinuxOS v3.0.0).
#
#   python tools/source_container.py pack                 -> build/source/NinuxOS_source.nxc
#   python tools/source_container.py check FILE           is it whole?
#   python tools/source_container.py unpack FILE [DIR]    take the files out (DIR: default ./NinuxOS_source)
#
# FILE can be the container itself, an image of a stick, or a stick: \\.\PhysicalDrive2
# (Administrator; turn USB write protection on first - see docs). Puffus writes the container onto
# the stick 1 GiB from its start, far behind the system; build_disk.py makes it at every build.
#
# The container: one sector of header, then a zip of every file git knows.
#   0   'NINUXSRC1', 0          8 bytes at 16: the length of the zip      32 bytes at 24: its SHA-256
#   64  the version, 0          96  the day it was made, 0
# It is checked (SHA-256), not secret: anyone who holds the stick can read it. Locking it with a
# passphrase is in TODO.md.

import datetime
import hashlib
import io
import os
import struct
import subprocess
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..'))
OUT = os.path.join(ROOT, 'build', 'source', 'NinuxOS_source.nxc')
MAGIC = b'NINUXSRC1\0'
SECTOR = 512
STICK_OFFSET = 1 << 30                  # where Puffus puts it on a stick


def version():
    try:
        return open(os.path.join(ROOT, 'VERSION')).read().strip()
    except OSError:
        return '?'


def tracked_files():
    try:
        r = subprocess.run(['git', '-C', ROOT, 'ls-files', '-z', '--cached', '--others', '--exclude-standard'],
                           capture_output=True)
        if r.returncode == 0 and r.stdout:
            return sorted(f for f in r.stdout.decode('utf-8').split('\0') if f)
    except OSError:
        pass
    found = []                              # no git here: every file, without what the tools make
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in ('.git', '__pycache__', 'work', 'out')]
        for f in files:
            found.append(os.path.relpath(os.path.join(base, f), ROOT).replace('\\', '/'))
    return sorted(found)


def pack(out=OUT):
    skip = os.path.relpath(out, ROOT).replace('\\', '/')
    buf = io.BytesIO()
    count = 0
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for f in tracked_files():
            path = os.path.join(ROOT, f)
            if f == skip or f.startswith('build/source/') or not os.path.isfile(path):
                continue
            z.write(path, f)
            count += 1
    data = buf.getvalue()
    head = bytearray(SECTOR)
    head[0:len(MAGIC)] = MAGIC
    struct.pack_into('<Q', head, 16, len(data))
    head[24:56] = hashlib.sha256(data).digest()
    v = ('NinuxOS v' + version()).encode()[:31]
    head[64:64 + len(v)] = v
    day = datetime.date.today().isoformat().encode()
    head[96:96 + len(day)] = day
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, 'wb') as f:
        f.write(head)
        f.write(data)
        f.write(b'\0' * (-len(data) % SECTOR))
    print('source: %d files, %d bytes -> %s' % (count, SECTOR + len(data), os.path.relpath(out, ROOT)))
    return out


def read(path):
    """the zip inside FILE, checked; looks at the start and 1 GiB in"""
    with open(path, 'rb', buffering=0) as f:
        for off in (0, STICK_OFFSET):
            try:
                f.seek(off)
                head = f.read(SECTOR)
            except OSError:
                continue
            if head[:len(MAGIC)] != MAGIC:
                continue
            length = struct.unpack_from('<Q', head, 16)[0]
            data = b''
            want = length + (-length % SECTOR)
            while len(data) < want:
                part = f.read(min(1 << 20, want - len(data)))
                if not part:
                    break
                data += part
            data = data[:length]
            if len(data) != length or hashlib.sha256(data).digest() != head[24:56]:
                sys.exit('source: the container at %d is damaged (its SHA-256 does not match)' % off)
            what = head[64:96].split(b'\0')[0].decode(errors='replace')
            day = head[96:128].split(b'\0')[0].decode(errors='replace')
            print('source: %s, made %s, %d bytes, whole' % (what, day, length))
            return data
    sys.exit('source: no container found in ' + path)


def main():
    a = sys.argv[1:]
    if a[:1] == ['pack']:
        pack()
    elif a[:1] == ['check'] and len(a) == 2:
        read(a[1])
    elif a[:1] == ['unpack'] and len(a) in (2, 3):
        data = read(a[1])
        to = a[2] if len(a) == 3 else 'NinuxOS_source'
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            z.extractall(to)
            print('source: %d files -> %s' % (len(z.namelist()), to))
    else:
        sys.exit(__doc__ or 'usage: source_container.py pack | check FILE | unpack FILE [DIR]')


if __name__ == '__main__':
    main()
