import os
import struct
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, HERE)
from underground_block_builder import read_png

DIR = os.path.join(REPO, 'res', 'graphics', 'underground_top_screen')
FULL = os.path.join(DIR, 'background_full.png')
TILES = os.path.join(DIR, 'background_tiles.png')
NSCR = os.path.join(DIR, 'background.NSCR')
ZOOM = os.path.join(DIR, 'zoom_full.png')
BASE = os.path.join(DIR, 'background_full_original.png')
FIRST_EXTRA_BANK = 2
EXTRA_BANKS = 8
ZOOM_MAP = os.path.join(DIR, 'zoom_map.bin')
ZOOM_SIZE = 60
MAX_TILES = 320


def png_palette(path):
    d = open(path, 'rb').read()
    pos = 8
    while pos < len(d):
        ln, = struct.unpack('>I', d[pos:pos + 4])
        if d[pos + 4:pos + 8] == b'PLTE':
            p = d[pos + 8:pos + 8 + ln]
            return [tuple(p[i:i + 3]) for i in range(0, len(p), 3)]
        pos += 12 + ln
    return None


def png_indices(path):
    d = open(path, 'rb').read()
    pos = 8
    idat = b''
    while pos < len(d):
        ln, = struct.unpack('>I', d[pos:pos + 4])
        typ = d[pos + 4:pos + 8]
        data = d[pos + 8:pos + 8 + ln]
        pos += 12 + ln
        if typ == b'IHDR':
            w, h, bd, ct = struct.unpack('>IIBB', data[:10])
        elif typ == b'IDAT':
            idat += data
    if ct != 3:
        raise SystemExit('%s must be an indexed (palette) PNG' % os.path.basename(path))
    raw = zlib.decompress(idat)
    stride = (w * bd + 7) // 8
    rows, prev, off = [], bytearray(stride), 0
    for _ in range(h):
        ft = raw[off]
        line = bytearray(raw[off + 1:off + 1 + stride])
        off += 1 + stride
        for i in range(stride):
            left = line[i - 1] if i >= 1 else 0
            up = prev[i]
            ul = prev[i - 1] if i >= 1 else 0
            if ft == 1:
                line[i] = (line[i] + left) & 255
            elif ft == 2:
                line[i] = (line[i] + up) & 255
            elif ft == 3:
                line[i] = (line[i] + (left + up) // 2) & 255
            elif ft == 4:
                p = left + up - ul
                pa, pb, pc = abs(p - left), abs(p - up), abs(p - ul)
                line[i] = (line[i] + (left if pa <= pb and pa <= pc else (up if pb <= pc else ul))) & 255
        rows.append(line)
        prev = line
    per = 8 // bd
    out = []
    for line in rows:
        out.append([(line[x // per] >> (8 - bd * (x % per + 1))) & ((1 << bd) - 1) for x in range(w)])
    return w, h, out


def write_png(path, w, h, rows, palette):
    def chunk(t, data):
        return struct.pack('>I', len(data)) + t + data + struct.pack('>I', zlib.crc32(t + data) & 0xffffffff)
    raw = b''.join(b'\x00' + bytes(r) for r in rows)
    out = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 3, 0, 0, 0))
    out += chunk(b'PLTE', b''.join(bytes(c) for c in palette)) + chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b'')
    open(path, 'wb').write(out)


def ds(c):
    return (c[0] >> 3, c[1] >> 3, c[2] >> 3)


def main():
    base = png_palette(BASE)[:16]
    base += [(0, 0, 0)] * (16 - len(base))
    base_index = {}
    for i, c in enumerate(base):
        base_index.setdefault(ds(c), i)
    backdrop = ds(base[0])
    w, h, rgb = read_png(FULL)
    if (w, h) != (256, 192):
        raise SystemExit('background_full.png must be 256x192')
    cells = {}
    for ty in range(24):
        for tx in range(32):
            cells[(tx, ty)] = [ds(rgb[ty * 8 + y][tx * 8 + x][:3]) for y in range(8) for x in range(8)]
    extra = [(tx, ty) for (tx, ty), px in cells.items() if not set(px) <= set(base_index)]
    banks = []
    assigned = {}
    for key in sorted(extra, key=lambda k: -len(set(cells[k]) - {backdrop})):
        need = set(cells[key]) - {backdrop}
        if len(need) > 15:
            raise SystemExit('the 8x8 tile at pixel (%d, %d) uses %d colours; one tile can use at most 15 plus black'
                             % (key[0] * 8, key[1] * 8, len(need)))
        for b, cols in enumerate(banks):
            if len(cols | need) <= 15:
                cols |= need
                assigned[key] = b
                break
        else:
            if len(banks) == EXTRA_BANKS:
                raise SystemExit('the picture needs more than %d extra palettes' % EXTRA_BANKS)
            banks.append(set(need))
            assigned[key] = len(banks) - 1
    bank_lists = [[backdrop] + sorted(cols) for cols in banks]

    tiles = [tuple([0] * 64)]
    lookup = {tiles[0]: 0}

    def entry(t):
        for flip in range(4):
            v = tuple(t[(7 - y if flip & 2 else y) * 8 + (7 - x if flip & 1 else x)] for y in range(8) for x in range(8))
            if v in lookup:
                return lookup[v] | (0x400 if flip & 1 else 0) | (0x800 if flip & 2 else 0)
        lookup[tuple(t)] = len(tiles)
        tiles.append(tuple(t))
        return len(tiles) - 1

    entries = [0] * 1024
    for (tx, ty), px in cells.items():
        if (tx, ty) in assigned:
            b = assigned[(tx, ty)]
            idx = {c: i for i, c in enumerate(bank_lists[b])}
            entries[ty * 32 + tx] = entry([idx[c] for c in px]) | ((FIRST_EXTRA_BANK + b) << 12)
        else:
            entries[ty * 32 + tx] = entry([base_index[c] for c in px])
    overview = len(tiles)
    zw, zh, zpx = png_indices(ZOOM)
    if (zw, zh) != (ZOOM_SIZE * 8, ZOOM_SIZE * 8):
        raise SystemExit('zoom_full.png must be 480x480')
    if any(v > 15 for r in zpx for v in r):
        raise SystemExit('zoom_full.png may only use the first 16 palette colours')
    zoom_entries = [entry([zpx[ty * 8 + y][tx * 8 + x] for y in range(8) for x in range(8)]) | 0x1000
                    for ty in range(ZOOM_SIZE) for tx in range(ZOOM_SIZE)]
    if len(tiles) > MAX_TILES:
        raise SystemExit('the pictures need %d different 8x8 tiles (%d for the full map); the game has room for %d'
                         % (len(tiles), overview, MAX_TILES))
    open(ZOOM_MAP, 'wb').write(struct.pack('<%dH' % len(zoom_entries), *zoom_entries))
    zoom_pal = (png_palette(ZOOM) + [(0, 0, 0)] * 16)[:16]
    palette = base + zoom_pal
    for cols in bank_lists:
        palette += [(r << 3, g << 3, b << 3) for r, g, b in cols] + [(0, 0, 0)] * (16 - len(cols))
    palette += [(0, 0, 0)] * (256 - len(palette))
    sheet = [[0] * 256 for _ in range(256)]
    for i, tile in enumerate(tiles):
        sx, sy = (i % 32) * 8, (i // 32) * 8
        for y in range(8):
            for x in range(8):
                sheet[sy + y][sx + x] = tile[y * 8 + x]
    write_png(TILES, 256, 256, sheet, palette)
    old = open(NSCR, 'rb').read()
    open(NSCR, 'wb').write(old[:0x24] + struct.pack('<1024H', *entries) + old[0x24 + 2048:])
    print('wrote background_tiles.png (%d tiles of %d: %d full map, %d close-up; %d extra palette(s) for %d tile(s)), '
          'background.NSCR and zoom_map.bin' % (len(tiles), MAX_TILES, overview, len(tiles) - overview, len(banks), len(assigned)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
