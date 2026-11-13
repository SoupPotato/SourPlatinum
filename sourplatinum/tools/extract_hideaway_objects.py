import collections
import glob
import json
import math
import os
import re
import struct
import subprocess
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import underground_block_builder as B
from extract_cave_kit import find_apicula

CATALOGUE = os.path.join(B.ASSETS, 'hideaway_objects.json')
OUT = os.path.join(B.ASSETS, 'hideaway_objects')
TEX_OUT = os.path.join(OUT, 'tex')
WORK = os.path.join(ROOT, 'build', 'hideaway_objects')
PROPS = os.path.join(ROOT, 'res', 'field', 'props')
ICON = 96


def glb_images(path):
    d = open(path, 'rb').read()
    length = struct.unpack_from('<I', d, 8)[0]
    off, js = 12, None
    while off < length:
        clen, ctype = struct.unpack_from('<II', d, off)
        if ctype == 0x4E4F534A:
            js = json.loads(d[off + 8:off + 8 + clen])
        off += 8 + clen
    out = {}
    for m in js.get('materials', []):
        t = m.get('pbrMetallicRoughness', {}).get('baseColorTexture')
        if t is None:
            continue
        img = js['images'][js['textures'][t['index']]['source']]
        out[m.get('name', '')] = os.path.splitext(os.path.basename(img.get('name') or img.get('uri', '')))[0]
    return out


def base_name(mat):
    return re.sub(r'_lm\d+$', '', mat)


def convert(apicula, model, texset, out):
    if not glob.glob(os.path.join(out, '*.glb')):
        subprocess.run([apicula, 'convert', '-f', 'glb', '--overwrite', model, texset, '-o', out], capture_output=True)
    hits = glob.glob(os.path.join(out, '*.glb'))
    return hits[0] if hits else None


def load_prop(apicula, entry):
    order = [l.strip() for l in open(os.path.join(PROPS, 'models', 'map_prop_models.order')) if l.strip()]
    sets = [l.strip() for l in open(os.path.join(PROPS, 'model_sets', 'prop_model_sets.order')) if l.strip()]
    tsets = [l.strip() for l in open(os.path.join(PROPS, 'texture_sets', 'prop_texture_sets.order')) if l.strip()]
    fn = order[entry['prop']]
    key = fn[:-len('.nsbmd')] + '_nsbmd'
    owner = None
    for si, s in enumerate(sets):
        if key in json.load(open(os.path.join(PROPS, 'model_sets', s + '.json')))['mapPropModels']:
            owner = si
            break
    if owner is None:
        return None, None
    out = os.path.join(WORK, 'prop_%03d' % entry['prop'])
    g = convert(apicula, os.path.join(PROPS, 'models', fn), os.path.join(PROPS, 'texture_sets', tsets[owner] + '.nsbtx'), out)
    return (B.read_glb(g), g) if g else (None, None)


def load_map(apicula, entry):
    data = open(os.path.join(ROOT, 'res', 'field', 'maps', 'data', 'map_data_%03d.bin' % entry['map']), 'rb').read()
    ps, bs, ms, hs = struct.unpack_from('<4I', data, 0)
    os.makedirs(WORK, exist_ok=True)
    model = os.path.join(WORK, 'map_%03d.nsbmd' % entry['map'])
    open(model, 'wb').write(data[16 + ps + bs:16 + ps + bs + ms])
    out = os.path.join(WORK, 'map_%03d' % entry['map'])
    g = convert(apicula, model, os.path.join(ROOT, 'res', 'field', 'maps', 'texture_sets', entry['texture_set'] + '.nsbtx'), out)
    return (B.read_glb(g), g) if g else (None, None)


def components(tris):
    parent = list(range(len(tris)))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    seen = {}
    for i, t in enumerate(tris):
        for p in t[1]:
            k = tuple(round(v, 1) for v in p)
            if k in seen:
                parent[find(i)] = find(seen[k])
            else:
                seen[k] = i
    groups = collections.defaultdict(list)
    for i in range(len(tris)):
        groups[find(i)].append(tris[i])
    return list(groups.values())


