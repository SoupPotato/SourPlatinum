import json
import math
import os
import struct
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import underground_block_builder as B

KIT = json.load(open(os.path.join(B.ASSETS, 'cave_kit.json')))
EDGES = json.load(open(os.path.join(B.ASSETS, 'ground_edges.json')))
WATER_KIT = json.load(open(os.path.join(B.ASSETS, 'water_kit.json')))
BANK_TEXTURE = WATER_KIT['bank']
WATER_SHADE = 0.81
SYMMETRIES = [(1, 0, 0, 1), (0, -1, 1, 0), (-1, 0, 0, -1), (0, 1, -1, 0), (-1, 0, 0, 1), (1, 0, 0, -1), (0, 1, 1, 0), (0, -1, -1, 0)]


def transformed_sig(sig, m):
    a, b, c, d = m
    out = [''] * 9
    for i in range(9):
        dx, dy = i % 3 - 1, i // 3 - 1
        tx, ty = a * dx + b * dy, c * dx + d * dy
        out[(ty + 1) * 3 + tx + 1] = sig[i]
    return ''.join(out)


def untransform(tris, m):
    a, b, c, d = m
    det = a * d - b * c
    ia, ib, ic, id_ = d / det, -b / det, -c / det, a / det
    out = []
    for t in tris:
        pts = []
        for p in t['p']:
            gx, gy = p[0] - 8.0, -(p[1] - 8.0)
            ux, uy = ia * gx + ib * gy, ic * gx + id_ * gy
            pts.append([ux + 8.0, -uy + 8.0, p[2]])
        uv, col = list(t['uv']), list(t['c'])
        if det < 0:
            pts = [pts[0], pts[2], pts[1]]
            uv = [uv[0], uv[2], uv[1]]
            col = [col[0], col[2], col[1]]
        out.append(dict(t, p=pts, uv=uv, c=col))
    return out
EDGE_OF = {f: v['edge'] for f, v in EDGES['families'].items()}
EDGE_NEIGHBOURS = [tuple(n) for n in EDGES['neighbours']]


def canonical_mask(mask):
    m = list(mask)
    for d, a, b in ((0, 1, 3), (2, 1, 4), (5, 3, 6), (7, 4, 6)):
        if m[a] == '1' or m[b] == '1':
            m[d] = '0'
    return ''.join(m)


def bilinear(corners, x, y):
    s, t = x / B.T, y / B.T
    nw, ne, se, sw = corners
    return tuple(nw[k] * (1 - s) * t + ne[k] * s * t + se[k] * s * (1 - t) + sw[k] * (1 - s) * (1 - t) for k in range(2))
BIOMES = json.load(open(os.path.join(B.ASSETS, 'hideaway_biomes.json')))
TEX_DIR = os.path.join(B.ASSETS, 'hideaway_textures')
FLOOR_LEVEL = 16.0
STOREY = 16.0
COLL_FLOOR = 0x0008
COLL_BLOCK = 0x8000
WALL_TEXTURES = ['dun_wall_n', 'dun_wall_s', 'dun_wall_e', 'dun_wall_w', 'dun_wall_c', 'dun_floor', 'dun_floor2']
DOOR_TEXTURES = ['dun_dhole', 'dun_ent2']
BASE_FLOORS = ('dun_floor', 'dun_floor3', 'dun_floor4')
TOP_FLOORS = ('dun_floor2', 'black')
FRONT_TO_DOOR = {(0, 1): 'N', (0, -1): 'S', (1, 0): 'W', (-1, 0): 'E'}
STEP_BACK = {'N': 'South', 'S': 'North', 'W': 'East', 'E': 'West'}
WEIGHTS = [1, 2, 1, 2, 0, 2, 1, 2, 1]
ROCK_TOP = 'rock'
OBJ_DIR = os.path.join(B.ASSETS, 'hideaway_objects')
_OBJECTS = {}


def object_mesh(key):
    if key not in _OBJECTS:
        path = os.path.join(OBJ_DIR, key + '.json')
        _OBJECTS[key] = json.load(open(path)) if os.path.exists(path) else None
    return _OBJECTS[key]


def footprint(o):
    mesh = object_mesh(o['key'])
    w, h = (mesh['w'], mesh['h']) if mesh else (o.get('w', 1), o.get('h', 1))
    return (h, w) if o.get('rot', 0) % 2 else (w, h)
