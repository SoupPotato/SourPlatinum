import json
import os
import re
import struct
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(HERE, 'underground_block_editor_assets', 'battle_previews')
NARC = os.path.join(ROOT, 'res', 'prebuilt', 'battle', 'graphic', 'pl_batt_bg.narc')
TERRAIN_DIR = os.path.join(ROOT, 'res', 'graphics', 'battle', 'terrain')
TIMES = ['day', 'evening', 'night']


def narc_files(data):
    off = 0x10
    assert data[off:off + 4] == b'BTAF'
    size, count = struct.unpack_from('<IH', data, off + 4)
    entries = [struct.unpack_from('<II', data, off + 12 + 8 * i) for i in range(count)]
    off += size
    off += struct.unpack_from('<I', data, off + 4)[0]
    assert data[off:off + 4] == b'GMIF'
    base = off + 8
    return [data[base + s:base + e] for s, e in entries]


def lz(data):
    if not data or data[0] not in (0x10, 0x11):
        return data
    kind = data[0]
    size = int.from_bytes(data[1:4], 'little')
    pos = 4
    out = bytearray()
    while len(out) < size:
        flags = data[pos]
        pos += 1
        for bit in range(8):
            if len(out) >= size:
                break
            if flags & (0x80 >> bit):
                if kind == 0x10:
                    b1, b2 = data[pos], data[pos + 1]
                    pos += 2
                    length = (b1 >> 4) + 3
                    disp = (((b1 & 0xF) << 8) | b2) + 1
                else:
                    b1 = data[pos]
                    ind = b1 >> 4
                    if ind == 0:
                        length = (((b1 & 0xF) << 4) | (data[pos + 1] >> 4)) + 0x11
                        disp = (((data[pos + 1] & 0xF) << 8) | data[pos + 2]) + 1
                        pos += 3
                    elif ind == 1:
                        length = (((b1 & 0xF) << 12) | (data[pos + 1] << 4) | (data[pos + 2] >> 4)) + 0x111
                        disp = (((data[pos + 2] & 0xF) << 8) | data[pos + 3]) + 1
                        pos += 4
                    else:
                        length = ind + 1
                        disp = (((b1 & 0xF) << 8) | data[pos + 1]) + 1
                        pos += 2
                for _ in range(length):
                    out.append(out[-disp])
            else:
                out.append(data[pos])
                pos += 1
    return bytes(out)


def section(data, magic):
    off = struct.unpack_from('<H', data, 0xC)[0]
    while off < len(data):
        if data[off:off + 4] == magic:
            return off
        off += struct.unpack_from('<I', data, off + 4)[0]
    raise ValueError(magic)


