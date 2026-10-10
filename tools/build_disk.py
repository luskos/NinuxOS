#!/usr/bin/env python3
# build_disk.py - make disk.img from the project (NinuxOS v3.0.0).
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
CORE_SIZE = 61968                       # the core; the extension (checked by SHA-256) follows it
KERNEL_SAYS = b'v2.9.59'                # the version written in the kernel's texts


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
    ap.add_argument('--keep-version', action='store_true', help='leave v2.9.59 in the texts of the kernel')
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
    # the version of the project (the file VERSION) goes into the texts of the core: the line the
    # loader shows, the line at the top of the shell, 'info'. Only the core: the extension has a
    # SHA-256 check and keeps its bytes (so 'machine' and Setup still say v2.9.59).
    stamped = 0
    kernel_changed = kernel != base[SECTOR:SECTOR + len(kernel)]
    version = ('v' + open(os.path.join(ROOT, 'VERSION')).read().strip()).encode()
    if not a.keep_version and not kernel_changed:
        if len(version) != len(KERNEL_SAYS):
            print('build: VERSION must be as long as %s (3.0.03) - the version is not stamped' % KERNEL_SAYS.decode())
        elif version != KERNEL_SAYS:
            core = kernel[:CORE_SIZE]
            stamped = core.count(KERNEL_SAYS)
            kernel = core.replace(KERNEL_SAYS, version) + kernel[CORE_SIZE:]
    if kernel_changed:
        changed.append('the kernel')
    elif stamped:
        changed.append('the version in the kernel (%s, %d places)' % (version.decode(), stamped))
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
    try:                                    # the whole source goes with every build
        import source_container
        source_container.pack()
    except Exception as e:
        print('build: the source container was not made (%s)' % e)
    print('build: boot sector %d bytes, kernel %d bytes, %d objects' % (len(boot), len(kernel), count))
    print('build: %s  %d bytes  SHA-256 %s' % (a.out, len(img), hashlib.sha256(img).hexdigest()))
    if stamped:
        print('build: the system says %s now. The Sentinel will list @kernel as CHANGED (its list was' % version.decode())
        print('       signed for v2.9.59); if the system refuses more than that, build with --keep-version.')
    if not changed:
        print('build: the same as the base image (v2.9.59)')
    else:
        print('build: different from the base image: ' + ', '.join(changed))
        if kernel_changed:
            print('build: WARNING - the kernel has other bytes. Nothing signs it yet: it will fail its own')
            print('       SHA-256 check (system operations off) and the Sentinel will call it CHANGED.')
        objects_changed = [c for c in changed if c.endswith('.asmo') or c.endswith('.kasm')]
        if objects_changed:
            print('build: WARNING - a changed system object is CHANGED for the Sentinel until it is accepted')
            print("       on the machine ('sentinel trust NAME', administrator).")
    return 0


if __name__ == '__main__':
    sys.exit(main())
