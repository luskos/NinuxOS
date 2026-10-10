#!/usr/bin/env python3
# sheet.py - many pictures of the screen on one sheet, small, to be looked at in one go.
#
#   python tools/qemu/sheet.py OUT.png PICTURE.png [PICTURE.png ...]   (5 in a row, a quarter of the size)
#
# The test scripts leave a picture for every program; looking at forty of them one by one is
# slow. No extra packages: PNG is read and written here (8 bits, RGB or RGBA, not interlaced).

import struct
import sys
import zlib


def read(path):
    d = open(path, 'rb').read()
    pos = 8
    data = b''
    while pos < len(d):
        n, kind = struct.unpack('>I4s', d[pos:pos + 8])
        body = d[pos + 8:pos + 8 + n]
        if kind == b'IHDR':
            w, h, bits, colour = struct.unpack('>IIBB', body[:10])
        elif kind == b'IDAT':
            data += body
        pos += 12 + n
    bpp = {2: 3, 6: 4}[colour]
    raw = zlib.decompress(data)
    stride = w * bpp
    rows = []
    prev = bytearray(stride)
    p = 0
    for y in range(h):
        f = raw[p]
        line = bytearray(raw[p + 1:p + 1 + stride])
        p += 1 + stride
        if f == 1:
            for i in range(bpp, stride):
                line[i] = (line[i] + line[i - bpp]) & 255
        elif f == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 255
        elif f == 3:
            for i in range(stride):
                a = line[i - bpp] if i >= bpp else 0
                line[i] = (line[i] + ((a + prev[i]) >> 1)) & 255
        elif f == 4:
            for i in range(stride):
                a = line[i - bpp] if i >= bpp else 0
                b = prev[i]
                c = prev[i - bpp] if i >= bpp else 0
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                line[i] = (line[i] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        rows.append(line)
        prev = line
    return w, h, bpp, rows


def write(path, w, h, rows):
    raw = b''.join(b'\0' + bytes(r) for r in rows)

    def chunk(kind, body):
        return struct.pack('>I', len(body)) + kind + body + struct.pack('>I', zlib.crc32(kind + body))
    open(path, 'wb').write(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
                           + chunk(b'IDAT', zlib.compress(raw, 6)) + chunk(b'IEND', b''))


def main():
    out, pics = sys.argv[1], sys.argv[2:]
    cols = 5
    step = 4
    tw, th = 1024 // step, 768 // step
    gap = 4
    n_rows = (len(pics) + cols - 1) // cols
    W = cols * (tw + gap) + gap
    H = n_rows * (th + gap) + gap
    sheet = [bytearray(b'\x40\x40\x40' * W) for _ in range(H)]
    for k, path in enumerate(pics):
        w, h, bpp, rows = read(path)
        x0 = gap + (k % cols) * (tw + gap)
        y0 = gap + (k // cols) * (th + gap)
        for y in range(min(th, h // step)):
            src = rows[y * step]
            line = sheet[y0 + y]
            for x in range(min(tw, w // step)):
                o = x * step * bpp
                line[(x0 + x) * 3:(x0 + x) * 3 + 3] = src[o:o + 3]
    write(out, W, H, sheet)
    print('sheet: %d pictures -> %s (%d x %d)' % (len(pics), out, W, H))


if __name__ == '__main__':
    main()
