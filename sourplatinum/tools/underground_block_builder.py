import glob
import json
import math
import re
import os
import struct
import subprocess
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, 'underground_block_editor_assets')

T = 16.0
HALF = 256.0
TOP = 58.0
FLOOR = -2.0
MID = 16.0
RAIL_LO, RAIL_HI, RAIL_T = 36.9, 47.6, 6.0
DOOR_W, DOOR_H = 32.0, 30.0
EPS = 1e-4

PROF = {'N': (14.6, 33.8), 'S': (18.7, 45.9), 'W': (14.8, 37.9), 'E': (14.8, 37.9)}
RAIL_E = {n: (PROF[n][1] - o - RAIL_T, PROF[n][1] - o) for n, o in (('N', 4.8), ('S', 2.9), ('W', 5.9), ('E', 5.9))}
DIRS = {'N': (0.0, 1.0), 'S': (0.0, -1.0), 'E': (1.0, 0.0), 'W': (-1.0, 0.0)}
COLLISION = {'.': 0x000C, '#': 0x8000, 'D': 0x8000}
FLOOR_COL = (1.0, 1.0, 1.0)
SHADOW_WIDTH = 16.0
SHADOW_EDGE = 0.19
SHADOW_CORNER = 0.04
RAIL_COL = (0.85, 0.85, 0.85)
BLACK = (0.0, 0.0, 0.0)

MATERIALS = [
    ('ug_map_ground', 'ug_floor', 0, 0),
    ('ug_map_wall', 'ug_map_wall', 0, 0),
    ('pasted__ug_map_s', 'ug_wall_stem', 1, 6),
    ('ug_door', 'dun_dhole', 0, 0),
    ('ug_door_floor', 'dun_ent2', 0, 0),
    ('ug_map_stem', 'ug_wall_stem2', 2, 6),
]
DOOR_PIECE = json.load(open(os.path.join(ASSETS, 'door_piece.json')))
DOOR_FLOOR_DEPTH = 16.0
USED_HEIGHT = {'ug_map_wall': 48}


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def mul(a, s):
    return (a[0] * s, a[1] * s, a[2] * s)


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def norm(a):
    length = math.sqrt(dot(a, a))
    return (0.0, 0.0, 0.0) if length < 1e-12 else mul(a, 1.0 / length)


def tri_normal(a, b, c):
    return norm(cross(sub(b, a), sub(c, a)))


def barycentric(p, a, b, c):
    v0, v1, v2 = sub(b, a), sub(c, a), sub(p, a)
    d00, d01, d11 = dot(v0, v0), dot(v0, v1), dot(v1, v1)
    d20, d21 = dot(v2, v0), dot(v2, v1)
    den = d00 * d11 - d01 * d01
    if abs(den) < 1e-12:
        return (1.0, 0.0, 0.0)
    v = (d11 * d20 - d01 * d21) / den
    w = (d00 * d21 - d01 * d20) / den
    return (1.0 - v - w, v, w)


