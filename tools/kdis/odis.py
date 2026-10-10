#!/usr/bin/env python3
# odis.py - turn a compiled ASMO / KASM object back into NASM source that assembles to the same bytes.
#
#   python tools/kdis/odis.py                     every compiled object of build/ that has code
#   python tools/kdis/odis.py build/objects/Desktop.asmo [more ...]
#
# writes  objects/NAME.asmo.kasm  (programs)   kernel/suits/NAME.kasm  (kernel suits)
#         tools/kdis/work/objects.txt           what was found in each
#
# An object says much more about itself than the kernel does: its header gives the places of
# DATA, META and the socket tables, the sockets are where code starts, and its table of
# relocations lists every place that holds an address. All of these become names in the source,
# so - unlike kernel/Kernel.kasm - lines can be added and removed: the header, the tables and the
# relocations follow. (An instruction that carries an address as a number is the exception; the
# report counts them.)

import os
import struct
import sys

import kdis

ROOT = kdis.ROOT
REPORT = os.path.join(kdis.WORK, 'objects.txt')
PROLOGUE = (0x53, 0x55, 0x41, 0x48, 0x50, 0x51, 0x52, 0x56, 0x57)


def q(b, at):
    return struct.unpack_from('<Q', b, at)[0]


def meta(b, key):
    for part in b[q(b, 0x18):q(b, 0x18) + 4096].split(b'\0'):
        if not part:
            break
        if part.startswith(key.encode() + b':'):
            return part[len(key) + 1:].decode('latin-1')
    return ''


def table(b, at, step=8):
    out = []
    while at and at + 8 <= len(b) and q(b, at):
        out.append((at, q(b, at)))
        at += step
    return out, at


