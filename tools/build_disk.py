#!/usr/bin/env python3
# build_disk.py - make disk.img from the project (NinuxOS v2.9.60).
#
#   python tools/build_disk.py [--out disk.img] [--base build/base/disk_v2.9.59.img]
#
# What it does:
#   1. assembles boot/Boot.kasm (the boot sector) and kernel/Kernel.kasm (core + extension) with nasm
#   2. takes the base image - the system as it came off the stick - and puts into it
#        the boot sector            at sector 0
#        the kernel                 from sector 1 (480 sectors are kept for it)
#        every object of build/     at the place docs/cabinet_objects.csv gives it
#   3. writes disk.img and says what is different from the base
#
# What it does not do yet (see TODO.md):
#   - an object of another size, a new object: the table of the cabinet is not understood yet,
#     so an object can only be replaced by one of the same length
#   - sign anything: a kernel with other bytes fails its own SHA-256 check ("system operations
#     off") and the Sentinel calls a changed system object CHANGED
# With nothing changed in the project the result is the base image, byte for byte.

import argparse
import csv
import hashlib
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..'))
WORK = os.path.join(ROOT, 'build', 'work')

SECTOR = 512
KERNEL_SECTORS = 480                    # boot/Boot.kasm: kernel_sectors
KERNEL_ROOM = KERNEL_SECTORS * SECTOR


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
    r = subprocess.run([nasm, '-f', 'bin', '-w-all', '-o', out, os.path.join(ROOT, src)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit('build: nasm stopped on %s\n%s' % (src, r.stderr[:4000]))
    return open(out, 'rb').read()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=os.path.join(ROOT, 'disk.img'))
    ap.add_argument('--base', default=os.path.join(ROOT, 'build', 'base', 'disk_v2.9.59.img'))
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
    kernel_changed = kernel != base[SECTOR:SECTOR + len(kernel)]
    if kernel_changed:
        changed.append('the kernel')
    img[SECTOR:SECTOR + len(kernel)] = kernel

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
            sys.exit('build: %s is %d bytes, its place in the cabinet holds %d - an object of another '
                     'size cannot be put in yet (TODO.md)' % (row['Object'], len(data), size))
        if data[:4] != b'OMSA':
            sys.exit('build: %s is not an ASMO object (no OMSA at its start)' % row['Object'])
        if data != base[off:off + size]:
            changed.append(row['Object'])
        img[off:off + size] = data
        count += 1

    with open(a.out, 'wb') as f:
        f.write(img)
    print('build: boot sector %d bytes, kernel %d bytes, %d objects' % (len(boot), len(kernel), count))
    print('build: %s  %d bytes  SHA-256 %s' % (a.out, len(img), hashlib.sha256(img).hexdigest()))
    if not changed:
        print('build: the same as the base image (v2.9.59)')
    else:
        print('build: different from the base image: ' + ', '.join(changed))
        if kernel_changed:
            print('build: WARNING - the kernel has other bytes. Nothing signs it yet: it will fail its own')
            print('       SHA-256 check (system operations off) and the Sentinel will call it CHANGED.')
        if len(changed) > (2 if kernel_changed else 1) or (changed and not kernel_changed and changed != ['the boot sector']):
            print('build: WARNING - a changed system object is CHANGED for the Sentinel until it is accepted')
            print("       on the machine ('sentinel trust NAME', administrator).")
    return 0


if __name__ == '__main__':
    sys.exit(main())