DEFAULT_ROCK_HEIGHT = 2
MAX_HEIGHT = 4
NEIGHBOURS = [(dx, dy) for dy in (-1, 0, 1) for dx in (-1, 0, 1)]


def invariant(tris, axis):
    if not tris:
        return False
    ends = ({}, {})
    for t in tris:
        for p, c in zip(t['p'], t['c']):
            v = p[axis]
            if abs(v) < 1e-3:
                side = 0
            elif abs(v - B.T) < 1e-3:
                side = 1
            else:
                return False
            rest = tuple(round(p[k], 2) for k in range(3) if k != axis) + tuple(round(x, 2) for x in c)
            ends[side][rest] = True
    return set(ends[0]) == set(ends[1])


def stretch(tris, axis, n):
    if n == 1:
        return tris
    out = []
    for t in tris:
        pts, uvs = [], []
        for i, p in enumerate(t['p']):
            if abs(p[axis] - B.T) < 1e-3:
                q = list(p)
                q[axis] = 0.0
                l = B.barycentric(tuple(q), *[tuple(v) for v in t['p']])
                base = [sum(l[k] * t['uv'][k][j] for k in range(3)) for j in range(2)]
                uvs.append([base[j] + (t['uv'][i][j] - base[j]) * n for j in range(2)])
                q[axis] = B.T * n
                pts.append(q)
            else:
                pts.append(list(p))
                uvs.append(list(t['uv'][i]))
        out.append(dict(t, p=pts, uv=uvs))
    return out


class Faces:
    def __init__(self, name):
        self.name = name
        self.faces = []


def normalise(data):
    biome = BIOMES[data['biome']]
    tiles = [list(r) for r in data['tiles']]
    h, w = len(tiles), len(tiles[0])
    palette = list(data.get('palette') or [biome['floor'], biome['floor2'], biome['liquid']])
    heights = data.get('heights')
    paint = data.get('paint')
    legacy = {'.': biome['floor'], ',': biome['floor2'], '~': biome['liquid']}

    def index(name):
        if name not in palette:
            palette.append(name)
        return palette.index(name)
    H = [[0] * w for _ in range(h)]
    P = [[None] * w for _ in range(h)]
    for r in range(h):
        for c in range(w):
            ch = tiles[r][c]
            if ch == ',':
                tiles[r][c] = '.'
            hv = heights[r][c] if heights else None
            if tiles[r][c] in '#X':
                H[r][c] = int(hv) if hv and hv.isdigit() and int(hv) > 0 else DEFAULT_ROCK_HEIGHT
            elif tiles[r][c] == '~':
                H[r][c] = int(hv) if hv and hv.isdigit() else 0
            pv = paint[r][c] if paint else None
            if pv is not None and pv != '-' and pv != ' ':
                P[r][c] = palette[int(pv, 36)]
            elif pv is None and ch in legacy:
                P[r][c] = legacy[ch]
            elif ch in '.~' and pv is None:
                P[r][c] = legacy[ch]
            if tiles[r][c] in '.~' and P[r][c] is None:
                P[r][c] = legacy[tiles[r][c]]
            if P[r][c] and P[r][c].startswith('@'):
                P[r][c] = biome[P[r][c][1:]]
    return tiles, H, P