def read_png(path):
    d = open(path, 'rb').read()
    pos = 8
    idat = b''
    plte = trns = None
    while pos < len(d):
        ln, = struct.unpack('>I', d[pos:pos + 4])
        typ = d[pos + 4:pos + 8]
        data = d[pos + 8:pos + 8 + ln]
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
    chans = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[ct]
    bits = chans * bd
    stride = (w * bits + 7) // 8
    bpp = max(1, bits // 8)
    rows, prev, off = [], bytearray(stride), 0
    for _ in range(h):
        ft = raw[off]
        line = bytearray(raw[off + 1:off + 1 + stride])
        off += 1 + stride
        for i in range(stride):
            left = line[i - bpp] if i >= bpp else 0
            up = prev[i]
            ul = prev[i - bpp] if i >= bpp else 0
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
    out = []
    for line in rows:
        px = []
        for x in range(w):
            if ct == 3:
                if bd == 8:
                    idx = line[x]
                else:
                    per = 8 // bd
                    idx = (line[x // per] >> (8 - bd * (x % per + 1))) & ((1 << bd) - 1)
                r, g, b = plte[idx * 3:idx * 3 + 3]
                a = trns[idx] if trns and idx < len(trns) else 255
            elif ct == 2:
                r, g, b = line[x * 3:x * 3 + 3]
                a = 255
            elif ct == 6:
                r, g, b, a = line[x * 4:x * 4 + 4]
            elif ct == 4:
                r = g = b = line[x * 2]
                a = line[x * 2 + 1]
            else:
                r = g = b = line[x]
                a = 255
            px.append((r, g, b, a))
        out.append(px)
    return w, h, out


def to_srgb(v):
    v = min(1.0, max(0.0, v))
    return v * 12.92 if v <= 0.0031308 else 1.055 * v ** (1 / 2.4) - 0.055


def read_glb(path):
    d = open(path, 'rb').read()
    length = struct.unpack_from('<I', d, 8)[0]
    off = 12
    js = binb = None
    while off < length:
        clen, ctype = struct.unpack_from('<II', d, off)
        chunk = d[off + 8:off + 8 + clen]
        if ctype == 0x4E4F534A:
            js = json.loads(chunk)
        elif ctype == 0x004E4942:
            binb = chunk
        off += 8 + clen

    def accessor(i):
        a = js['accessors'][i]
        bv = js['bufferViews'][a['bufferView']]
        fmt, size = {5126: ('f', 4), 5121: ('B', 1), 5123: ('H', 2), 5125: ('I', 4), 5120: ('b', 1), 5122: ('h', 2)}[a['componentType']]
        n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a['type']]
        start = bv.get('byteOffset', 0) + a.get('byteOffset', 0)
        stride = bv.get('byteStride', size * n)
        scale = {'B': 255.0, 'H': 65535.0}.get(fmt) if a.get('normalized') else None
        out = []
        for k in range(a['count']):
            vals = struct.unpack_from('<' + fmt * n, binb, start + k * stride)
            out.append(tuple(v / scale for v in vals) if scale else vals)
        return out

    canon = {'ug_floor': 'ug_map_ground', 'ug_wall_stem': 'pasted__ug_map_s', 'ug_map_wall': 'ug_map_wall',
             'ug_wall_stem2': 'ug_map_stem'}
    mat_names = []
    for m in js.get('materials', []):
        name = m.get('name', '')
        tex = m.get('pbrMetallicRoughness', {}).get('baseColorTexture')
        if tex is not None:
            src = js['textures'][tex['index']].get('source')
            img = js['images'][src].get('name') or js['images'][src].get('uri', '')
            key = os.path.splitext(os.path.basename(img))[0]
            name = canon.get(key, name)
        mat_names.append(name)
    tris = []
    for mesh in js['meshes']:
        for prim in mesh['primitives']:
            at = prim['attributes']
            pos = accessor(at['POSITION'])
            uv = accessor(at['TEXCOORD_0']) if 'TEXCOORD_0' in at else [(0.0, 0.0)] * len(pos)
            col = accessor(at['COLOR_0']) if 'COLOR_0' in at else [(1.0, 1.0, 1.0)] * len(pos)
            idx = [i[0] for i in accessor(prim['indices'])] if 'indices' in prim else list(range(len(pos)))
            mat = mat_names[prim['material']] if 'material' in prim else ''
            for k in range(0, len(idx) - 2, 3):
                vs = idx[k:k + 3]
                cos = [(pos[i][0], -pos[i][2], pos[i][1]) for i in vs]
                uvs = [(uv[i][0], 1.0 - uv[i][1], 0.0) for i in vs]
                cols = [tuple(to_srgb(v) for v in col[i][:3]) for i in vs]
                n = tri_normal(*cos)
                if dot(n, n) < 1e-12:
                    continue
                lo = tuple(min(c[j] for c in cos) for j in range(3))
                hi = tuple(max(c[j] for c in cos) for j in range(3))
                tris.append((mat, cos, uvs, cols, n, lo, hi))
    return tris


LIB = read_glb(os.path.join(ASSETS, 'reference_block.glb'))
LIB_BY_MAT = {}
for t in LIB:
    LIB_BY_MAT.setdefault(t[0], []).append(t)

LIB_WALL = {
    'N': lambda u, d, z: (u, 193.8 - d, z),
    'S': lambda u, d, z: (u, 34.1 + d, z),
    'W': lambda u, d, z: (-197.9 + d, u, z),
    'E': lambda u, d, z: (-42.1 - d, u, z),
}


LIB_RANGE = {'N': (110.0, 250.0), 'S': (110.0, 250.0), 'W': (-250.0, -110.0), 'E': (-250.0, -110.0)}


def sample(mat, p, nrm, color_at=None):
    if color_at is not None:
        uv = sample(mat, p, nrm)[0]
        return uv, sample(mat, color_at, nrm)[1]
    best = None
    for m, cos, uvs, cols, n, lo, hi in LIB_BY_MAT.get(mat, ()):
        if nrm is not None and dot(n, nrm) < 0.9:
            continue
        dist = abs(dot(sub(p, cos[0]), n))
        out = sum(max(0.0, lo[i] - p[i], p[i] - hi[i]) for i in range(3))
        score = dist * 10 + out
        if best is None or score < best[0]:
            best = (score, cos, uvs, cols)
    if best is None:
        return (0.0, 0.0), (1.0, 1.0, 1.0)
    _, cos, uvs, cols = best
    w = barycentric(p, *cos)
    uv = add(add(mul(uvs[0], w[0]), mul(uvs[1], w[1])), mul(uvs[2], w[2]))
    c = add(add(mul(cols[0], w[0]), mul(cols[1], w[1])), mul(cols[2], w[2]))
    return (uv[0], uv[1]), tuple(min(1.0, max(0.0, v)) for v in c)


def elevation(name, e):
    upper, total = PROF[name]
    lower = total - upper
    if e <= 0:
        return FLOOR
    if e < lower:
        return FLOOR + (MID - FLOOR) * e / lower
    if e < total:
        return MID + (TOP - MID) * (e - lower) / upper
    return TOP


def inverse(name, z):
    upper, total = PROF[name]
    lower = total - upper
    if z <= FLOOR:
        return 0.0
    if z <= MID:
        return lower * (z - FLOOR) / (MID - FLOOR)
    return lower + upper * min(1.0, (z - MID) / (TOP - MID))


SOURCE_DIR = os.path.join(ASSETS, 'source_blocks')
REGION_MARGIN = 1
_SOURCE_CACHE = {}


def source_tris(block_id):
    if block_id is None:
        return []
    if block_id not in _SOURCE_CACHE:
        path = os.path.join(SOURCE_DIR, 'block_%d.glb' % block_id)
        _SOURCE_CACHE[block_id] = read_glb(path) if os.path.exists(path) else []
    return _SOURCE_CACHE[block_id]


def source_grid(block_id):
    if block_id is None:
        return None
    path = os.path.join(ASSETS, 'blocks', 'block_%d.json' % block_id)
    if not os.path.exists(path):
        return None
    return [list(r) for r in json.load(open(path))['tiles']]


def lerp_vertex(a, b, f):
    return (tuple(a[0][i] + (b[0][i] - a[0][i]) * f for i in range(3)),
            tuple(a[1][i] + (b[1][i] - a[1][i]) * f for i in range(2)),
            tuple(a[2][i] + (b[2][i] - a[2][i]) * f for i in range(3)))


def poly_area(poly):
    total = (0.0, 0.0, 0.0)
    for k in range(1, len(poly) - 1):
        total = add(total, cross(sub(poly[k][0], poly[0][0]), sub(poly[k + 1][0], poly[0][0])))
    return math.sqrt(dot(total, total)) / 2


def split_poly(poly, axis, value):
    lo, hi = [], []
    for k in range(len(poly)):
        a, b = poly[k], poly[(k + 1) % len(poly)]
        da, db = a[0][axis] - value, b[0][axis] - value
        if da <= 1e-6:
            lo.append(a)
        if da >= -1e-6:
            hi.append(a)
        if (da < -1e-6 and db > 1e-6) or (da > 1e-6 and db < -1e-6):
            m = lerp_vertex(a, b, da / (da - db))
            lo.append(m)
            hi.append(m)
    lo = lo if len(lo) >= 3 and poly_area(lo) > 1e-3 else None
    hi = hi if len(hi) >= 3 and poly_area(hi) > 1e-3 else None
    return lo, hi


def cut_rect(poly, r):
    outside = []
    a, b = split_poly(poly, 0, r[0])
    if a:
        outside.append(a)
    if not b:
        return outside, None
    a, b = split_poly(b, 0, r[1])
    if b:
        outside.append(b)
    if not a:
        return outside, None
    c, d = split_poly(a, 1, r[2])
    if c:
        outside.append(c)
    if not d:
        return outside, None
    e, f = split_poly(d, 1, r[3])
    if f:
        outside.append(f)
    return outside, e


class Block:
    def __init__(self, tiles, name, neighbours=None, source=None, neighbour_sources=None):
        self.grid = [list(r) for r in tiles]
        self.name = name
        self.nb = {k: [list(r) for r in v] for k, v in (neighbours or {}).items()}
        self.faces = []
        self.doors = []
        self.source = source
        self.door_frames = self.find_doors()
        self.region = self.find_region()
        self.region_rects = self.merge_region()
        self.match_tris = []
        offsets = {'N': (0.0, 512.0), 'S': (0.0, -512.0), 'E': (512.0, 0.0), 'W': (-512.0, 0.0)}
        for side, block_id in [(None, source)] + list((neighbour_sources or {}).items()):
            ox, oy = offsets.get(side, (0.0, 0.0))
            for m, cos, uvs, cols, n, lo, hi in source_tris(block_id):
                moved = [(c[0] + ox, c[1] + oy, c[2]) for c in cos]
                self.match_tris.append((m, moved, uvs, cols, n, (lo[0] + ox, lo[1] + oy, lo[2]), (hi[0] + ox, hi[1] + oy, hi[2])))
        self.match_buckets = {}
        for k, tri in enumerate(self.match_tris):
            lo, hi = tri[5], tri[6]
            for bx in range(int(math.floor(lo[0] / 32)), int(math.floor(hi[0] / 32)) + 1):
                for by in range(int(math.floor(lo[1] / 32)), int(math.floor(hi[1] / 32)) + 1):
                    self.match_buckets.setdefault((bx, by), []).append(k)

    def find_region(self):
        original = source_grid(self.source)
        if original is None or not source_tris(self.source):
            return {(tx, tz) for tz in range(32) for tx in range(32)}
        before = Block([''.join(r) for r in original], 'source', {k: [''.join(r) for r in v] for k, v in self.nb.items()})
        changed = set()
        for tz in range(32):
            for tx in range(32):
                x0, x1, y0, y1 = self.tile_rect(tx, tz)
                for i in range(5):
                    for j in range(5):
                        x = x0 + (x1 - x0) * (0.02 + 0.96 * i / 4)
                        y = y0 + (y1 - y0) * (0.02 + 0.96 * j / 4)
                        if abs(self.height(x, y) - before.height(x, y)) > 0.05 or                                 abs(self.floor_shade(x, y)[0] - before.floor_shade(x, y)[0]) > 0.005:
                            changed.add((tx, tz))
        for d in self.door_frames:
            x0, x1, y0, y1 = d['rect']
            for tz in range(32):
                for tx in range(32):
                    a0, a1, b0, b1 = self.tile_rect(tx, tz)
                    if a0 < x1 and a1 > x0 and b0 < y1 and b1 > y0:
                        changed.add((tx, tz))
        region = set()
        for tx, tz in changed:
            for dz in range(-REGION_MARGIN, REGION_MARGIN + 1):
                for dx in range(-REGION_MARGIN, REGION_MARGIN + 1):
                    if 0 <= tx + dx < 32 and 0 <= tz + dz < 32:
                        region.add((tx + dx, tz + dz))
        return region

    def merge_region(self):
        rects, left = [], set(self.region)
        for tz in range(32):
            for tx in range(32):
                if (tx, tz) not in left:
                    continue
                x1 = tx
                while (x1 + 1, tz) in left:
                    x1 += 1
                z1 = tz
                while all((x, z1 + 1) in left for x in range(tx, x1 + 1)):
                    z1 += 1
                for z in range(tz, z1 + 1):
                    for x in range(tx, x1 + 1):
                        left.discard((x, z))
                rects.append((-HALF + T * tx, -HALF + T * (x1 + 1), HALF - T * (z1 + 1), HALF - T * tz))
        return rects

    def in_region(self, x, y):
        return (int(math.floor((x + HALF) / T)), int(math.floor((HALF - y) / T))) in self.region

    def match_vertex(self, mat, p, nrm):
        best = None
        for k in self.match_buckets.get((int(math.floor(p[0] / 32)), int(math.floor(p[1] / 32))), ()):
            m, cos, uvs, cols, n, lo, hi = self.match_tris[k]
            if m != mat or dot(n, nrm) < 0.98 or abs(dot(sub(p, cos[0]), n)) > 0.25:
                continue
            out = sum(max(0.0, lo[i] - p[i], p[i] - hi[i]) for i in range(3))
            if best is None or out < best[0]:
                best = (out, cos, uvs, cols)
        if best is None:
            return None
        out, cos, uvs, cols = best
        w = barycentric(p, *cos)
        uv = add(add(mul(uvs[0], w[0]), mul(uvs[1], w[1])), mul(uvs[2], w[2]))
        cw = [max(0.0, v) for v in w]
        s = sum(cw) or 1.0
        cw = [v / s for v in cw]
        c = add(add(mul(cols[0], cw[0]), mul(cols[1], cw[1])), mul(cols[2], cw[2]))
        return (uv[0], uv[1]), tuple(min(1.0, max(0.0, v)) for v in c), out < 1e-3

    def match_faces(self, start):
        for k in range(start, len(self.faces)):
            mat, pts, uvs, cols = self.faces[k]
            if len(pts) < 3:
                continue
            n = tri_normal(pts[0], pts[1], pts[2])
            if dot(n, n) < 1e-12:
                continue
            new_uvs, new_cols = list(uvs), list(cols)
            for i, p in enumerate(pts):
                hit = self.match_vertex(mat, p, n)
                if hit is None:
                    continue
                uv, c, inside = hit
                new_uvs[i] = uv
                if mat != 'ug_map_ground' or inside:
                    new_cols[i] = c
            self.faces[k] = (mat, pts, new_uvs, new_cols)

    def keep_source(self):
        tris = source_tris(self.source)
        if not tris or len(self.region) == 32 * 32:
            return
        rects = self.region_rects

        def touches(lo, hi):
            return any(lo[0] < r[1] - 1e-3 and hi[0] > r[0] + 1e-3 and lo[1] < r[3] - 1e-3 and hi[1] > r[2] + 1e-3 for r in rects)
        stems = [k for k, tri in enumerate(tris) if tri[0] == 'ug_map_stem']
        key = lambda c: (round(c[0], 2), round(c[1], 2), round(c[2], 2))
        owner = {}
        for k in stems:
            for c in tris[k][1]:
                owner.setdefault(key(c), []).append(k)
        drop = set()
        seen = set()
        for k in stems:
            if k in seen:
                continue
            island, stack = set(), [k]
            while stack:
                j = stack.pop()
                if j in island:
                    continue
                island.add(j)
                for c in tris[j][1]:
                    stack.extend(owner[key(c)])
            seen |= island
            if any(touches(tris[j][5], tris[j][6]) for j in island):
                drop |= island
        for k, (m, cos, uvs, cols, n, lo, hi) in enumerate(tris):
            if k in drop:
                continue
            pieces = [[(cos[i], (uvs[i][0], uvs[i][1]), cols[i]) for i in range(3)]]
            if m != 'ug_map_stem':
                for r in rects:
                    if not (lo[0] < r[1] and hi[0] > r[0] and lo[1] < r[3] and hi[1] > r[2]):
                        continue
                    nxt = []
                    for piece in pieces:
                        outside, inside = cut_rect(piece, r)
                        nxt.extend(outside)
                    pieces = nxt
            for piece in pieces:
                self.faces.append((m, [v[0] for v in piece], [v[1] for v in piece], [v[2] for v in piece]))

    def clip_to_region(self, start):
        kept = self.faces[:start]
        for mat, pts, uvs, cols in self.faces[start:]:
            poly = [(pts[i], uvs[i], cols[i]) for i in range(len(pts))]
            for r in self.region_rects:
                outside, inside = cut_rect(poly, r)
                if inside:
                    kept.append((mat, [v[0] for v in inside], [v[1] for v in inside], [v[2] for v in inside]))
        self.faces = kept

    def cell(self, tx, tz):
        inx, inz = 0 <= tx < 32, 0 <= tz < 32
        if inx and not inz:
            side = 'N' if tz < 0 else 'S'
            if side in self.nb:
                return self.nb[side][max(0, 32 + tz) if tz < 0 else min(31, tz - 32)][tx]
        if inz and not inx:
            side = 'W' if tx < 0 else 'E'
            if side in self.nb:
                return self.nb[side][tz][max(0, 32 + tx) if tx < 0 else min(31, tx - 32)]
        return self.grid[min(31, max(0, tz))][min(31, max(0, tx))]

    def is_floor(self, tx, tz):
        return self.cell(tx, tz) == '.'

    @staticmethod
    def tile_rect(tx, tz):
        return (-HALF + T * tx, -HALF + T * (tx + 1), HALF - T * (tz + 1), HALF - T * tz)

    def height(self, x, y):
        tx, tz = int(math.floor((x + HALF) / T)), int(math.floor((HALF - y) / T))
        best = TOP
        for dz in range(-3, 4):
            for dx in range(-3, 4):
                if not self.is_floor(tx + dx, tz + dz):
                    continue
                x0, x1, y0, y1 = self.tile_rect(tx + dx, tz + dz)
                zx = elevation('E', x - x1) if x > x1 else (elevation('W', x0 - x) if x < x0 else FLOOR)
                zy = elevation('N', y - y1) if y > y1 else (elevation('S', y0 - y) if y < y0 else FLOOR)
                g = max(zx, zy)
                if g < best:
                    best = g
        return best

    def find_doors(self):
        found = []
        for tz in range(32):
            for tx in range(32):
                if self.grid[tz][tx] != 'D':
                    continue
                for name, (dx, dz) in (('N', (0, 1)), ('S', (0, -1)), ('E', (-1, 0)), ('W', (1, 0))):
                    xx, zz = tx + dx, tz + dz
                    if not (0 <= xx < 32 and 0 <= zz < 32) or self.grid[zz][xx] != '.':
                        continue
                    x0, x1, y0, y1 = self.tile_rect(tx, tz)
                    if name == 'N':
                        W, uc, axis = (lambda u, e, z, b=y0: (u, b + e, z)), (x0 + x1) / 2, 'x'
                    elif name == 'S':
                        W, uc, axis = (lambda u, e, z, b=y1: (u, b - e, z)), (x0 + x1) / 2, 'x'
                    elif name == 'E':
                        W, uc, axis = (lambda u, e, z, b=x0: (b + e, u, z)), (y0 + y1) / 2, 'y'
                    else:
                        W, uc, axis = (lambda u, e, z, b=x1: (b - e, u, z)), (y0 + y1) / 2, 'y'
                    d0 = uc - DOOR_W / 2
                    lower = PROF[name][1] - PROF[name][0]
                    a, b = W(d0, -DOOR_FLOOR_DEPTH, 0), W(d0 + DOOR_W, lower, 0)
                    rect = (min(a[0], b[0]), max(a[0], b[0]), min(a[1], b[1]), max(a[1], b[1]))
                    e_lines = [W(0, e, 0)[1 if axis == 'x' else 0] for e in (-DOOR_FLOOR_DEPTH, 0.0, lower)]
                    found.append({'tile': (tx, tz), 'name': name, 'W': W, 'd0': d0, 'axis': axis, 'rect': rect,
                                  'u_lines': (d0, d0 + DOOR_W), 'e_lines': e_lines})
                    break
        return found

    def in_door(self, x, y):
        for d in self.door_frames:
            x0, x1, y0, y1 = d['rect']
            if x0 + 1e-3 < x < x1 - 1e-3 and y0 + 1e-3 < y < y1 - 1e-3:
                return True
        return False

    def knot_lines(self):
        xs, ys = {-HALF, HALF}, {-HALF, HALF}
        for r in self.region_rects:
            xs.update((r[0], r[1]))
            ys.update((r[2], r[3]))
        if len(self.region) < 32 * 32:
            for m, cos, uvs, cols, n, lo, hi in source_tris(self.source):
                if m != 'ug_map_ground':
                    continue
                for c in cos:
                    if any(r[0] - 1e-3 <= c[0] <= r[1] + 1e-3 and r[2] - 1e-3 <= c[1] <= r[3] + 1e-3 for r in self.region_rects):
                        xs.add(c[0])
                        ys.add(c[1])
        for d in self.door_frames:
            (xs if d['axis'] == 'x' else ys).update(d['u_lines'])
            (ys if d['axis'] == 'x' else xs).update(d['e_lines'])
        for tz in range(32):
            for tx in range(-1, 32):
                a, b = self.is_floor(tx, tz), self.is_floor(tx + 1, tz)
                if a == b:
                    continue
                xb = -HALF + T * (tx + 1)
                name, sgn = ('E', 1) if a else ('W', -1)
                upper, total = PROF[name]
                xs.update((xb, xb + sgn * (total - upper), xb + sgn * total))
                if name == 'W':
                    xs.add(xb + SHADOW_WIDTH)
        for tx in range(32):
            for tz in range(-1, 32):
                a, b = self.is_floor(tx, tz), self.is_floor(tx, tz + 1)
                if a == b:
                    continue
                yb = HALF - T * (tz + 1)
                name, sgn = ('S', -1) if a else ('N', 1)
                upper, total = PROF[name]
                ys.update((yb, yb + sgn * (total - upper), yb + sgn * total))
                if name == 'N':
                    ys.add(yb - SHADOW_WIDTH)

        def clean(vals):
            out = []
            for v in sorted(v for v in vals if -HALF - 1e-6 <= v <= HALF + 1e-6):
                if not out or v - out[-1] > 0.05:
                    out.append(v)
            return out
        return clean(xs), clean(ys)

    def add_face(self, mat, pts, want, uvs, cols):
        n = tri_normal(pts[0], pts[1], pts[2])
        if len(pts) == 4:
            n = norm(cross(sub(pts[2], pts[0]), sub(pts[3], pts[1])))
        if dot(n, want) < 0:
            pts, uvs, cols = pts[::-1], uvs[::-1], cols[::-1]
        self.faces.append((mat, list(pts), list(uvs), list(cols)))

    def wall_distance(self, x, y, dx, dy):
        tx, tz = int(math.floor((x + HALF) / T)), int(math.floor((HALF - y) / T))
        for k in range(0, 3):
            nx, nz = tx + dx * k, tz - dy * k
            if not self.is_floor(nx, nz):
                x0, x1, y0, y1 = self.tile_rect(nx, nz)
                if dx > 0:
                    return x0 - x
                if dx < 0:
                    return x - x1
                if dy > 0:
                    return y0 - y
                return y1 - y
        return SHADOW_WIDTH * 4

    def floor_shade(self, x, y):
        west = max(0.0, 1.0 - max(0.0, self.wall_distance(x, y, -1, 0)) / SHADOW_WIDTH)
        north = max(0.0, 1.0 - max(0.0, self.wall_distance(x, y, 0, 1)) / SHADOW_WIDTH)
        s = 1.0 - SHADOW_EDGE * max(west, north) - SHADOW_CORNER * min(west, north)
        return (s, s, s)

    def terrain_face(self, pts):
        zs = [p[2] for p in pts]
        flat = max(zs) - min(zs) < 0.05
        if flat and abs(zs[0] - TOP) < 0.05:
            self.add_face('ug_map_wall', pts, (0, 0, 1), [(p[0] / 64.0, p[1] / 64.0) for p in pts], [BLACK] * len(pts))
            return
        if flat and abs(zs[0] - FLOOR) < 0.05:
            uvs = [sample('ug_map_ground', (p[0], p[1], FLOOR), (0, 0, 1))[0] for p in pts]
            self.add_face('ug_map_ground', pts, (0, 0, 1), uvs, [self.floor_shade(p[0] + (sum(q[0] for q in pts) / len(pts) - p[0]) * 0.001, p[1] + (sum(q[1] for q in pts) / len(pts) - p[1]) * 0.001) for p in pts])
            return
        n = tri_normal(pts[0], pts[1], pts[2])
        if n[2] < 0:
            n = mul(n, -1)
        if abs(n[0]) >= abs(n[1]):
            name = 'W' if n[0] > 0 else 'E'
        else:
            name = 'S' if n[1] > 0 else 'N'
        total = PROF[name][1]
        src, csrc = [], []
        lo_u, hi_u = LIB_RANGE[name]
        for p in pts:
            u = p[0] if name in 'NS' else p[1]
            d = total - inverse(name, p[2])
            src.append(LIB_WALL[name](u, d, p[2]))
            csrc.append(LIB_WALL[name](min(hi_u, max(lo_u, u)), d, p[2]))
        sn = tri_normal(src[0], src[1], src[2])
        if sn[2] < 0:
            sn = mul(sn, -1)
        uvs, cols = [], []
        for s, cs in zip(src, csrc):
            uv, c = sample('ug_map_wall', s, sn, cs)
            uvs.append(uv)
            cols.append(c)
        self.add_face('ug_map_wall', pts, (0, 0, 1), uvs, cols)

    def build_terrain(self):
        xs, ys = self.knot_lines()
        nx, ny = len(xs), len(ys)
        H = [[self.height(xs[i], ys[j]) for j in range(ny)] for i in range(nx)]
        plane = {}
        for i in range(nx - 1):
            for j in range(ny - 1):
                if self.in_door((xs[i] + xs[i + 1]) / 2, (ys[j] + ys[j + 1]) / 2):
                    continue
                if not self.in_region((xs[i] + xs[i + 1]) / 2, (ys[j] + ys[j + 1]) / 2):
                    continue
                h00, h10, h01, h11 = H[i][j], H[i + 1][j], H[i][j + 1], H[i + 1][j + 1]
                hc = self.height((xs[i] + xs[i + 1]) / 2, (ys[j] + ys[j + 1]) / 2)
                shaded = max(h00, h10, h01, h11) <= FLOOR + 0.01 and any(
                    self.floor_shade(px, py)[0] < 0.999 for px in (xs[i], xs[i + 1]) for py in (ys[j], ys[j + 1]))
                if shaded:
                    self.terrain_face([(xs[i], ys[j], h00), (xs[i + 1], ys[j], h10), (xs[i + 1], ys[j + 1], h11), (xs[i], ys[j + 1], h01)])
                    continue
                if abs((h00 + h11) - (h10 + h01)) < EPS and abs(hc - (h00 + h11) / 2) < 1e-3:
                    dx, dy = xs[i + 1] - xs[i], ys[j + 1] - ys[j]
                    b = (h10 - h00) / dx
                    c = (h01 - h00) / dy
                    a = h00 - b * xs[i] - c * ys[j]
                    plane[(i, j)] = (round(a, 3), round(b, 5), round(c, 5))
                else:
                    p00, p10 = (xs[i], ys[j], h00), (xs[i + 1], ys[j], h10)
                    p01, p11 = (xs[i], ys[j + 1], h01), (xs[i + 1], ys[j + 1], h11)
                    if abs((h00 + h11) / 2 - hc) <= abs((h10 + h01) / 2 - hc):
                        tris = ((p00, p10, p11), (p00, p11, p01))
                    else:
                        tris = ((p00, p10, p01), (p10, p11, p01))
                    for t in tris:
                        self.terrain_face(list(t))
        done = set()
        for j in range(ny - 1):
            for i in range(nx - 1):
                if (i, j) not in plane or (i, j) in done:
                    continue
                key = plane[(i, j)]
                i1 = i
                while i1 + 1 < nx - 1 and plane.get((i1 + 1, j)) == key and (i1 + 1, j) not in done:
                    i1 += 1
                j1 = j
                while j1 + 1 < ny - 1 and all(plane.get((k, j1 + 1)) == key and (k, j1 + 1) not in done for k in range(i, i1 + 1)):
                    j1 += 1
                for jj in range(j, j1 + 1):
                    for ii in range(i, i1 + 1):
                        done.add((ii, jj))
                pts = [(xs[i], ys[j], H[i][j]), (xs[i1 + 1], ys[j], H[i1 + 1][j]),
                       (xs[i1 + 1], ys[j1 + 1], H[i1 + 1][j1 + 1]), (xs[i], ys[j1 + 1], H[i][j1 + 1])]
                self.terrain_face(pts)

    def boundary_chains(self):
        edges = []
        for tz in range(32):
            for tx in range(-1, 32):
                a, b = self.is_floor(tx, tz), self.is_floor(tx + 1, tz)
                if a == b:
                    continue
                xb = -HALF + T * (tx + 1)
                edges.append(((xb, HALF - T * (tz + 1)), (xb, HALF - T * tz), 'E' if a else 'W'))
        for tx in range(32):
            for tz in range(-1, 32):
                a, b = self.is_floor(tx, tz), self.is_floor(tx, tz + 1)
                if a == b:
                    continue
                yb = HALF - T * (tz + 1)
                edges.append(((-HALF + T * tx, yb), (-HALF + T * (tx + 1), yb), 'S' if a else 'N'))
        adj = {}
        for i, (p, q, n) in enumerate(edges):
            adj.setdefault(p, []).append(i)
            adj.setdefault(q, []).append(i)
        used = set()

        def walk(e, pt):
            chain = []
            while e is not None and e not in used:
                used.add(e)
                p, q, n = edges[e]
                nxt = q if pt == p else p
                chain.append((pt, nxt, n))
                cands = [k for k in adj.get(nxt, []) if k not in used]
                if len(cands) == 1:
                    e = cands[0]
                elif cands:
                    perp = [k for k in cands if edges[k][2] != n]
                    e = perp[0] if perp else cands[0]
                else:
                    e = None
                pt = nxt
            return chain
        chains = []
        for p, lst in adj.items():
            if len(lst) == 1 and lst[0] not in used:
                chains.append((walk(lst[0], p), False))
        for i in range(len(edges)):
            if i not in used:
                ch = walk(i, edges[i][0])
                chains.append((ch, bool(ch) and ch[-1][1] == ch[0][0]))
        return chains

    @staticmethod
    def offset(chain, closed, which):
        merged = []
        for p, q, n in chain:
            if merged and merged[-1][2] == n:
                merged[-1] = (merged[-1][0], q, n)
            else:
                merged.append((p, q, n))
        if closed and len(merged) > 1 and merged[0][2] == merged[-1][2]:
            merged[0] = (merged[-1][0], merged[0][1], merged[0][2])
            merged.pop()

        def line(seg):
            p, q, n = seg
            e = RAIL_E[n][which]
            d = DIRS[n]
            return ('x', p[0] + d[0] * e) if n in 'EW' else ('y', p[1] + d[1] * e)
        pts = []
        if not closed:
            ax, v = line(merged[0])
            p = merged[0][0]
            pts.append((v, p[1]) if ax == 'x' else (p[0], v))
        for i in range(len(merged) - (0 if closed else 1)):
            a, b = merged[i], merged[(i + 1) % len(merged)]
            la, lb = line(a), line(b)
            if la[0] == lb[0]:
                p = a[1]
                pts.append((la[1], p[1]) if la[0] == 'x' else (p[0], la[1]))
                continue
            pts.append((la[1] if la[0] == 'x' else lb[1], la[1] if la[0] == 'y' else lb[1]))
        if not closed:
            ax, v = line(merged[-1])
            q = merged[-1][1]
            pts.append((v, q[1]) if ax == 'x' else (q[0], v))
        else:
            pts.append(pts[0])
        return pts

    @staticmethod
    def rail_sample(a, s, z, nrm):
        return sample('pasted__ug_map_s', (-192.0 + a, -200.0 + s, z), nrm)

    def build_rails(self):
        clip = lambda pts: [(min(HALF, max(-HALF, p[0])), min(HALF, max(-HALF, p[1]))) for p in pts]
        for chain, closed in self.boundary_chains():
            if not chain:
                continue
            inner = clip(self.offset(chain, closed, 0))
            outer = clip(self.offset(chain, closed, 1))
            s = 0.0
            for i in range(len(inner) - 1):
                a0, a1 = inner[i], inner[i + 1]
                b0, b1 = outer[i], outer[i + 1]
                seg = math.hypot(a1[0] - a0[0], a1[1] - a0[1])
                if seg < 1e-4 and math.hypot(b1[0] - b0[0], b1[1] - b0[1]) < 1e-4:
                    continue
                if math.hypot(b0[0] - a0[0], b0[1] - a0[1]) < 1e-3 and math.hypot(b1[0] - a1[0], b1[1] - a1[1]) < 1e-3:
                    s += seg
                    continue
                into = norm((b0[0] - a0[0], b0[1] - a0[1], 0.0))
                uvs, cols = [], []
                for a, sv in ((RAIL_T, s), (RAIL_T, s + seg), (0.0, s + seg), (0.0, s)):
                    uv, c = self.rail_sample(a, sv, RAIL_HI, (0, 0, 1))
                    uvs.append(uv)
                    cols.append(c)
                top = [(p[0], p[1], RAIL_HI) for p in (a0, a1, b1, b0)]
                self.add_face('pasted__ug_map_s', top, (0, 0, 1), uvs, cols)
                for (p0, p1), a, want, sn in (((a0, a1), RAIL_T, mul(into, -1), (1, 0, 0)), ((b0, b1), 0.0, into, (-1, 0, 0))):
                    pts = [(p0[0], p0[1], RAIL_LO), (p1[0], p1[1], RAIL_LO), (p1[0], p1[1], RAIL_HI), (p0[0], p0[1], RAIL_HI)]
                    uvs, cols = [], []
                    for sv, z in ((s, RAIL_LO), (s + seg, RAIL_LO), (s + seg, RAIL_HI), (s, RAIL_HI)):
                        uv, c = self.rail_sample(a, sv, z, sn)
                        uvs.append(uv)
                        cols.append(c)
                    self.add_face('pasted__ug_map_s', pts, want, uvs, cols)
                s += seg

    def build_doors(self):
        for d in self.door_frames:
            W, name, d0 = d['W'], d['name'], d['d0']
            U = sub(W(1, 0, 0), W(0, 0, 0))
            E = sub(W(0, 1, 0), W(0, 0, 0))
            for tri in DOOR_PIECE:
                pts = []
                for u, e, h in tri['pts']:
                    if tri['kind'] == 'door_floor':
                        pts.append(W(d0 + u, e, FLOOR))
                    elif tri['kind'] == 'door_front':
                        pts.append(W(d0 + u, inverse(name, FLOOR + h), FLOOR + h))
                    else:
                        pts.append(W(d0 + u, e, FLOOR + h))
                n = tri['normal']
                want = add(add(mul(U, n[0]), mul(E, n[1])), (0.0, 0.0, n[2]))
                mat = 'ug_door_floor' if tri['kind'] == 'door_floor' else 'ug_door'
                self.add_face(mat, pts, want, [tuple(v) for v in tri['uvs']], [tuple(c) for c in tri['cols']])
            self.doors.append({'tile': list(d['tile']), 'facing': name})

    def build(self):
        self.keep_source()
        start = len(self.faces)
        self.build_terrain()
        rails = len(self.faces)
        self.build_rails()
        self.clip_to_region(rails)
        self.match_faces(start)
        self.build_doors()
        fixed = []
        for mat, pts, uvs, cols in self.faces:
            su = math.floor(min(u[0] for u in uvs))
            sv = 0 if mat == 'ug_map_wall' else math.floor(min(u[1] for u in uvs))
            fixed.append((mat, pts, [(u[0] - su, u[1] - sv) for u in uvs], cols))
        self.faces = fixed

    def collision(self):
        out = bytearray()
        for tz in range(32):
            for tx in range(32):
                out += struct.pack('<H', COLLISION.get(self.grid[tz][tx], 0x8000))
        return bytes(out)


def f6(v):
    return '%.6f' % v


def texture_xml(index, name, original_height=None, path=None):
    w, h, px = read_png(path or os.path.join(ASSETS, name + '.png'))
    alphas = set(a for row in px for r, g, b, a in row)
    rgb = set(((r >> 3) | ((g >> 3) << 5) | ((b >> 3) << 10)) for row in px for r, g, b, a in row if a > 0)
    if any(0 < a < 255 for a in alphas) and 255 in alphas and len(rgb) <= 32:
        colors = sorted(rgb)
        index_of = {c: i for i, c in enumerate(colors)}
        data = bytearray()
        for row in px:
            for r, g, b, a in row:
                c = (r >> 3) | ((g >> 3) << 5) | ((b >> 3) << 10)
                data.append((index_of.get(c, 0) if a > 0 else 0) | (int(round(a * 7 / 255.0)) << 5))
        colors = (colors + [0] * 32)[:32]
        bitmap = ' '.join('%02x%02x' % (data[k + 1], data[k]) for k in range(0, len(data), 2))
        tex = ('      <tex_image index="%d" name="%s" width="%d" height="%d" original_width="%d" original_height="%d" format="a3i5" '
               'color0_mode="color" palette_name="%s_pl" path="">\n        <bitmap size="%d">%s</bitmap>\n      </tex_image>'
               % (index, name, w, h, w, original_height or h, name, len(data) // 2, bitmap))
        pal = '      <tex_palette index="%d" name="%s_pl" color_size="32">%s</tex_palette>' % (index, name, ' '.join('%04x' % c for c in colors))
        return tex, pal, w, h
    transparent = any(a == 0 for row in px for r, g, b, a in row)
    colors, data = ([-1] if transparent else []), bytearray()
    flat = []
    for row in px:
        for r, g, b, a in row:
            c = -1 if transparent and a < 128 else (r >> 3) | ((g >> 3) << 5) | ((b >> 3) << 10)
            if c not in colors:
                colors.append(c)
            flat.append(c)
    fmt, bpp, size = ('palette16', 4, 16) if len(colors) <= 16 else ('palette256', 8, 256)
    colors = (colors + [0] * size)[:size]
    index_of = {c: i for i, c in enumerate(colors)}
    acc = nbits = 0
    for c in flat:
        acc |= index_of.get(c, 0) << nbits
        nbits += bpp
        if nbits == 8:
            data.append(acc)
            acc = nbits = 0
    bitmap = ' '.join('%02x%02x' % (data[k + 1], data[k]) for k in range(0, len(data), 2))
    tex = ('      <tex_image index="%d" name="%s" width="%d" height="%d" original_width="%d" original_height="%d" format="%s" '
           'color0_mode="%s" palette_name="%s_pl" path="">\n        <bitmap size="%d">%s</bitmap>\n      </tex_image>'
           % (index, name, w, h, w, original_height or h, fmt, 'transparency' if transparent else 'color', name, len(data) // 2, bitmap))
    pal = '      <tex_palette index="%d" name="%s_pl" color_size="%d">%s</tex_palette>' % (index, name, size, ' '.join('%04x' % max(c, 0) for c in colors))
    return tex, pal, w, h


def convex_quad(q):
    pts = [v[0] for v in q]
    n = cross(sub(pts[1], pts[0]), sub(pts[2], pts[0]))
    length = math.sqrt(dot(n, n))
    if length < 1e-6:
        return False
    n = mul(n, 1.0 / length)
    if abs(dot(sub(pts[3], pts[0]), n)) > 0.01:
        return False
    for k in range(4):
        a, b, c = pts[k], pts[(k + 1) % 4], pts[(k + 2) % 4]
        if dot(cross(sub(b, a), sub(c, b)), n) <= 1e-6:
            return False
    return True


def pair_quad(t1, t2):
    (a, b, c), (a2, c2, d) = t1, t2
    if a[0] != a2[0] or c[0] != c2[0] or a[2] != a2[2] or c[2] != c2[2]:
        return None
    du, dv = a2[1][0] - a[1][0], a2[1][1] - a[1][1]
    if abs(du - round(du)) > 1e-6 or abs(dv - round(dv)) > 1e-6:
        return None
    if abs(c2[1][0] - c[1][0] - du) > 1e-6 or abs(c2[1][1] - c[1][1] - dv) > 1e-6:
        return None
    q = [a, b, c, (d[0], (d[1][0] - du, d[1][1] - dv), d[2])]
    return q if convex_quad(q) else None


def write_imd(block, path, materials=None, texture_paths=None):
    tex_xml, pal_xml, mat_xml, poly_xml, disp_xml = [], [], [], [], []
    total_v = total_t = total_q = 0
    lo, hi = [1e9] * 3, [-1e9] * 3
    used = [m for m in (materials or MATERIALS) if any(f[0] == m[0] for f in block.faces)]
    for i, (mname, tname, pid, emit) in enumerate(used):
        tex, pal, w, h = texture_xml(i, tname, path=(texture_paths or {}).get(tname))
        alphas = set(a for row in read_png((texture_paths or {}).get(tname) or os.path.join(ASSETS, tname + '.png'))[2] for r, g, b, a in row)
        alpha = max(1, int(round(min(alphas) * 31 / 255.0))) if len(alphas) == 1 and 0 < min(alphas) < 255 else 31
        h = USED_HEIGHT.get(tname, h)
        tex_xml.append(tex)
        pal_xml.append(pal)
        mat_xml.append('      <material index="%d" name="%s" light0="off" light1="off" light2="off" light3="off" face="front" alpha="%d" '
                       'wire_mode="off" polygon_mode="modulate" polygon_id="%d" fog_flag="on" depth_test_decal="off" '
                       'translucent_update_depth="off" render_1_pixel="off" far_clipping="off" diffuse="31 31 31" ambient="0 0 0" '
                       'specular="0 0 0" emission="%d %d %d" shininess_table_flag="off" tex_image_idx="%d" tex_palette_idx="%d" '
                       'tex_tiling="repeat repeat" tex_scale="1.000000 1.000000" tex_rotate="0.000000" tex_translate="0.000000 0.000000" '
                       'tex_gen_mode="none"/>' % (i, mname, alpha, pid if alpha == 31 else 10 + i, emit, emit, emit, i, i))
        tri_list, quad_list = [], []
        pending = None
        for mat, pts, uvs, cols in block.faces:
            if mat != mname:
                continue
            verts = [(tuple(pts[j]), tuple(uvs[j][:2]), tuple(cols[j])) for j in range(len(pts))]
            if len(verts) == 4 and convex_quad(verts):
                quad_list.append(verts)
                continue
            for k in range(1, len(verts) - 1):
                t = (verts[0], verts[k], verts[k + 1])
                if pending is not None:
                    q = pair_quad(pending, t)
                    if q:
                        quad_list.append(q)
                        pending = None
                        continue
                    tri_list.append(pending)
                pending = t
        if pending is not None:
            tri_list.append(pending)
        last_clr = [None]

        def emit(group):
            cmds = []
            for poly in group:
                for p, uv, col in poly:
                    ds = (p[0], p[2], -p[1])
                    for a in range(3):
                        lo[a] = min(lo[a], ds[a])
                        hi[a] = max(hi[a], ds[a])
                    cmds.append('            <tex st="%s %s"/>' % (f6(uv[0] * w), f6((1.0 - uv[1]) * h)))
                    clr = tuple(max(0, min(31, int(round(c * 31)))) for c in col)
                    if clr != last_clr[0]:
                        cmds.append('            <clr rgb="%d %d %d"/>' % clr)
                        last_clr[0] = clr
                    cmds.append('            <pos_xyz xyz="%s %s %s"/>' % tuple(f6(a / 64.0) for a in ds))
            return cmds
        prim_xml = []
        for kind, group, nv in (('triangles', tri_list, 3), ('quads', quad_list, 4)):
            if not group:
                continue
            last_clr[0] = None
            prim_xml.append('            <primitive index="%d" type="%s" vertex_size="%d">\n            <mtx idx="0"/>\n%s\n            </primitive>'
                            % (len(prim_xml), kind, len(group) * nv, '\n'.join(emit(group))))
        ntri, nquad = len(tri_list), len(quad_list)
        nvert = ntri * 3 + nquad * 4
        total_v += nvert
        total_t += ntri
        total_q += nquad
        prims = ('          <primitive_array size="%d">\n%s\n          </primitive_array>\n' % (len(prim_xml), '\n'.join(prim_xml)))
        poly_xml.append('      <polygon index="%d" name="polygon%d" vertex_size="%d" polygon_size="%d" triangle_size="%d" quad_size="%d" '
                        'volume_min="0.000000 0.000000 0.000000" volume_max="0.000000 0.000000 0.000000" volume_r="0.000000" '
                        'mtx_prim_size="1" nrm_flag="off" clr_flag="on" tex_flag="on">\n        <mtx_prim index="0">\n'
                        '          <mtx_list size="1">0</mtx_list>\n%s        </mtx_prim>\n      </polygon>'
                        % (i, i, nvert, ntri + nquad, ntri, nquad, prims))
        disp_xml.append('        <display index="%d" material="%d" polygon="%d" priority="0"/>' % (i, i, i))
    n = len(used)
    lo = [v / 64.0 for v in lo]
    hi = [v / 64.0 for v in hi]
    big = max([abs(v) for v in lo + hi] + [hi[a] - lo[a] for a in range(3)])
    bscale = 0
    while big / (2.0 ** bscale) > 7.9:
        bscale += 1
    bf = 2.0 ** bscale
    box = 'pos_scale="%d" xyz="%s %s %s" whd="%s %s %s"' % ((bscale,) + tuple(f6(v / bf) for v in lo) + tuple(f6((hi[a] - lo[a]) / bf) for a in range(3)))
    head = ('<create user="unknown" host="unknown" date="2026-01-01T00:00:00" source="%s"/>' % block.name)
    xml = '\n'.join([
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<imd version="1.6.0">',
        '  <head>',
        '    ' + head,
        '    <title>Model Data for NINTENDO NITRO-System</title>',
        '    <generator name="underground_block_builder" version="1.0"/>',
        '  </head>',
        '  <body>',
        '    <original_' + head[1:],
        '    <original_generator name="underground_block_builder" version="1.0"/>',
        '    <model_info pos_scale="6" scaling_rule="standard" vertex_style="direct" magnify="1.000000" tool_start_frame="1" '
        'tex_matrix_mode="maya" compress_node="merge" node_size="1 1" compress_material="on" material_size="%d %d" '
        'output_texture="used" force_full_weight="off" use_primitive_strip="on"/>' % (n, n),
        '    <box_test %s/>' % box,
        '    <tex_image_array size="%d">' % n, '\n'.join(tex_xml), '    </tex_image_array>',
        '    <tex_palette_array size="%d">' % n, '\n'.join(pal_xml), '    </tex_palette_array>',
        '    <material_array size="%d">' % n, '\n'.join(mat_xml), '    </material_array>',
        '    <matrix_array size="1">', '      <matrix index="0" mtx_weight="1" node_idx="0"/>', '    </matrix_array>',
        '    <polygon_array size="%d">' % n, '\n'.join(poly_xml), '    </polygon_array>',
        '    <node_array size="1">',
        '      <node index="0" name="world_root" kind="mesh" parent="-1" child="-1" brother_next="-1" brother_prev="-1" draw_mtx="on" '
        'billboard="off" scale="1.000000 1.000000 1.000000" rotate="0.000000 0.000000 0.000000" translate="0.000000 0.000000 0.000000" '
        'visibility="on" display_size="%d" vertex_size="%d" polygon_size="%d" triangle_size="%d" quad_size="%d" '
        'volume_min="0.000000 0.000000 0.000000" volume_max="0.000000 0.000000 0.000000" volume_r="0.000000">' % (n, total_v, total_t + total_q, total_t, total_q),
        '\n'.join(disp_xml),
        '      </node>',
        '    </node_array>',
        '    <output_info vertex_size="%d" polygon_size="%d" triangle_size="%d" quad_size="%d"/>' % (total_v, total_t + total_q, total_t, total_q),
        '  </body>',
        '</imd>', ''])
    open(path, 'w', encoding='utf-8').write(xml)
    return total_t + 2 * total_q


def find_converter():
    env = os.environ.get('G3DCVTR')
    if env and os.path.exists(env):
        return env
    home = os.path.expanduser('~')
    for pattern in ('Desktop/*/bin/converter/g3dcvtr.exe', 'Desktop/*/*/*/bin/converter/g3dcvtr.exe',
                    'Desktop/*/*/bin/converter/g3dcvtr.exe', 'Desktop/*/converter/g3dcvtr.exe'):
        hits = glob.glob(os.path.join(home, pattern))
        if hits:
            return hits[0]
    return None


def build_block(tiles, name, out_dir, neighbours=None, quiet=False, source=None, neighbour_sources=None):
    block = Block(tiles, name, neighbours, source, neighbour_sources)
    block.build()
    os.makedirs(out_dir, exist_ok=True)
    base = os.path.join(out_dir, name)
    perm = block.collision()
    open(base + '_collision.bin', 'wb').write(perm)
    tris = write_imd(block, base + '.imd')
    info = {'name': name, 'triangles': tris, 'doors': block.doors}
    blob = None
    conv = find_converter()
    if conv:
        if os.path.exists(base + '.nsbmd'):
            os.remove(base + '.nsbmd')
        run = subprocess.run([conv, os.path.abspath(base + '.imd'), '-emdl', '-o', os.path.abspath(base + '.nsbmd')],
                             cwd=os.path.dirname(conv), capture_output=True, text=True)
        if os.path.exists(base + '.nsbmd'):
            model = open(base + '.nsbmd', 'rb').read()
            bdhc = open(os.path.join(ASSETS, 'reference.bdhc'), 'rb').read()
            blob = struct.pack('<4I', len(perm), 0, len(model), len(bdhc)) + perm + model + bdhc
            open(base + '_map_data.bin', 'wb').write(blob)
            info['nsbmd_bytes'] = len(model)
            info['map_data_bytes'] = len(blob)
        else:
            print('g3dcvtr failed for %s:' % name)
            print(run.stdout)
            print(run.stderr)
    else:
        print('g3dcvtr.exe not found; set G3DCVTR to its path to get .nsbmd and map_data output')
    json.dump(info, open(base + '_info.json', 'w'), indent=2)
    if not quiet:
        print('built %s: %d triangles, %d door(s)%s' % (name, tris, len(block.doors),
                                                         ', %d byte map_data' % len(blob) if blob else ''))
    return blob, info


def main():
    args = sys.argv[1:]
    if not args:
        print('usage: underground_block_builder.py block.json [output_dir]')
        return 1
    layout = json.load(open(args[0]))
    out_dir = args[1] if len(args) > 1 else os.path.dirname(os.path.abspath(args[0]))
    name = layout.get('name') or os.path.splitext(os.path.basename(args[0]))[0]
    source = layout.get('source')
    if source is None:
        found = re.match(r'block_(\d+)', name)
        source = int(found.group(1)) if found else None
    build_block(layout['tiles'], name, out_dir, layout.get('neighbours'), source=source,
                neighbour_sources=layout.get('neighbour_sources'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
