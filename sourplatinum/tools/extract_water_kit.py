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
import extract_cave_kit as K

TEXTURE_SETS = ['map_texture_set_006', 'map_texture_set_008']
KITS = {'sea': {'sea'}, 'lake': {'lake', 'lakep'}}
BANK = 'seaside3'
BED = 'puddle_b'
GROUND = {'ngrass', 'nectgr', 'ckado', 'lgreen', 'lgreenp', 'nsand', 'nsandp', 'tshadow', 'nhana', 'shana', 'hage', 'ngrass2', 'puddle', 'puddlep'}
WATER_DROP = 8.0
OUT = os.path.join(B.ASSETS, 'water_kit.json')
TEX_OUT = os.path.join(B.ASSETS, 'hideaway_textures', 'floors')
MAX_MAP = 300


def classify(tiles, water):
    kinds = {}
    for (c, r), pieces in tiles.items():
        top = K.centre_surface(pieces, c, r)
        if top is None:
            continue
        z, mat, n = top
        if mat in water and n[2] > 0.99:
            kinds[(c, r)] = ('w', z + WATER_DROP)
        elif mat in GROUND and n[2] > 0.99:
            kinds[(c, r)] = ('l', z)
    return kinds


def main():
    apicula = K.find_apicula()
    if not apicula:
        print('apicula not found; set APICULA to its path')
        return 1
    out = {'water_drop': WATER_DROP, 'bank': BANK, 'kits': {}}
    bank_png = None
    for kit_name, water in KITS.items():
        bank_png = build_kit(apicula, kit_name, water, out) or bank_png
    json.dump(out, open(OUT, 'w'), separators=(',', ':'))
    if bank_png:
        open(os.path.join(TEX_OUT, BANK + '.png'), 'wb').write(bank_png)
    return 0


def build_kit(apicula, kit_name, water, out):
    found = collections.defaultdict(collections.Counter)
    pieces = {}
    tmp = tempfile.mkdtemp()
    bank_png = None
    try:
        for path in sorted(glob.glob(os.path.join(ROOT, 'res', 'field', 'maps', 'data', 'map_data_*.bin'))):
            num = int(re.search(r'(\d+)', os.path.basename(path)).group(1))
            if num > MAX_MAP:
                continue
            data = open(path, 'rb').read()
            if BANK.encode() not in data or not any(w.encode() in data for w in water):
                continue
            tris = None
            for tset in TEXTURE_SETS:
                os.makedirs(os.path.join(tmp, tset), exist_ok=True)
                perm, tris = K.load_map(num, tset, apicula, os.path.join(tmp, tset))
                if tris and glob.glob(os.path.join(tmp, tset, 'g%d' % num, BANK + '.png')):
                    if bank_png is None:
                        bank_png = open(glob.glob(os.path.join(tmp, tset, 'g%d' % num, BANK + '.png'))[0], 'rb').read()
                    break
            if tris is None:
                continue
            tiles = K.clip_to_tiles(tris)
            kinds = classify(tiles, water)
            used = 0
            for (c, r), (kind, level) in kinds.items():
                sig = ''
                ok = True
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        k = kinds.get((c + dx, r + dy))
                        if k is None or abs(k[1] - level) > 0.5:
                            ok = False
                            break
                        sig += k[0]
                    if not ok:
                        break
                if not ok or sig == 'lllllllll':
                    continue
                x0, x1, y0, y1 = K.tile_rect(c, r)
                piece = []
                for mat, poly in tiles.get((c, r), []):
                    if mat in GROUND:
                        mat = 'floor'
                    elif mat in water and mat == kit_name:
                        mat = 'water'
                    elif mat not in water and mat not in (BANK, BED):
                        ok = False
                        break
                    rel = []
                    for p, uv, col in poly:
                        z = p[2] - level
                        if z < -64 or z > 8:
                            ok = False
                        rel.append(((p[0] - x0, p[1] - y0, z), uv, col))
                    piece.append((mat, rel))
                if not ok or not piece:
                    continue
                piece = K.canonical(piece)
                key = K.piece_key(piece)
                found[sig][key] += 1
                pieces.setdefault(key, (num, piece))
                used += 1
            if used:
                print('%s kit, map %d: %d tiles' % (kit_name, num, used))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    kit = {}
    for sig, variants in sorted(found.items()):
        key, count = variants.most_common(1)[0]
        num, piece = pieces[key]
        tris = []
        for mat, poly in piece:
            for k in range(1, len(poly) - 1):
                tri = [poly[0], poly[k], poly[k + 1]]
                tris.append({'m': mat,
                             'p': [[round(v, 3) for v in t[0]] for t in tri],
                             'uv': [[round(v, 4) for v in t[1]] for t in tri],
                             'c': [[round(v, 3) for v in t[2]] for t in tri]})
        kit[sig] = {'map': num, 'count': count, 'variants': len(variants), 'tris': tris}
    out['kits'][kit_name] = {'pieces': kit}
    print('%s kit: %d water/land patterns' % (kit_name, len(kit)))
    return bank_png


if __name__ == '__main__':
    sys.exit(main())