class Hideaway:
    def __init__(self, data):
        self.name = data['name']
        self.biome_key = data['biome']
        self.biome = BIOMES[data['biome']]
        self.grid, self.height, self.paint = normalise(data)
        self.h = len(self.grid)
        self.w = len(self.grid[0])
        if self.w not in (32, 64) or self.h not in (32, 64) or any(len(r) != self.w for r in self.grid):
            raise ValueError('hideaway must be 32x32 or 64x64 tiles')
        self.objects = data.get('objects', [])
        self.levels()
        self.missing = {}
        self.warnings = []
        self.exits = []

    def inside(self, c, r):
        return 0 <= c < self.w and 0 <= r < self.h

    def at(self, c, r):
        return self.grid[r][c] if self.inside(c, r) else '#'

    def levels(self):
        w, h = self.w, self.h
        L = [[0] * w for _ in range(h)]
        U = [[0] * w for _ in range(h)]
        for r in range(h):
            for c in range(w):
                t = self.grid[r][c]
                if t in '#X':
                    L[r][c] = self.height[r][c]
                elif t == '~':
                    U[r][c] = self.height[r][c]
        changed = True
        while changed:
            changed = False
            for r in range(h):
                for c in range(w):
                    t = self.grid[r][c]
                    if t in '#X':
                        low = min([max(L[r + dy][c + dx], 0) for dx, dy in NEIGHBOURS
                                   if (dx or dy) and self.inside(c + dx, r + dy)] or [L[r][c]])
                        v = min(self.height[r][c], low + 1)
                        if v != L[r][c]:
                            L[r][c] = v
                            changed = True
                    elif t == '~':
                        low = min([(U[r + dy][c + dx] if self.grid[r + dy][c + dx] == '~' else -1) for dx, dy in NEIGHBOURS
                                   if (dx or dy) and self.inside(c + dx, r + dy)] or [U[r][c]])
                        v = min(self.height[r][c], low + 1)
                        if v != U[r][c]:
                            U[r][c] = v
                            changed = True
        for r in range(h):
            for c in range(w):
                if self.grid[r][c] == '~':
                    L[r][c] = -U[r][c]
        self.L = L
        self.slope = [[any(self.inside(c + dx, r + dy) and L[r + dy][c + dx] < L[r][c] for dx, dy in NEIGHBOURS)
                       for c in range(w)] for r in range(h)]

    def info(self, c, r):
        if not self.inside(c, r):
            return None
        return self.L[r][c], self.slope[r][c]

    def code(self, c, r):
        here = self.info(c, r)
        level, slope = here
        if slope:
            base = level - 1
            low_flat = any(self.info(c + dx, r + dy) == (base, False) for dx, dy in NEIGHBOURS if dx or dy)
            centre, o = (1, base) if low_flat else (2, base - 1)
        else:
            centre, o = 0, level
        sig = []
        for dx, dy in NEIGHBOURS:
            if not dx and not dy:
                sig.append(str(centre))
                continue
            n = self.info(c + dx, r + dy)
            if n is None:
                sig.append('3')
                continue
            rel = n[0] - o
            if n[1]:
                v = max(0, min(3, rel))
            elif rel <= 0:
                v = 0
            elif rel == 1:
                v = 2 if centre != 2 else 1
            else:
                v = 3
            sig.append(str(v))
        return ''.join(sig), o

    def piece(self, sig):
        pieces = KIT['pieces']
        if sig in pieces:
            return pieces[sig]['tris']
        self.missing[sig] = self.missing.get(sig, 0) + 1
        best = None
        for cand in pieces:
            if cand[4] != sig[4]:
                continue
            score = sum(w * abs(int(a) - int(b)) for w, a, b in zip(WEIGHTS, cand, sig))
            if best is None or score < best[0]:
                best = (score, cand)
        if best is None:
            return []
        return pieces[best[1]]['tris']

    def paint_at(self, c, r, level):
        if self.info(c, r) == (level, False) and self.paint[r][c]:
            return self.paint[r][c]
        for k in range(1, 5):
            for dy in range(-k, k + 1):
                for dx in range(-k, k + 1):
                    if max(abs(dx), abs(dy)) != k:
                        continue
                    if self.info(c + dx, r + dy) == (level, False) and self.paint[r + dy][c + dx]:
                        return self.paint[r + dy][c + dx]
        return self.paint[r][c] or self.biome['floor']

    def is_water(self, c, r):
        return self.inside(c, r) and self.grid[r][c] == '~' and self.L[r][c] == 0 and not self.slope[r][c]

    def water_sig(self, c, r):
        if self.grid[r][c] not in '.~' or self.L[r][c] != 0 or self.slope[r][c]:
            return None
        sig = ''
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if self.inside(c + dx, r + dy) and self.L[r + dy][c + dx] != 0:
                    return None
                sig += 'w' if self.is_water(c + dx, r + dy) else 'l'
        return sig if 'w' in sig else None

    def water_piece(self, sig, kit='sea'):
        pieces = WATER_KIT['kits'][kit]['pieces']
        best = None
        for m in SYMMETRIES:
            t = transformed_sig(sig, m)
            if t in pieces and (best is None or pieces[t]['count'] > pieces[best[0]]['count']):
                best = (t, m)
        if best:
            return untransform(pieces[best[0]]['tris'], best[1])
        self.missing[sig] = self.missing.get(sig, 0) + 1
        best = None
        for cand in pieces:
            if cand[4] != sig[4]:
                continue
            score = sum(w for w, a, b in zip(WEIGHTS, cand, sig) if a != b)
            if best is None or score < best[0]:
                best = (score, cand)
        return pieces[best[1]]['tris'] if best else []

    def nearest_paint(self, c, r, kind):
        if self.grid[r][c] == kind and self.paint[r][c]:
            return self.paint[r][c]
        for k in range(1, 5):
            for dy in range(-k, k + 1):
                for dx in range(-k, k + 1):
                    if max(abs(dx), abs(dy)) == k and self.inside(c + dx, r + dy) and self.grid[r + dy][c + dx] == kind and self.paint[r + dy][c + dx]:
                        return self.paint[r + dy][c + dx]
        return self.biome['liquid' if kind == '~' else 'floor']

    def resolve_water(self, c, r, sig):
        out = []
        liquid = self.nearest_paint(c, r, '~')
        kit = liquid if liquid in WATER_KIT['kits'] else 'sea'
        for t in self.water_piece(sig, kit):
            mat, world = t['m'], False
            if mat == 'floor':
                mat, world = self.nearest_paint(c, r, '.'), True
            elif mat == 'water':
                mat, world = liquid, True
            elif mat in ('puddle_b',):
                world = True
            uv = [(u, 1.0 - v) for u, v in t['uv']] if mat in EDGE_OF.values() else t['uv']
            shade = 1.0 if t['m'] in ('water', 'puddle_b') else WATER_SHADE
            cols = [[v * shade for v in col] for col in t['c']]
            out.append({'m': mat, 'p': t['p'], 'uv': uv, 'c': cols, 'w': world})
        return out

    def edge_for(self, c, r):
        if self.grid[r][c] != '.' or self.L[r][c] != 0 or self.slope[r][c] or self.paint[r][c] in EDGE_OF:
            return None
        best = None
        for fam in EDGE_OF:
            mask = ''.join('1' if self.info(c + dx, r + dy) == (0, False) and self.grid[r + dy][c + dx] == '.' and self.paint[r + dy][c + dx] == fam else '0'
                           for dx, dy in EDGE_NEIGHBOURS)
            n = mask.count('1')
            if n and (best is None or n > best[0]):
                best = (n, fam, mask)
        if best is None:
            return None
        fam, mask = best[1], best[2]
        entry = EDGES['families'][fam]['masks'].get(mask) or EDGES['canonical'].get(canonical_mask(mask))
        if entry is None:
            return ('fill', fam)
        corners = entry.get('%d%d' % (c % 2, r % 2)) or next(iter(entry.values()))
        return (EDGE_OF[fam], corners)

    def resolve(self, c, r):
        level, slope = self.L[r][c], self.slope[r][c]
        wsig = self.water_sig(c, r)
        if wsig:
            return self.resolve_water(c, r, wsig)
        if not slope and self.grid[r][c] in '#X' and not self.paint[r][c]:
            return []
        sig, o = self.code(c, r)
        out = []
        top_paint = self.paint[r][c] if self.grid[r][c] in '#X' else None
        edge = self.edge_for(c, r)
        for t in self.piece(sig):
            mat, cols = t['m'], t['c']
            zs = [p[2] for p in t['p']]
            flat = max(zs) - min(zs) < 0.01
            world_uv = False
            uv = t['uv']
            if mat in BASE_FLOORS and max(zs) < 1.0 and edge and edge[0] == 'fill':
                mat = edge[1]
                world_uv = True
            elif mat in BASE_FLOORS and max(zs) < 1.0 and edge:
                mat = edge[0]
                uv = [(u, 1.0 - v) for u, v in (bilinear(edge[1], p[0], p[1]) for p in t['p'])]
            elif mat in BASE_FLOORS and max(zs) < 1.0:
                mat = self.paint_at(c, r, o)
                world_uv = True
            elif flat and mat in TOP_FLOORS + BASE_FLOORS and top_paint and abs(o * STOREY + zs[0] - level * STOREY) < 0.5:
                mat = top_paint
                world_uv = True
                cols = [[0.81, 0.81, 0.81]] * 3
            elif mat in BASE_FLOORS:
                mat = 'dun_floor'
            elif mat == 'black':
                mat = 'dun_floor2'
                cols = [[0.0, 0.0, 0.0]] * 3
            if mat == ROCK_TOP:
                mat = 'dun_floor2'
            out.append({'m': mat, 'p': [[p[0], p[1], p[2] + o * STOREY] for p in t['p']], 'uv': uv, 'c': cols, 'w': world_uv})
        return out

    def tile_pieces(self):
        tiles = {}
        self.stamped = set()
        for r in range(self.h):
            for c in range(self.w):
                tiles[(c, r)] = self.resolve(c, r)
        for r in range(self.h):
            for c in range(self.w):
                if self.grid[r][c] != 'X':
                    continue
                front = None
                for f, name in FRONT_TO_DOOR.items():
                    if self.at(c + f[0], r + f[1]) == '.':
                        front = (f, name)
                        break
                if front is None:
                    self.warnings.append('exit at %d,%d has no floor in front of it' % (c, r))
                    continue
                (fx, fy), name = front
                stamp = KIT['doors'][name]
                for cell in stamp['cells']:
                    depth = cell['dy'] if fx == 0 else cell['dx']
                    depth_sign = fy if fx == 0 else fx
                    want = 0 if depth * depth_sign > 0 else (1 if depth == 0 else 2)
                    pos = (c + cell['dx'], r + cell['dy'])
                    if not self.inside(*pos) or self.L[pos[1]][pos[0]] != want:
                        self.warnings.append('exit at %d,%d needs a straight wall 3 tiles wide with floor in front' % (c, r))
                    tris = []
                    for t in cell['tris']:
                        mat, uv, world = t['m'], t['uv'], False
                        if mat in BASE_FLOORS and max(p[2] for p in t['p']) < 1.0 and self.inside(*pos):
                            mat, world = self.paint_at(pos[0], pos[1], 0), True
                        elif mat == 'black':
                            continue
                        tris.append({'m': mat, 'p': t['p'], 'uv': uv, 'c': t['c'], 'w': world})
                    tiles[pos] = tris
                    self.stamped.add(pos)
                self.exits.append({'tile': [c, r], 'facing': name, 'arrive': [c + fx, r + fy], 'step_back': STEP_BACK[name]})
        return tiles

    def material_paths(self, used):
        walls = os.path.join(TEX_DIR, 'walls_' + self.biome['walls'])
        paths = {}
        for n in used:
            if n in WALL_TEXTURES:
                paths[n] = os.path.join(walls, n + '.png')
            elif n in DOOR_TEXTURES:
                paths[n] = os.path.join(B.ASSETS, n + '.png')
            elif os.path.exists(os.path.join(TEX_DIR, 'floors', n + '.png')):
                paths[n] = os.path.join(TEX_DIR, 'floors', n + '.png')
            else:
                paths[n] = os.path.join(OBJ_DIR, 'tex', n + '.png')
        return paths

    def groups(self, tiles):
        keys = {}
        for (c, r), tris in tiles.items():
            if (c, r) in self.stamped or not tris:
                continue
            shape = tuple((t['m'], t['w'], tuple(tuple(round(v, 2) for v in p) for p in t['p']),
                           tuple(round(u, 3) for uv in t['uv'] for u in uv) if not t['w'] else (),
                           tuple(round(v, 2) for col in t['c'] for v in col)) for t in tris)
            keys[(c, r)] = (hash(shape), invariant(tris, 0), invariant(tris, 1))
        done = set()
        out = []
        for my in range(self.h // 32):
            for mx in range(self.w // 32):
                for r in range(my * 32, my * 32 + 32):
                    for c in range(mx * 32, mx * 32 + 32):
                        if (c, r) in done or not tiles.get((c, r)):
                            continue
                        key = keys.get((c, r))
                        nx = ny = 1
                        if key and key[1]:
                            while c + nx < mx * 32 + 32 and keys.get((c + nx, r)) == key and (c + nx, r) not in done:
                                nx += 1
                        if key and key[2]:
                            while r + ny < my * 32 + 32 and all(keys.get((c + k, r + ny)) == key and (c + k, r + ny) not in done for k in range(nx)):
                                ny += 1
                        for k in range(nx):
                            for j in range(ny):
                                done.add((c + k, r + j))
                        out.append((c, r, nx, ny, stretch(stretch(tiles[(c, r)], 0, nx), 1, ny)))
        return out

    def build(self):
        tiles = self.tile_pieces()
        used = set(WALL_TEXTURES) | set(DOOR_TEXTURES)
        for tris in tiles.values():
            for t in tris:
                used.add(t['m'])
        for o in self.objects:
            mesh = object_mesh(o['key'])
            if mesh is None:
                self.warnings.append('object %s at %d,%d is not in the catalogue' % (o['key'], o['x'], o['z']))
                continue
            used.update(g['tex'] for g in mesh['groups'] if g['tex'])
        paths = self.material_paths(used)
        sizes = {n: B.read_png(p)[:2] for n, p in paths.items()}
        maps = {}
        for c, r, nx, ny, tris in self.groups(tiles):
            mx, my = c // 32, r // 32
            lc, lr = c % 32, r % 32
            x0 = -B.HALF + lc * B.T
            y0 = B.HALF - (lr + ny) * B.T
            gx0 = c * B.T
            gy0 = (self.h - r - ny) * B.T
            holder = maps.setdefault((mx, my), Faces('%s_%d_%d' % (self.name, mx, my)))
            for t in tris:
                mat = t['m']
                pts = [(x0 + p[0], y0 + p[1], FLOOR_LEVEL + p[2]) for p in t['p']]
                uvs = [tuple(u) for u in t['uv']]
                if t['w']:
                    w, h = sizes[mat]
                    uvs = [((gx0 + p[0]) / w, (gy0 + p[1]) / h) for p in t['p']]
                su = math.floor(min(u[0] for u in uvs))
                sv = math.floor(min(u[1] for u in uvs))
                holder.faces.append((mat, pts, [(u[0] - su, u[1] - sv) for u in uvs], [tuple(c) for c in t['c']]))
        for my in range(self.h // 32):
            for mx in range(self.w // 32):
                maps.setdefault((mx, my), Faces('%s_%d_%d' % (self.name, mx, my)))
        for o in self.objects:
            mesh = object_mesh(o['key'])
            if mesh is None:
                continue
            w, h = footprint(o)
            mx, my = min(self.w // 32 - 1, (o['x'] + w // 2) // 32), min(self.h // 32 - 1, (o['z'] + h // 2) // 32)
            cx = -B.HALF + (o['x'] - mx * 32 + w / 2.0) * B.T
            cy = B.HALF - (o['z'] - my * 32 + h / 2.0) * B.T
            cz = FLOOR_LEVEL + self.L[o['z']][o['x']] * STOREY
            ca, sa = [(1, 0), (0, 1), (-1, 0), (0, -1)][o.get('rot', 0) % 4]
            holder = maps[(mx, my)]
            for g in mesh['groups']:
                mat = g['tex'] or 'dun_floor2'
                pos, uv, col = g['pos'], g['uv'], g['col']
                for i in range(0, len(pos) // 3, 3):
                    pts, uvs, cols = [], [], []
                    for k in range(i, i + 3):
                        x, y, z = pos[3 * k:3 * k + 3]
                        pts.append((cx + x * ca - y * sa, cy + x * sa + y * ca, cz + z))
                        uvs.append((uv[2 * k], uv[2 * k + 1]))
                        cols.append(tuple(col[3 * k:3 * k + 3]))
                    su = math.floor(min(u[0] for u in uvs))
                    sv = math.floor(min(u[1] for u in uvs))
                    holder.faces.append((mat, pts, [(u[0] - su, u[1] - sv) for u in uvs], cols))
        return maps, paths

    def blocked(self):
        out = set()
        for o in self.objects:
            mesh = object_mesh(o['key'])
            if mesh is None or mesh.get('walkable'):
                continue
            w, h = footprint(o)
            for dx in range(w):
                for dy in range(h):
                    out.add((o['x'] + dx, o['z'] + dy))
        return out

    def collision(self, mx, my):
        blocked = self.blocked()
        out = bytearray()
        for lr in range(32):
            for lc in range(32):
                c, r = mx * 32 + lc, my * 32 + lr
                ch = self.grid[r][c]
                walk = ch in '.X' and (c, r) not in blocked
                out += struct.pack('<H', COLL_FLOOR if walk else COLL_BLOCK)
        return bytes(out)


def flat_bdhc(height):
    data = bytearray(open(os.path.join(B.ASSETS, 'reference.bdhc'), 'rb').read())
    pc, nc, cc = struct.unpack_from('<3H', data, 4)
    struct.pack_into('<i', data, 16 + 8 * pc + 12 * nc, -int(height * 4096))
    return bytes(data)


def convert(conv, imd, out, flag):
    if os.path.exists(out):
        os.remove(out)
    run = subprocess.run([conv, os.path.abspath(imd), flag, '-o', os.path.abspath(out)],
                         cwd=os.path.dirname(conv), capture_output=True, text=True)
    if not os.path.exists(out):
        print(run.stdout)
        print(run.stderr)
        return None
    return open(out, 'rb').read()


def texture_set_imd(paths, title):
    holder = Faces(title)
    names = sorted(paths)
    for i, n in enumerate(names):
        x = i * 0.1
        holder.faces.append((n, [(x, 0.0, 0.0), (x + 0.05, 0.0, 0.0), (x, 0.05, 0.0)],
                             [(0.0, 0.0), (1.0, 0.0), (0.0, 1.0)], [(1.0, 1.0, 1.0)] * 3))
    return holder, [(n, n, 0, 0) for n in names]


def write_texture_set(conv, paths, base):
    holder, mats = texture_set_imd(paths, os.path.basename(base))
    B.write_imd(holder, base + '.imd', mats, paths)
    return convert(conv, base + '.imd', base + '.nsbtx', '-etex')


def build(path, out_dir=None):
    data = json.load(open(path))
    hide = Hideaway(data)
    out_dir = out_dir or os.path.join(ROOT, 'build', 'hideaways', hide.name)
    os.makedirs(out_dir, exist_ok=True)
    maps, paths = hide.build()
    conv = B.find_converter()
    if not conv:
        print('g3dcvtr.exe not found; set G3DCVTR to its path')
        return 1
    materials = [(n, n, 0, 0) for n in sorted(paths)]
    bdhc = flat_bdhc(FLOOR_LEVEL)
    info = {'name': hide.name, 'biome': data['biome'], 'size': [hide.w // 32, hide.h // 32], 'maps': [], 'exits': hide.exits,
            'textures': sorted(paths), 'objects': len(hide.objects)}
    for (mx, my), holder in sorted(maps.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        base = os.path.join(out_dir, holder.name)
        if not holder.faces:
            holder.faces.append(('dun_floor2', [(0.0, 0.0, 0.0), (0.01, 0.0, 0.0), (0.0, 0.01, 0.0)],
                                 [(0.0, 0.0), (1.0, 0.0), (0.0, 1.0)], [(0.0, 0.0, 0.0)] * 3))
        tris = B.write_imd(holder, base + '.imd', materials, paths)
        model = convert(conv, base + '.imd', base + '.nsbmd', '-emdl')
        if model is None:
            return 1
        perm = hide.collision(mx, my)
        blob = struct.pack('<4I', len(perm), 0, len(model), len(bdhc)) + perm + model + bdhc
        open(base + '_map_data.bin', 'wb').write(blob)
        info['maps'].append({'x': mx, 'y': my, 'file': os.path.basename(base) + '_map_data.bin', 'triangles': tris, 'bytes': len(blob)})
    if write_texture_set(conv, paths, os.path.join(out_dir, hide.name + '_textures')) is None:
        return 1
    info['texture_set'] = hide.name + '_textures.nsbtx'
    info['texture_paths'] = {n: os.path.relpath(p, B.ASSETS) for n, p in paths.items()}
    info['missing_shapes'] = hide.missing
    info['warnings'] = hide.warnings
    json.dump(info, open(os.path.join(out_dir, hide.name + '_info.json'), 'w'), indent=2)
    print('built %s (%s): %d map(s), %d exit(s)' % (hide.name, hide.biome['label'], len(info['maps']), len(hide.exits)))
    for m in info['maps']:
        print('  %s: %d triangles, %d bytes' % (m['file'], m['triangles'], m['bytes']))
    if hide.missing:
        print('  %d tile shape(s) had no exact cave match and used the closest one' % sum(hide.missing.values()))
    for w in hide.warnings:
        print('  warning: ' + w)
    return 0


def main():
    if len(sys.argv) < 2:
        print('usage: build_hideaway.py hideaway.json [output_dir]')
        return 1
    return build(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)


if __name__ == '__main__':
    sys.exit(main())
