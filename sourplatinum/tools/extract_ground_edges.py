import collections
import glob
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import underground_block_builder as B
from extract_cave_kit import find_apicula

FAMILIES = {'lgreen': 'lgreenp', 'nsand': 'nsandp', 'puddle': 'puddlep', 'beach': 'beachp', 'blueglay': 'blueglayp', 'lake': 'lakep'}
TEXTURE_SETS = ['map_texture_set_006', 'map_texture_set_000', 'map_texture_set_014']
OUT = os.path.join(B.ASSETS, 'ground_edges.json')
TEX_OUT = os.path.join(B.ASSETS, 'hideaway_textures', 'floors')
NEIGHBOURS = [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]
MAX_MAP = 300


def canonical(mask):
    m = list(mask)
    for d, a, b in ((0, 1, 3), (2, 1, 4), (5, 3, 6), (7, 4, 6)):
        if m[a] == '1' or m[b] == '1':
            m[d] = '0'
    return ''.join(m)


def base(mat):
    return re.sub(r'_lm\d+$', '', mat)


def tile_rect(c, r):
    x0 = -B.HALF + c * B.T
    y1 = B.HALF - r * B.T
    return x0, x0 + B.T, y1 - B.T, y1


def covering(tris, x, y):
    best = None
    for t in tris:
        mat, cos, uvs = t[0], t[1], t[2]
        if t[5][0] > x or t[6][0] < x or t[5][1] > y or t[6][1] < y:
            continue
        a, b, c = cos
        den = (b[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (b[1] - a[1])
        if abs(den) < 1e-6:
            continue
        l1 = ((x - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (y - a[1])) / den
        l2 = ((b[0] - a[0]) * (y - a[1]) - (x - a[0]) * (b[1] - a[1])) / den
        l0 = 1 - l1 - l2
        if min(l0, l1, l2) < -1e-4:
            continue
        z = l0 * a[2] + l1 * b[2] + l2 * c[2]
        if best is None or z > best[0] + 0.01:
            best = (z, t)
    return best[1] if best else None


def affine_uv(t, x, y):
    a, b, c = t[1]
    den = (b[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (b[1] - a[1])
    l1 = ((x - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (y - a[1])) / den
    l2 = ((b[0] - a[0]) * (y - a[1]) - (x - a[0]) * (b[1] - a[1])) / den
    l0 = 1 - l1 - l2
    return tuple(l0 * t[2][0][k] + l1 * t[2][1][k] + l2 * t[2][2][k] for k in range(2))


def learn_map(tris, table):
    by_family = collections.defaultdict(list)
    for t in tris:
        m = base(t[0])
        if m in FAMILIES or m in FAMILIES.values():
            by_family[m].append(t)
    if not by_family:
        return 0
    found = 0
    grid = {}
    for r in range(32):
        for c in range(32):
            x0, x1, y0, y1 = tile_rect(c, r)
            t = covering([t for ts in by_family.values() for t in ts], (x0 + x1) / 2, (y0 + y1) / 2)
            if t is not None:
                grid[(c, r)] = (base(t[0]), t)
    for (c, r), (m, t) in grid.items():
        fam = next((f for f, e in FAMILIES.items() if e == m), None)
        if fam is None:
            continue
        mask = ''.join('1' if grid.get((c + dx, r + dy), ('',))[0] == fam else '0' for dx, dy in NEIGHBOURS)
        if mask == '00000000':
            continue
        x0, x1, y0, y1 = tile_rect(c, r)
        corners = [affine_uv(t, x, y) for x, y in ((x0, y1), (x1, y1), (x1, y0), (x0, y0))]
        su = min(u for u, v in corners)
        sv = min(v for u, v in corners)
        shift = (int(su // 1), int(sv // 1))
        corners = tuple((round(u - shift[0], 3), round(v - shift[1], 3)) for u, v in corners)
        table[fam][mask][(c % 2, r % 2)][corners] += 1
        found += 1
    return found


def main():
    apicula = find_apicula()
    if not apicula:
        print('apicula not found; set APICULA to its path')
        return 1
    data_dir = os.path.join(ROOT, 'res', 'field', 'maps', 'data')
    names = '|'.join(FAMILIES.values())
    table = collections.defaultdict(lambda: collections.defaultdict(lambda: collections.defaultdict(collections.Counter)))
    tmp = tempfile.mkdtemp()
    textures = {}
    try:
        for path in sorted(glob.glob(os.path.join(data_dir, 'map_data_*.bin'))):
            num = int(re.search(r'(\d+)', os.path.basename(path)).group(1))
            if num > MAX_MAP:
                continue
            data = open(path, 'rb').read()
            if not re.search(names.encode(), data):
                continue
            ps, bs, ms, hs = struct.unpack_from('<4I', data, 0)
            model = os.path.join(tmp, 'm%d.nsbmd' % num)
            open(model, 'wb').write(data[16 + ps + bs:16 + ps + bs + ms])
            for tset in TEXTURE_SETS:
                out = os.path.join(tmp, 'g%d_%s' % (num, tset[-3:]))
                subprocess.run([apicula, 'convert', '-f', 'glb', '--overwrite', model,
                                os.path.join(ROOT, 'res', 'field', 'maps', 'texture_sets', tset + '.nsbtx'), '-o', out], capture_output=True)
                hits = glob.glob(os.path.join(out, '*.glb'))
                pngs = {os.path.splitext(os.path.basename(p))[0]: p for p in glob.glob(os.path.join(out, '*.png'))}
                if hits and any(e in pngs for e in FAMILIES.values()):
                    for name in list(FAMILIES) + list(FAMILIES.values()):
                        src = pngs.get(name) or pngs.get(name + '_1')
                        if src and name not in textures:
                            textures[name] = open(src, 'rb').read()
                    n = learn_map(B.read_glb(hits[0]), table)
                    print('map %d: %d edge tiles' % (num, n))
                    break
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    out = {'families': {}, 'neighbours': NEIGHBOURS}
    shared = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
    for fam, masks in table.items():
        entry = {}
        for mask, parities in masks.items():
            entry[mask] = {'%d%d' % p: [list(c) for c in counts.most_common(1)[0][0]] for p, counts in parities.items()}
            for p, counts in parities.items():
                for corners, n in counts.items():
                    shared[canonical(mask)]['%d%d' % p][corners] += n
        out['families'][fam] = {'edge': FAMILIES[fam], 'masks': entry}
        print('%s: %d neighbour patterns' % (fam, len(entry)))
    out['canonical'] = {mask: {p: [list(c) for c in counts.most_common(1)[0][0]] for p, counts in parities.items()}
                        for mask, parities in shared.items()}
    print('%d canonical patterns shared by all families' % len(out['canonical']))
    json.dump(out, open(OUT, 'w'), separators=(',', ':'))
    for name, raw in textures.items():
        open(os.path.join(TEX_OUT, name + '.png'), 'wb').write(raw)
    print('wrote %s and %d textures' % (OUT, len(textures)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
