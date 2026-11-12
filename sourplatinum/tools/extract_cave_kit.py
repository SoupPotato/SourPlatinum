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

KIT_SETS = ['map_texture_set_052', 'map_texture_set_068', 'map_texture_set_069']
OUT = os.path.join(B.ASSETS, 'cave_kit.json')
RADIUS = 3
WALL_HEIGHT = 32.0


def base_material(name):
    name = re.sub(r'_lm\d+$', '', name)
    return 'black' if re.match(r'^lm\d+$', name) else name


def clean_material(m):
    return m == 'black' or m.startswith('dun_wall_') or m in ('dun_floor', 'dun_floor2', 'dun_floor3', 'dun_floor4')


def find_apicula():
    env = os.environ.get('APICULA')
    if env and os.path.exists(env):
        return env
    for p in (os.path.join(ROOT, 'build', 'underground_models', 'apicula.exe'), shutil.which('apicula') or ''):
        if p and os.path.exists(p):
            return p
    return None


def cave_maps():
    headers = open(os.path.join(ROOT, 'include', 'data', 'map_headers.h')).read()
    found = collections.OrderedDict()
    for tset in KIT_SETS:
        for m in re.finditer(r'\[(MAP_HEADER_\w+)\]\s*=\s*\{(.*?)\n    \}', headers, re.S):
            body = m.group(2)
            area = re.search(r'areaDataArchiveID = (\w+)', body).group(1)
            matrix = re.search(r'mapMatrixID = (\w+)', body).group(1)
            area_json = json.load(open(os.path.join(ROOT, 'res', 'field', 'area_data', area + '.json')))
            if area_json['mapTextureSet'] != tset:
                continue
            path = os.path.join(ROOT, 'res', 'field', 'matrices', matrix + '.json')
            if not os.path.exists(path):
                continue
            for row in json.load(open(path))['maps']:
                for name in row:
                    if name and re.match(r'^MAP_\d+$', name):
                        found.setdefault(int(name[4:]), tset)
    return found


def load_map(num, tset, apicula, tmp):
    data = open(os.path.join(ROOT, 'res', 'field', 'maps', 'data', 'map_data_%03d.bin' % num), 'rb').read()
    ps, bs, ms, hs = struct.unpack_from('<4I', data, 0)
    perm = struct.unpack_from('<1024H', data, 16)
    model = data[16 + ps + bs:16 + ps + bs + ms]
    mpath = os.path.join(tmp, 'm%d.nsbmd' % num)
    open(mpath, 'wb').write(model)
    out = os.path.join(tmp, 'g%d' % num)
    tex = os.path.join(ROOT, 'res', 'field', 'maps', 'texture_sets', tset + '.nsbtx')
    subprocess.run([apicula, 'convert', '-f', 'glb', '--overwrite', mpath, tex, '-o', out], capture_output=True)
    hits = glob.glob(os.path.join(out, '*.glb'))
    if not hits:
        return None, None
    return perm, B.read_glb(hits[0])


def tile_rect(c, r):
    x0 = -B.HALF + c * B.T
    y1 = B.HALF - r * B.T
    return (x0, x0 + B.T, y1 - B.T, y1)


