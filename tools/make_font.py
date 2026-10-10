#!/usr/bin/env python3
# make_font.py - the letters of the system from a .ttf: the object `font` (NinuxOS v3.0.11).
#
#   python tools/make_font.py Exo-Regular            look at build/font/preview.txt
#   python tools/make_font.py Exo-Medium --use       ... and the next build puts it in
#   python tools/make_font.py C:\path\Some.ttf --height 14 --weight 600
#   python tools/make_font.py --back                 the letters v2.9.59 came with again
#
# The object `font` is 256 letters of 8 x 16 dots, a byte a row, the left dot the highest bit,
# in the order of Windows-1251 (Latin and Cyrillic). This draws every letter of that order with
# Windows' own renderer (GDI, no extra packages) and packs it. The codes that are no letters
# (below 32, 127 .. 159) stay as the present font has them.
#
# A name is looked for in assets/fonts/*.zip (Exo, JetBrains Mono, Russo One are there); a path
# to a .ttf works too. A font whose letters have different widths (Exo) is made to fit the cell:
# a letter wider than 8 dots is drawn narrower until it fits, a narrow one stands in the middle.
#
# Without --use nothing in the system changes: the object is written to build/font/font.asmo
# with a preview beside it. With --use it also goes to build/add/font.asmo, and the build puts
# every object of build/add into the cabinet in the place of the one with its name.

import argparse
import ctypes
import glob
import os
import shutil
import struct
import sys
import zipfile
from ctypes import wintypes

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..'))
OUT = os.path.join(ROOT, 'build', 'font')
sys.path.insert(0, HERE)
import build_disk                                                   # noqa: E402

CELL_W, CELL_H = 8, 16
CANVAS = 48                             # a letter is drawn in the middle of a square this big


def find_font(what):
    """a path to a .ttf, or a name looked for in the zips of assets/fonts -> the path of the .ttf"""
    if os.path.exists(what):
        return what
    key = what.lower().replace(' ', '').replace('.ttf', '')
    for z in sorted(glob.glob(os.path.join(ROOT, 'assets', 'fonts', '*.zip'))):
        with zipfile.ZipFile(z) as f:
            names = [n for n in f.namelist() if n.lower().endswith('.ttf')]
            for n in names:
                if os.path.basename(n).lower().replace('.ttf', '') == key:
                    os.makedirs(OUT, exist_ok=True)
                    path = os.path.join(OUT, os.path.basename(n))
                    with open(path, 'wb') as o:
                        o.write(f.read(n))
                    return path
    sys.exit('make_font: no font "%s" (a path to a .ttf, or one of assets/fonts: Exo-Regular, '
             'JetBrainsMono-Regular, RussoOne-Regular ...)' % what)


def face_name(path):
    """the name of the family, read from the .ttf"""
    d = open(path, 'rb').read()
    tables = struct.unpack_from('>H', d, 4)[0]
    for i in range(tables):
        tag, _, off, length = struct.unpack_from('>4sIII', d, 12 + 16 * i)
        if tag != b'name':
            continue
        count, strings = struct.unpack_from('>HH', d, off + 2)
        best = None
        for j in range(count):
            platform, enc, lang, name_id, n, at = struct.unpack_from('>6H', d, off + 6 + 12 * j)
            if name_id != 1:
                continue
            raw = d[off + strings + at:off + strings + at + n]
            if platform == 3:
                return raw.decode('utf-16-be')
            best = raw.decode('latin-1')
        if best:
            return best
    sys.exit('make_font: %s has no name in it' % path)