def disassemble(path, out):
    b = open(path, 'rb').read()
    size = len(b)
    if b[:4] != b'OMSA' or q(b, 8) != size:
        return None
    os.makedirs(kdis.WORK, exist_ok=True)
    sec = kdis.Section('obj', 0, 0, size)
    with open(sec.file, 'wb') as f:
        f.write(b)
    kdis.image = b
    kdis.SECTIONS = [sec]
    kdis.FAR = {}
    kdis.DIRECTIVES = {'obj': 'org 0'}
    kdis.BLOBS = (os.path.join(os.path.dirname(out), 'data'), os.path.basename(out).split('.')[0])
    name = meta(b, 'name') or os.path.basename(path)
    kdis.HEADER = [
        '; %s - the object "%s" (type %s) of NinuxOS v2.9.59 as NASM source.' % (os.path.basename(out), name, meta(b, 'type')),
        '; Made from the compiled object by tools/kdis/odis.py; it assembles to the same %d bytes:' % size,
        ';   nasm -f bin -I %s/ %s -o %s   (run where the file is)' % ('.', os.path.basename(out), os.path.basename(path)),
        ';',
        '; obj_data, obj_meta, obj_system, obj_named, obj_prockets, obj_relocs: the parts of the object.',
        '; sock_N a socket; fn_ a function; L_ a place jumped to; d_ data; p_ what an address points at;',
        '; r_ a place that holds an address (the table of relocations at the end lists them).',
        '',
    ]
    pointers, given, seeds = {}, {}, []
    given[size] = 'obj_end'
    pointers[0x08] = (8, size, 0)
    pointers[size - 16] = (8, size, 0)
    for at, label in ((0x10, 'obj_data'), (0x18, 'obj_meta'), (0x20, 'obj_system'), (0x28, 'obj_named'),
                      (0x30, 'obj_prockets'), (0x60, 'obj_relocs')):
        if 0 < q(b, at) < size:
            pointers[at] = (8, q(b, at), 0)
            given.setdefault(q(b, at), label)
    system, _ = table(b, q(b, 0x20))
    named, _ = table(b, q(b, 0x28))
    prockets, _ = table(b, q(b, 0x30), 16)
    names = [s for s in meta(b, 'sockets').split(',') if s]
    for i, (at, target) in enumerate(system):
        pointers[at] = (8, target, 0)
        seeds.append(target)
    for i, (at, target) in enumerate(named):
        pointers[at] = (8, target, 0)
        seeds.append(target)
        given.setdefault(target, 'sock_' + (names[i] if i < len(names) else str(i)))
    for i, (at, target) in enumerate(prockets):
        pointers[at] = (8, target, 0)
        seeds.append(target)
        given.setdefault(target, 'procket_%d' % i)
    relocs = []
    r = q(b, 0x60)
    if 0 < r < size:
        count = struct.unpack_from('<I', b, r)[0]
        for i in range(count):
            e = struct.unpack_from('<I', b, r + 4 + 4 * i)[0]
            place, wide = e & 0x7FFFFFFF, not e & 0x80000000
            if place + (8 if wide else 4) > size:
                continue
            value = q(b, place) if wide else struct.unpack_from('<I', b, place)[0]
            relocs.append((r + 4 + 4 * i, place, wide, value, e & 0x80000000))
    for entry, place, wide, value, flag in relocs:
        if value <= size:
            pointers[place] = (8 if wide else 4, value, 0)
    kdis.POINTERS = pointers
    kdis.GIVEN = given

    k = kdis.Kernel()
    for s in seeds:
        if s < size:
            k.follow(s, 64)
    grew = True
    while grew:                                 # what an address points at may be a function too
        grew = False
        for entry, place, wide, value, flag in relocs:
            if value < size and k.owner[value] == 0 and b[value] in PROLOGUE:
                before = len(k.code)
                k.follow(value, 64)
                grew = grew or len(k.code) > before
    in_code = 0
    for place in list(pointers):
        if place < size and k.owner[place]:     # the address is inside an instruction: stays a number
            del pointers[place]
            in_code += 1
    # the table of relocations itself: every line names the place it speaks of
    for entry, place, wide, value, flag in relocs:
        if place < size:
            pointers[entry] = (4, place, flag)
            given.setdefault(place, 'r_%05x' % place)
    kdis.POINTERS = pointers
    kdis.GIVEN = given

    w = kdis.Writer(k)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    rounds = 0
    while True:
        rounds += 1
        w.write(out)
        n, what = kdis.verify(w, out)
        if n == 0 or rounds > 40:
            break
    w.write(out)
    built, lst, errors, stderr = kdis.assemble(out)
    same = not errors and open(built, 'rb').read() == b
    code = sum(1 for x in k.owner if x)
    ins = [it for items in w.items for it in items if it.code]
    kept = sum(1 for it in ins if it.fallback)
    return dict(name=name, kind=meta(b, 'type'), size=size, same=same, code=code, ins=len(ins), kept=kept,
                funcs=len(k.calls), relocs=len(relocs), in_code=in_code, out=os.path.relpath(out, ROOT))


def suit_code(b):
    """a kernel suit: its DATA is 64 bytes of signature, the slot it runs at, its size, 16 zero bytes, the code"""
    d = b[q(b, 0x10):q(b, 0x10) + q(b, 0x58)]
    slot, size = struct.unpack_from('<QQ', d, 64)
    return slot, d[96:96 + size]