def clip_to_tiles(tris):
    tiles = collections.defaultdict(list)
    for mat, cos, uvs, cols, nrm, lo, hi in tris:
        mat = base_material(mat)
        poly = [(cos[k], uvs[k][:2], cols[k]) for k in range(3)]
        c0 = int((lo[0] + B.HALF) // B.T)
        c1 = int((hi[0] + B.HALF - 1e-6) // B.T)
        r0 = int((B.HALF - hi[1]) // B.T)
        r1 = int((B.HALF - lo[1] - 1e-6) // B.T)
        for r in range(max(0, r0), min(31, r1) + 1):
            for c in range(max(0, c0), min(31, c1) + 1):
                _, inside = B.cut_rect(poly, tile_rect(c, r))
                if inside:
                    tiles[(c, r)].append((mat, inside))
    return tiles


def centre_surface(pieces, c, r):
    x0, x1, y0, y1 = tile_rect(c, r)
    px, py = (x0 + x1) / 2, (y0 + y1) / 2
    best = None
    for mat, poly in pieces:
        for k in range(1, len(poly) - 1):
            a, b, d = poly[0][0], poly[k][0], poly[k + 1][0]
            if abs((b[0] - a[0]) * (d[1] - a[1]) - (d[0] - a[0]) * (b[1] - a[1])) < 1e-6:
                continue
            l = B.barycentric((px, py, 0.0), (a[0], a[1], 0.0), (b[0], b[1], 0.0), (d[0], d[1], 0.0))
            if l is None or min(l) < -1e-4:
                continue
            z = l[0] * a[2] + l[1] * b[2] + l[2] * d[2]
            n = B.norm(B.tri_normal(a, b, d))
            if best is None or z > best[0]:
                best = (z, mat, n)
    return best


def classify(perm, tiles):
    kind = {}
    for r in range(32):
        for c in range(32):
            top = centre_surface(tiles.get((c, r), []), c, r)
            if top is None:
                kind[(c, r)] = ('#',) if perm[r * 32 + c] & 0x8000 else ('?',)
                continue
            z, mat, n = top
            walkable = not (perm[r * 32 + c] & 0x8000)
            if walkable and mat.startswith('dun_floor') and n[2] > 0.99:
                kind[(c, r)] = ('.', round(z))
            elif not walkable and clean_material(mat):
                kind[(c, r)] = ('#',)
            else:
                kind[(c, r)] = ('?',)
    return kind


def distances(kind):
    dist = {}
    for (c, r), k in kind.items():
        if k[0] == '.':
            dist[(c, r)] = (0, k[1])
            continue
        if k[0] != '#':
            continue
        result = None
        for d in range(1, RADIUS + 1):
            ring = [(c + dx, r + dy) for dx in range(-d, d + 1) for dy in range(-d, d + 1) if max(abs(dx), abs(dy)) == d]
            inside = [kind.get(p) for p in ring if p in kind]
            floors = {k2[1] for k2 in inside if k2[0] == '.'}
            if floors:
                result = (d, floors.pop()) if len(floors) == 1 else None
                break
        else:
            result = (RADIUS, None)
        if result is not None:
            dist[(c, r)] = result
    return dist


def signature(dist, c, r):
    sig = []
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            p = (c + dx, r + dy)
            if not (0 <= p[0] < 32 and 0 <= p[1] < 32):
                return None
            if p not in dist:
                return None
            sig.append(str(min(dist[p][0], RADIUS)))
    return ''.join(sig)


def floor_level(dist, c, r):
    levels = set()
    for dy in range(-RADIUS, RADIUS + 1):
        for dx in range(-RADIUS, RADIUS + 1):
            v = dist.get((c + dx, r + dy))
            if v is not None and v[1] is not None:
                levels.add(v[1])
    return levels.pop() if len(levels) == 1 else None


def plane_basis(n):
    a = (1.0, 0.0, 0.0) if abs(n[0]) < 0.9 else (0.0, 1.0, 0.0)
    u = B.norm(B.cross(n, a))
    return u, B.cross(n, u)


def hull_2d(points):
    pts = sorted(set(points))
    if len(pts) < 3:
        return pts

    def turn(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and turn(lower[-2], lower[-1], p) <= 1e-6:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and turn(upper[-2], upper[-1], p) <= 1e-6:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def area_2d(poly):
    return abs(sum(poly[k][0] * poly[(k + 1) % len(poly)][1] - poly[(k + 1) % len(poly)][0] * poly[k][1] for k in range(len(poly)))) / 2


def merge_group(polys):
    tris = []
    for poly in polys:
        for k in range(1, len(poly) - 1):
            tris.append([poly[0], poly[k], poly[k + 1]])
    if len(tris) < 2:
        return None
    n = B.tri_normal(*[v[0] for v in tris[0]])
    bu, bv = plane_basis(n)
    to2 = lambda p: (round(B.dot(p, bu), 3), round(B.dot(p, bv), 3))
    ref = max(tris, key=lambda t: area_2d([to2(v[0]) for v in t]))
    rp = [v[0] for v in ref]

    def attrs(p):
        l = B.barycentric(p, *rp)
        uv = tuple(sum(l[k] * ref[k][1][j] for k in range(3)) for j in range(2))
        col = tuple(sum(l[k] * ref[k][2][j] for k in range(3)) for j in range(3))
        return uv, col
    total = 0.0
    for t in tris:
        total += area_2d([to2(v[0]) for v in t])
        shift = None
        for p, uv, col in t:
            auv, acol = attrs(p)
            d = (uv[0] - auv[0], uv[1] - auv[1])
            if shift is None:
                shift = (round(d[0]), round(d[1]))
            if abs(d[0] - shift[0]) > 0.02 or abs(d[1] - shift[1]) > 0.02 or max(abs(col[j] - acol[j]) for j in range(3)) > 0.03:
                return None
    lookup = {}
    for t in tris:
        for v in t:
            lookup[to2(v[0])] = v[0]
    hull = hull_2d(list(lookup))
    if abs(area_2d(hull) - total) > 0.01 * max(total, 1.0):
        return None
    out = []
    for h in hull:
        p = lookup[h]
        uv, col = attrs(p)
        out.append((p, uv, col))
    return out


def canonical(piece):
    groups = collections.OrderedDict()
    for mat, poly in piece:
        n = B.tri_normal(poly[0][0], poly[1][0], poly[2][0])
        d = B.dot(n, poly[0][0])
        key = (mat, round(n[0], 2), round(n[1], 2), round(n[2], 2), round(d, 1))
        groups.setdefault(key, []).append(poly)
    out = []
    for key, polys in groups.items():
        merged = merge_group(polys)
        if merged:
            out.append((key[0], merged))
        else:
            out.extend((key[0], p) for p in polys)
    return out


def piece_key(piece):
    return json.dumps([[m, [[round(v, 1) for v in p[0]] for p in poly]] for m, poly in sorted(piece, key=lambda x: (x[0], [p[0] for p in x[1]]))])


DOOR_MAP = 471
DOOR_SET = 'map_texture_set_055'
DOOR_ANCHORS = {'N': (11, 1, 0, 1), 'S': (11, 21, 0, -1), 'W': (1, 11, 1, 0), 'E': (21, 11, -1, 0)}
DOOR_MATERIALS = ('dun_dhole', 'dun_ent2')


def door_stamps(apicula, tmp):
    perm, tris = load_map(DOOR_MAP, DOOR_SET, apicula, tmp)
    tiles = clip_to_tiles(tris)
    kind = classify(perm, tiles)
    dist = distances(kind)
    stamps = {}
    for name, (ac, ar, fx, fy) in DOOR_ANCHORS.items():
        level = 16
        cells = []
        for a in (-1, 0, 1):
            for b in (-1, 0, 1):
                dx, dy = (a, b) if fx == 0 else (b, a)
                c, r = ac + dx, ar + dy
                x0, x1, y0, y1 = tile_rect(c, r)
                out = []
                for mat, poly in tiles.get((c, r), []):
                    if mat == 'black' and max(p[0][2] for p in poly) - level < WALL_HEIGHT - 1:
                        continue
                    for k in range(1, len(poly) - 1):
                        tri = [poly[0], poly[k], poly[k + 1]]
                        out.append({'m': mat,
                                    'p': [[round(t[0][0] - x0, 3), round(t[0][1] - y0, 3), round(t[0][2] - level, 3)] for t in tri],
                                    'uv': [[round(v, 4) for v in t[1]] for t in tri],
                                    'c': [[round(v, 3) for v in t[2]] for t in tri]})
                cells.append({'dx': dx, 'dy': dy, 'sig': signature(dist, c, r), 'tris': out})
        stamps[name] = {'front': [fx, fy], 'cells': cells}
    return stamps


def main():
    apicula = find_apicula()
    if not apicula:
        print('apicula not found; set APICULA to its path')
        return 1
    maps = cave_maps()
    found = collections.defaultdict(collections.Counter)
    pieces = {}
    tmp = tempfile.mkdtemp()
    try:
        doors = door_stamps(apicula, tmp)
        for num, tset in maps.items():
            perm, tris = load_map(num, tset, apicula, tmp)
            if tris is None:
                continue
            tiles = clip_to_tiles(tris)
            kind = classify(perm, tiles)
            dist = distances(kind)
            used = 0
            for (c, r) in dist:
                sig = signature(dist, c, r)
                if sig is None:
                    continue
                level = floor_level(dist, c, r)
                if level is None:
                    continue
                x0, x1, y0, y1 = tile_rect(c, r)
                piece = []
                ok = True
                for mat, poly in tiles.get((c, r), []):
                    if mat == 'black' and max(p[0][2] for p in poly) - level < WALL_HEIGHT - 1:
                        continue
                    if not clean_material(mat):
                        ok = False
                        break
                    rel = []
                    for p, uv, col in poly:
                        z = p[2] - level
                        if z < -0.5 or z > WALL_HEIGHT + 0.5:
                            ok = False
                        rel.append(((p[0] - x0, p[1] - y0, z), uv, col))
                    piece.append((mat, rel))
                if not ok or not piece:
                    continue
                piece = canonical(piece)
                key = piece_key(piece)
                found[sig][key] += 1
                pieces.setdefault(key, (num, piece))
                used += 1
            print('map %d (%s): %d tiles' % (num, tset[-3:], used))
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
    json.dump({'radius': RADIUS, 'tile': B.T, 'wall_height': WALL_HEIGHT, 'pieces': kit, 'doors': doors}, open(OUT, 'w'), separators=(',', ':'))
    print('%d signatures written to %s' % (len(kit), OUT))
    return 0


if __name__ == '__main__':
    sys.exit(main())