def ncgr(data):
    s = section(data, b'RAHC')
    depth = struct.unpack_from('<I', data, s + 0xC)[0]
    size, off = struct.unpack_from('<II', data, s + 0x18)
    raw = data[s + 0x8 + off:s + 0x8 + off + size] if off else data[s + 0x20:s + 0x20 + size]
    bpp = 4 if depth == 3 else 8
    tiles = []
    step = 8 * bpp
    for t in range(len(raw) // step):
        chunk = raw[t * step:(t + 1) * step]
        if bpp == 4:
            px = []
            for b in chunk:
                px += [b & 0xF, b >> 4]
        else:
            px = list(chunk)
        tiles.append(px)
    return tiles, bpp


def nclr(data):
    s = section(data, b'TTLP')
    size, off = struct.unpack_from('<II', data, s + 0x10)
    raw = data[s + 0x18:s + 0x18 + size]
    cols = []
    for i in range(0, len(raw) - 1, 2):
        v = struct.unpack_from('<H', raw, i)[0]
        cols.append(((v & 31) * 255 // 31, ((v >> 5) & 31) * 255 // 31, ((v >> 10) & 31) * 255 // 31))
    return cols


def nscr(data):
    s = section(data, b'NRCS')
    w, h = struct.unpack_from('<HH', data, s + 8)
    size = struct.unpack_from('<I', data, s + 0x10)[0]
    raw = data[s + 0x14:s + 0x14 + size]
    return w, h, [struct.unpack_from('<H', raw, i)[0] for i in range(0, len(raw), 2)]


def write_png(path, w, h, rows, alpha=False):
    raw = b''.join(b'\0' + bytes(v for p in row for v in p) for row in rows)
    ch = lambda t, d: struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    open(path, 'wb').write(b'\x89PNG\r\n\x1a\n' + ch(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 6 if alpha else 2, 0, 0, 0))
                           + ch(b'IDAT', zlib.compress(raw, 9)) + ch(b'IEND', b''))


def render_bg(tiles, bpp, pal, w, h, entries, crop=(256, 192)):
    rows = [[(0, 0, 0)] * crop[0] for _ in range(crop[1])]
    for i, e in enumerate(entries):
        block, k = divmod(i, 1024)
        tx, ty = (block % max(1, w // 256)) * 256 + (k % 32) * 8, (block // max(1, w // 256)) * 256 + (k // 32) * 8
        if tx >= crop[0] or ty >= crop[1]:
            continue
        idx, hf, vf, pb = e & 0x3FF, (e >> 10) & 1, (e >> 11) & 1, e >> 12
        if idx >= len(tiles):
            continue
        t = tiles[idx]
        for y in range(8):
            for x in range(8):
                v = t[(7 - y if vf else y) * 8 + (7 - x if hf else x)]
                c = pal[(pb * 16 + v) if bpp == 4 else v] if ((pb * 16 + v) if bpp == 4 else v) < len(pal) else (0, 0, 0)
                rows[ty + y][tx + x] = c
    return rows


def read_indexed_png(path):
    d = open(path, 'rb').read()
    pos, idat, plte, trns = 8, b'', None, None
    while pos < len(d):
        ln, = struct.unpack('>I', d[pos:pos + 4])
        typ, data = d[pos + 4:pos + 8], d[pos + 8:pos + 8 + ln]
        pos += 12 + ln
        if typ == b'IHDR':
            w, h, bd, ct = struct.unpack('>IIBB', data[:10])
        elif typ == b'PLTE':
            plte = data
        elif typ == b'tRNS':
            trns = data
        elif typ == b'IDAT':
            idat += data
    raw = zlib.decompress(idat)
    stride = (w * bd + 7) // 8
    rows, prev = [], bytearray(stride)
    i = 0
    for y in range(h):
        f = raw[i]
        line = bytearray(raw[i + 1:i + 1 + stride])
        i += 1 + stride
        for x in range(stride):
            a = line[x - 1] if x else 0
            b = prev[x]
            c = prev[x - 1] if x else 0
            if f == 1:
                line[x] = (line[x] + a) & 255
            elif f == 2:
                line[x] = (line[x] + b) & 255
            elif f == 3:
                line[x] = (line[x] + ((a + b) >> 1)) & 255
            elif f == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                line[x] = (line[x] + (a if pa <= pb and pa <= pc else (b if pb <= pc else c))) & 255
        prev = line
        idx = []
        for x in range(w):
            if bd == 8:
                idx.append(line[x])
            elif bd == 4:
                idx.append((line[x // 2] >> (4 if x % 2 == 0 else 0)) & 15)
        rows.append(idx)
    return w, h, rows


def read_jasc(path):
    lines = open(path).read().split('\n')
    n = int(lines[2])
    return [tuple(int(v) for v in lines[3 + i].split()) for i in range(n)]


def main():
    os.makedirs(OUT, exist_ok=True)
    files = [lz(f) for f in narc_files(open(NARC, 'rb').read())]
    backgrounds = [l.strip() for l in open(os.path.join(ROOT, 'generated', 'battle_backgrounds.txt')) if l.strip() and not l.strip().endswith('_MAX')]
    w, h, entries = nscr(files[2])
    index = {'backgrounds': {}, 'terrains': {}}
    for b, name in enumerate(backgrounds):
        try:
            tiles, bpp = ncgr(files[3 + b])
        except Exception:
            continue
        for t, tname in enumerate(TIMES):
            try:
                pal = nclr(files[172 + b * 3 + t])
            except Exception:
                continue
            fn = 'bg_%s_%s.png' % (name, tname)
            write_png(os.path.join(OUT, fn), 256, 192, render_bg(tiles, bpp, pal, w, h, entries))
            index['backgrounds'].setdefault(name, {})[tname] = fn
    src = open(os.path.join(ROOT, 'src', 'battle', 'terrain.c')).read()
    pal_rows = dict(re.findall(r'\[(TERRAIN_\w+)\]\s*=\s*\{\s*terrain_(\w+?)_(?:day|all)_NCLR', src))
    player = dict(re.findall(r'\[(TERRAIN_\w+)\]\s*=\s*terrain_(\w+?)_player_NCGR_lz', src))
    enemy = dict(re.findall(r'\[(TERRAIN_\w+)\]\s*=\s*terrain_(\w+?)_enemy_NCGR_lz', src))
    for terrain, folder in player.items():
        pfolder = pal_rows.get(terrain, folder)
        for side, which in (('player', folder), ('enemy', enemy.get(terrain, folder))):
            png = os.path.join(TERRAIN_DIR, which, side + '.png')
            if not os.path.exists(png):
                continue
            iw, ih, idx = read_indexed_png(png)
            for tname in TIMES:
                palfile = os.path.join(TERRAIN_DIR, pfolder, tname + '.pal')
                if not os.path.exists(palfile):
                    palfile = os.path.join(TERRAIN_DIR, pfolder, 'all.pal')
                pal = read_jasc(palfile)
                rows = [[(pal[v] + (0 if v == 0 else 255,)) if v < len(pal) else (0, 0, 0, 0) for v in row] for row in idx]
                fn = 'ground_%s_%s_%s.png' % (terrain, side, tname)
                write_png(os.path.join(OUT, fn), iw, ih, rows, alpha=True)
                index['terrains'].setdefault(terrain, {}).setdefault(side, {})[tname] = fn
    json.dump(index, open(os.path.join(OUT, 'index.json'), 'w'), indent=1)
    print('%d backgrounds, %d grounds' % (len(index['backgrounds']), len(index['terrains'])))
    return 0


if __name__ == '__main__':
    sys.exit(main())