class Drawer:
    """letters drawn by Windows into a small picture that can be read dot by dot"""

    def __init__(self, path, face, height, weight):
        self.gdi = ctypes.WinDLL('gdi32')
        self.user = ctypes.WinDLL('user32')
        self.gdi.CreateFontW.restype = wintypes.HANDLE
        self.gdi.CreateCompatibleDC.restype = wintypes.HANDLE
        self.gdi.CreateDIBSection.restype = wintypes.HANDLE
        self.gdi.SelectObject.restype = wintypes.HANDLE
        self.gdi.SelectObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
        self.gdi.DeleteObject.argtypes = [wintypes.HANDLE]
        self.gdi.TextOutW.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_int, wintypes.LPCWSTR, ctypes.c_int]
        self.gdi.CreateDIBSection.argtypes = [wintypes.HANDLE, ctypes.c_void_p, wintypes.UINT,
                                              ctypes.POINTER(ctypes.c_void_p), wintypes.HANDLE, wintypes.DWORD]
        for f in (self.gdi.SetTextColor, self.gdi.SetBkColor, self.gdi.GetTextMetricsW, self.gdi.PatBlt):
            f.argtypes = None
        if not self.gdi.AddFontResourceExW(path, 0x10, 0):          # for this program only
            sys.exit('make_font: Windows does not take %s as a font' % path)
        self.face, self.height, self.weight = face, height, weight
        self.dc = self.gdi.CreateCompatibleDC(None)
        header = struct.pack('<IiiHHIIiiII', 40, CANVAS, -CANVAS, 1, 32, 0, 0, 0, 0, 0, 0)
        self.bits = ctypes.c_void_p()
        self.bitmap = self.gdi.CreateDIBSection(self.dc, header, 0, ctypes.byref(self.bits), None, 0)
        self.gdi.SelectObject(self.dc, self.bitmap)
        self.gdi.SetTextColor(wintypes.HANDLE(self.dc), 0xFFFFFF)
        self.gdi.SetBkColor(wintypes.HANDLE(self.dc), 0)
        self.fonts = {}
        self.ascent = self.metrics(0)[0]

    def font(self, width):
        if width not in self.fonts:
            # height in dots of the letters' cell, no smoothing: a dot is on or off
            self.fonts[width] = self.gdi.CreateFontW(self.height, width, 0, 0, self.weight, 0, 0, 0, 1, 0, 0, 3, 0, self.face)
        return self.fonts[width]

    def metrics(self, width):
        self.gdi.SelectObject(self.dc, self.font(width))
        tm = (ctypes.c_long * 20)()
        self.gdi.GetTextMetricsW(wintypes.HANDLE(self.dc), tm)
        return tm[1], tm[2], tm[5]                                  # ascent, descent, the usual width

    def letter(self, ch, width):
        """the dots of one letter: rows of CANVAS booleans, the base line at row CANVAS // 2"""
        self.gdi.SelectObject(self.dc, self.font(width))
        ctypes.memset(self.bits, 0, CANVAS * CANVAS * 4)
        self.gdi.TextOutW(self.dc, CANVAS // 4, CANVAS // 2 - self.metrics(width)[0], ch, 1)
        raw = ctypes.string_at(self.bits, CANVAS * CANVAS * 4)
        return [[raw[(y * CANVAS + x) * 4 + 1] > 127 for x in range(CANVAS)] for y in range(CANVAS)]


def fit(drawer, ch, top):
    """the 16 bytes of one letter: as wide as it comes if that is 8 dots or less, else narrower"""
    usual = drawer.metrics(0)[2]
    for width in [0] + list(range(min(usual, 9), 2, -1)):
        dots = drawer.letter(ch, width)
        columns = [x for x in range(CANVAS) if any(dots[y][x] for y in range(CANVAS))]
        if not columns:
            return bytes(CELL_H)
        left, wide = columns[0], columns[-1] - columns[0] + 1
        if wide <= CELL_W:
            break
    shift = left - (CELL_W - wide + 1) // 2
    rows = []
    for r in range(CELL_H):
        y = top + r
        b = 0
        for x in range(CELL_W):
            if 0 <= y < CANVAS and 0 <= shift + x < CANVAS and dots[y][shift + x]:
                b |= 0x80 >> x
        rows.append(b)
    return bytes(rows)


def preview(data, lines):
    out = []
    for line in lines:
        codes = line.encode('cp1251', 'replace')
        for r in range(CELL_H):
            out.append(''.join(''.join('#' if data[c * 16 + r] & (0x80 >> x) else ' ' for x in range(8)) for c in codes).rstrip())
        out.append('')
    return '\n'.join(out) + '\n'


def main():
    ap = argparse.ArgumentParser(description='the object font from a .ttf')
    ap.add_argument('font', nargs='?', help='a .ttf, or the name of one in assets/fonts (Exo-Regular)')
    ap.add_argument('--height', type=int, default=0, help='the height of the font in dots (default: the biggest that fits 16)')
    ap.add_argument('--weight', type=int, default=400, help='400 ordinary, 500 medium, 700 bold')
    ap.add_argument('--use', action='store_true', help='also write build/add/font.asmo: the next build puts it in')
    ap.add_argument('--back', action='store_true', help='take build/add/font.asmo away: the letters of v2.9.59 again')
    a = ap.parse_args()
    used = os.path.join(ROOT, 'build', 'add', 'font.asmo')
    if a.back:
        if os.path.exists(used):
            os.remove(used)
        print('make_font: the next build has the letters v2.9.59 came with')
        return 0
    if not a.font:
        ap.error('which font?')
    if os.name != 'nt':
        sys.exit('make_font: the letters are drawn by Windows (GDI); on another system this is still to be written')
    path = find_font(a.font)
    face = face_name(path)
    old = open(os.path.join(ROOT, 'build', 'objects', 'font.asmo'), 'rb').read()
    data = bytearray(build_disk.object_data(old))
    if len(data) != 256 * CELL_H:
        sys.exit('make_font: build/objects/font.asmo is not 256 letters of 16 rows')

    height = a.height
    if not height:                      # the biggest whose tallest and deepest letters fit the 16 rows
        for height in range(20, 7, -1):
            d = Drawer(path, face, height, a.weight)
            ascent, descent, _ = d.metrics(0)
            if ascent + descent <= CELL_H:
                break
    d = Drawer(path, face, height, a.weight)
    ascent, descent, usual = d.metrics(0)
    top = CANVAS // 2 - ascent - max(0, (CELL_H - ascent - descent) // 2)
    made = 0
    for code in list(range(32, 127)) + list(range(160, 256)):
        try:
            ch = bytes([code]).decode('cp1251')
        except UnicodeDecodeError:
            continue
        data[code * 16:code * 16 + 16] = fit(d, ch, top)
        made += 1

    os.makedirs(OUT, exist_ok=True)
    obj = build_disk.make_object(bytes(data), [
        'type:font', 'name:font', 'kind:font',
        "data:the system's letters: 256 x 8x16 pixels, Windows-1251 (Latin + Cyrillic), %s" % face,
        'desktop:no', 'made:make_font.py'])
    out = os.path.join(OUT, 'font.asmo')
    open(out, 'wb').write(obj)
    show = os.path.join(OUT, 'preview.txt')
    with open(show, 'w', encoding='utf-8') as f:
        f.write('%s, %d dots high (ascent %d, descent %d, usual width %d), weight %d\n\n'
                % (face, height, ascent, descent, usual, a.weight))
        f.write(preview(data, ['NinuxOS v3 ninux> help', 'The quick brown fox, 0123456789',
                               'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz',
                               '\u0410\u0411\u0412\u0413\u0414\u0415\u0416\u0417 \u0430\u0431\u0432\u0433\u0434\u0435\u0436\u0437 \u0449\u044a\u044e\u044f',
                               '!@#$%^&*()[]{}<>/\\|;:\'",.?-_=+']))
    print('make_font: %s, %d dots high, %d letters -> %s' % (face, height, made, os.path.relpath(out, ROOT)))
    print('make_font: how it looks: %s' % os.path.relpath(show, ROOT))
    if a.use:
        os.makedirs(os.path.dirname(used), exist_ok=True)
        shutil.copyfile(out, used)
        print('make_font: build/add/font.asmo written - the next build puts these letters into the system')
    else:
        print('make_font: nothing in the system changed (--use for that)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
