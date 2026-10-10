#!/usr/bin/env python3
# table_copy.py - the two tables of the cabinet on a NinuxOS disk or image: look, and put the copy back.
#
#   python tools/table_copy.py check   disk.img            (or \\\\.\\PhysicalDriveN, as Administrator)
#   python tools/table_copy.py restore disk.img            the copy over the table - when the table is damaged
#
# From v3.0.24 the kernel writes the table of the cabinet twice: at sector 481 and, first, a copy
# right behind it (485). The loader reads only the first; if those sectors are lost the system
# does not start - this puts the copy back from another machine. (In the system itself `scan fix`
# makes a table anew from the objects it finds, but only a system that starts can run it.)

import struct
import sys

SECTOR = 512
TABLE = 481


def read(path):
    with open(path, 'rb') as f:
        f.seek(TABLE * SECTOR)
        return f.read(16 * SECTOR)


def look(t):
    """what a table says of itself: (is it a table, how many objects, its sectors)"""
    if t[:4] != b'CABN':
        return False, 0, 4
    return True, struct.unpack_from('<H', t, 6)[0], struct.unpack_from('<H', t, 8)[0]


def main():
    if len(sys.argv) != 3 or sys.argv[1] not in ('check', 'restore'):
        sys.exit(__doc__)
    data = read(sys.argv[2])
    ok, count, sectors = look(data)
    size = (sectors or 4) * SECTOR
    first, second = data[:size], data[size:2 * size]
    ok2, count2, _ = look(second)
    print('the table (sector %d): %s' % (TABLE, '%d objects' % count if ok else 'NOT a table'))
    print('the copy  (sector %d): %s' % (TABLE + size // SECTOR, '%d objects' % count2 if ok2 else 'not there'))
    if ok and ok2:
        print('they are the same' if first == second else 'they DIFFER (the copy is written first: it is the newer one)')
    if sys.argv[1] == 'check':
        return 0 if ok else 1
    if not ok2:
        sys.exit('restore: there is no copy to put back')
    with open(sys.argv[2], 'r+b') as f:
        f.seek(TABLE * SECTOR)
        f.write(second)
    print('restore: the copy was written over the table')
    return 0


if __name__ == '__main__':
    sys.exit(main())