def nearby(tris, radius):
    parent = list(range(len(tris)))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    cells = collections.defaultdict(list)
    cent = []
    for i, t in enumerate(tris):
        c = (sum(p[0] for p in t[1]) / 3, sum(p[1] for p in t[1]) / 3)
        cent.append(c)
        cells[(int(c[0] // radius), int(c[1] // radius))].append(i)
    for i, c in enumerate(cent):
        gx, gy = int(c[0] // radius), int(c[1] // radius)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for j in cells.get((gx + dx, gy + dy), []):
                    if j > i and (cent[j][0] - c[0]) ** 2 + (cent[j][1] - c[1]) ** 2 <= radius * radius:
                        parent[find(i)] = find(j)
    groups = collections.defaultdict(list)
    for i in range(len(tris)):
        groups[find(i)].append(tris[i])
    return list(groups.values())


def pick_cluster(entry, tris):
    wanted = set(entry['materials'])
    main = [t for t in tris if base_name(t[0]) in wanted]
    comps = nearby(main, entry.get('radius', 12.0))
    if not comps:
        return []
    if entry.get('pick') == 'largest':
        comp = max(comps, key=len)
    else:
        sizes = collections.Counter(len(c) for c in comps)
        typical = max(sizes, key=lambda s: (s * sizes[s], s))
        chosen = [c for c in comps if len(c) == typical]
        comp = chosen[min(entry.get('pick', 0), len(chosen) - 1)]
    lo = [min(p[k] for t in comp for p in t[1]) for k in range(2)]
    hi = [max(p[k] for t in comp for p in t[1]) for k in range(2)]
    extra = []
    for t in tris:
        if base_name(t[0]) in set(entry.get('with', [])):
            cx = sum(p[0] for p in t[1]) / 3
            cy = sum(p[1] for p in t[1]) / 3
            if lo[0] - 4 <= cx <= hi[0] + 4 and lo[1] - 4 <= cy <= hi[1] + 4:
                extra.append(t)
    return comp + extra


def render_icon(groups, textures, path):
    pts = [(g['pos'][i], g['pos'][i + 1], g['pos'][i + 2]) for g in groups for i in range(0, len(g['pos']), 3)]
    if not pts:
        return
    xs, ys, zs = zip(*pts)
    cx, cy, cz = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, (min(zs) + max(zs)) / 2
    rad = max(max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)) / 2 + 1
    d = rad * 3.2
    eye = (cx, cy - d * 0.75, cz + d * 0.66)
    f = B.norm(B.sub((cx, cy, cz), eye))
    r = B.norm(B.cross(f, (0, 0, 1)))
    u = B.cross(r, f)
    foc = (ICON / 2) / math.tan(math.radians(20))
    zb = [[1e18] * ICON for _ in range(ICON)]
    img = [[(0, 0, 0, 0)] * ICON for _ in range(ICON)]

    def proj(p):
        v = B.sub(p, eye)
        z = B.dot(v, f)
        return (ICON / 2 + foc * B.dot(v, r) / z, ICON / 2 - foc * B.dot(v, u) / z, z)
    for g in groups:
        tex = textures.get(g['tex'])
        for i in range(0, len(g['pos']), 9):
            P = [proj(tuple(g['pos'][i + 3 * k:i + 3 * k + 3])) for k in range(3)]
            uv = [g['uv'][(i // 3 + k) * 2:(i // 3 + k) * 2 + 2] for k in range(3)]
            col = [g['col'][(i // 3 + k) * 3:(i // 3 + k) * 3 + 3] for k in range(3)]
            if min(p[2] for p in P) <= 1:
                continue
            x0 = max(0, int(min(p[0] for p in P)))
            x1 = min(ICON - 1, int(max(p[0] for p in P)) + 1)
            y0 = max(0, int(min(p[1] for p in P)))
            y1 = min(ICON - 1, int(max(p[1] for p in P)) + 1)
            for y in range(y0, y1 + 1):
                for x in range(x0, x1 + 1):
                    px_, py_ = x + 0.5, y + 0.5
                    w0 = (P[1][0] - px_) * (P[2][1] - py_) - (P[2][0] - px_) * (P[1][1] - py_)
                    w1 = (P[2][0] - px_) * (P[0][1] - py_) - (P[0][0] - px_) * (P[2][1] - py_)
                    w2 = (P[0][0] - px_) * (P[1][1] - py_) - (P[1][0] - px_) * (P[0][1] - py_)
                    if not ((w0 >= 0 and w1 >= 0 and w2 >= 0) or (w0 <= 0 and w1 <= 0 and w2 <= 0)):
                        continue
                    s = w0 + w1 + w2
                    if s == 0:
                        continue
                    b = [w0 / s / P[0][2], w1 / s / P[1][2], w2 / s / P[2][2]]
                    bs = sum(b)
                    b = [k / bs for k in b]
                    z = 1 / bs
                    if z >= zb[y][x]:
                        continue
                    uu = sum(b[k] * uv[k][0] for k in range(3))
                    vv = sum(b[k] * uv[k][1] for k in range(3))
                    cc = [sum(b[k] * col[k][j] for k in range(3)) for j in range(3)]
                    if tex:
                        tw, th, tp = tex
                        p = tp[int((1.0 - vv % 1) * th) % th][int((uu % 1) * tw) % tw]
                        if p[3] < 64:
                            continue
                        c = tuple(min(255, int(p[j] * cc[j])) for j in range(3)) + (255,)
                    else:
                        c = tuple(int(255 * cc[j]) for j in range(3)) + (255,)
                    zb[y][x] = z
                    img[y][x] = c
    raw = b''.join(b'\0' + bytes(v for p in row for v in p) for row in img)
    ch = lambda t, d: struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    open(path, 'wb').write(b'\x89PNG\r\n\x1a\n' + ch(b'IHDR', struct.pack('>IIBBBBB', ICON, ICON, 8, 6, 0, 0, 0))
                           + ch(b'IDAT', zlib.compress(raw)) + ch(b'IEND', b''))


def main():
    apicula = find_apicula()
    if not apicula:
        print('apicula not found; set APICULA to its path')
        return 1
    os.makedirs(TEX_OUT, exist_ok=True)
    for old in glob.glob(os.path.join(TEX_OUT, '*.png')):
        os.remove(old)
    floors_dir = os.path.join(B.ASSETS, 'hideaway_textures', 'floors')
    reserved = {}
    for p in glob.glob(os.path.join(floors_dir, '*.png')):
        reserved[os.path.splitext(os.path.basename(p))[0]] = open(p, 'rb').read()
    entries = json.load(open(CATALOGUE))
    tex_owner = {}
    for entry in entries:
        if 'prop' in entry:
            tris, g = load_prop(apicula, entry)
        else:
            tris, g = load_map(apicula, entry)
            if tris:
                tris = pick_cluster(entry, tris)
        if not tris:
            print('skipped %s: nothing found' % entry['key'])
            continue
        images = glb_images(g)
        src_dir = os.path.dirname(g)
        scale = entry.get('scale', 1.0)
        xs = [p[0] for t in tris for p in t[1]]
        ys = [p[1] for t in tris for p in t[1]]
        zs = [p[2] for t in tris for p in t[1]]
        if 'prop' in entry:
            ox, oy = 0.0, 0.0
        else:
            ox, oy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
        oz = min(zs)
        flat = max(zs) - min(zs) < 0.5
        lift = 0.5 if flat else 0.0
        groups = collections.OrderedDict()
        textures = {}
        for mat, cos, uvs, cols, n, lo, hi in tris:
            image = images.get(mat)
            if not image or not os.path.exists(os.path.join(src_dir, image + '.png')):
                continue
            tex = None
            if image and os.path.exists(os.path.join(src_dir, image + '.png')):
                raw = open(os.path.join(src_dir, image + '.png'), 'rb').read()
                tex = image
                k = 2
                while (tex in tex_owner and tex_owner[tex] != raw) or (tex in reserved and reserved[tex] != raw):
                    tex = '%s_%d' % (image[:13], k)
                    k += 1
                if tex not in tex_owner:
                    tex_owner[tex] = raw
                    open(os.path.join(TEX_OUT, tex + '.png'), 'wb').write(raw)
                textures[tex] = os.path.join('tex', tex + '.png')
            g2 = groups.setdefault(tex or '', {'tex': tex or '', 'pos': [], 'uv': [], 'col': []})
            for p, uv, c in zip(cos, uvs, cols):
                z = (p[2] - oz) * scale
                g2['pos'] += [round((p[0] - ox) * scale, 3), round((p[1] - oy) * scale, 3), round(max(z, 0.5) if z < 0.5 else z + lift, 3)]
                g2['uv'] += [round(uv[0], 4), round(uv[1], 4)]
                g2['col'] += [round(v, 3) for v in c]
        allx = [v for g2 in groups.values() for v in g2['pos'][0::3]]
        ally = [v for g2 in groups.values() for v in g2['pos'][1::3]]
        w = max(1, int(math.ceil((max(abs(min(allx)), abs(max(allx))) * 2 - 2) / B.T)))
        h = max(1, int(math.ceil((max(abs(min(ally)), abs(max(ally))) * 2 - 2) / B.T)))
        w, h = entry.get('w', w), entry.get('h', h)
        mesh = {'key': entry['key'], 'label': entry['label'], 'w': w, 'h': h, 'walkable': entry.get('walkable', False),
                'textures': textures, 'groups': list(groups.values())}
        json.dump(mesh, open(os.path.join(OUT, entry['key'] + '.json'), 'w'), separators=(',', ':'))
        loaded = {}
        for name, rel in textures.items():
            loaded[name] = B.read_png(os.path.join(OUT, rel))
        render_icon(mesh['groups'], loaded, os.path.join(OUT, 'icon_' + entry['key'] + '.png'))
        print('%-20s %4d triangles, %dx%d tiles, textures %s' % (entry['key'], len(tris), w, h, ', '.join(textures)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