def suit(path, out):
    """the code of a kernel suit as source: it runs at a fixed place and calls the kernel by name"""
    b = open(path, 'rb').read()
    slot, code = suit_code(b)
    size = len(code)
    os.makedirs(kdis.WORK, exist_ok=True)
    sec = kdis.Section('suit', slot, 0, size)
    with open(sec.file, 'wb') as f:
        f.write(code)
    kdis.image = code
    kdis.SECTIONS = [sec]
    kdis.FAR = {}
    kdis.BLOBS = None
    kdis.DIRECTIVES = {'suit': 'org 0x%X' % slot}
    name = meta(b, 'name')
    kdis.HEADER = [
        '; %s - the kernel suit %s of NinuxOS v2.9.59 as NASM source: %d bytes of kernel code that' % (os.path.basename(out), name, size),
        '; run at 0x%X. Made by tools/kdis/odis.py; it assembles to the same bytes:' % slot,
        ';   nasm -f bin -I kernel/suits/ %s -o %s.bin' % (os.path.basename(out), name),
        '; The build puts the code into the object %s (64 bytes of signature, the slot, the size, the' % name,
        '; code) and signs it. The names fn_0xxxx, L_0xxxx, d_0xxxx are the kernel\'s (Kernel.sym.inc).',
        '',
        '%include "../Kernel.sym.inc"',
        '',
    ]
    external = {}
    sym = os.path.join(ROOT, 'kernel', 'Kernel.sym.inc')
    if os.path.exists(sym):
        for line in open(sym):
            f = line.split()
            if len(f) == 3 and f[1] == 'equ':
                external.setdefault(int(f[2], 16), f[0])
    kdis.EXTERNAL = external
    pointers, given, seeds = {}, {slot: 'suit_start'}, []
    at = 0x20                                   # after the mark, the size and the name: where the kernel comes in
    while at + 8 <= size and slot <= q(code, at) < slot + size:
        pointers[slot + at] = (8, q(code, at), 0)
        seeds.append(q(code, at))
        given.setdefault(q(code, at), 'entry_%02d' % ((at - 0x20) // 8))
        at += 8
    given.setdefault(slot + at, 'suit_table_end')
    kdis.POINTERS = pointers
    kdis.GIVEN = given
    k = kdis.Kernel()
    for s in seeds:
        k.follow(s, 64)
    w = kdis.Writer(k)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    rounds = 0
    while True:
        rounds += 1
        w.write(out)
        n, what = kdis.verify(w, out)
        if n == 0 or rounds > 40:
            break
    w.write(out)
    built, lst, errors, stderr = kdis.assemble(out)
    same = not errors and open(built, 'rb').read() == code
    ins = [it for items in w.items for it in items if it.code]
    kdis.EXTERNAL = {}
    return dict(name=name, kind='suit', size=size, same=same, code=sum(1 for x in k.owner if x), ins=len(ins),
                kept=sum(1 for it in ins if it.fallback), funcs=len(k.calls), relocs=len(seeds), in_code=0,
                out=os.path.relpath(out, ROOT))


def targets():
    found = []
    for folder, where, ending in (('build/objects', 'objects', '.asmo.kasm'), ('build/kernel', 'kernel/suits', '.kasm')):
        d = os.path.join(ROOT, folder)
        for f in sorted(os.listdir(d)):
            p = os.path.join(d, f)
            b = open(p, 'rb').read(0x70)
            if b[:4] != b'OMSA' or struct.unpack_from('<Q', b, 0x38)[0] != 1:
                continue
            if folder == 'build/kernel':
                found.append((p, os.path.join(ROOT, where, f.rsplit('.', 1)[0] + ending)))
                continue
            base = f.rsplit('.', 1)[0]
            found.append((p, os.path.join(ROOT, where, base + ending)))
    return found


def main():
    wanted = [os.path.abspath(a) for a in sys.argv[1:]]
    jobs = [j for j in targets() if not wanted or j[0] in wanted]
    lines = []
    for path, out in jobs:
        b = open(path, 'rb').read()
        if b[:4] != b'OMSA':
            continue
        if meta(b, 'type') == 'kernel':
            r = suit(path, out)
        else:
            # an object with nothing but stubs for sockets has no code worth a source
            first = q(b, q(b, 0x28)) if 0 < q(b, 0x28) < len(b) else 0
            if not first and not (0 < q(b, 0x60) < len(b)):
                continue
            r = disassemble(path, out)
        if r is None:
            continue
        line = '%-22s %-8s %8d bytes  %s  code %5.1f%%  %6d instructions (%d as bytes)  %4d functions  ' \
               '%5d relocations (%d inside instructions)' % (
                   r['name'], r['kind'], r['size'], 'SAME' if r['same'] else 'DIFFERENT', 100.0 * r['code'] / r['size'],
                   r['ins'], r['kept'], r['funcs'], r['relocs'], r['in_code'])
        print(line)
        lines.append(line + '  -> ' + r['out'])
    with open(REPORT, 'w') as f:
        f.write('\n'.join(lines) + '\n')


if __name__ == '__main__':
    main()
