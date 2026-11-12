import collections
import copy
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, HERE)
import underground_block_builder as ub

ASSETS = os.path.join(HERE, 'underground_block_editor_assets')
BLOCKS = os.path.join(ASSETS, 'blocks')
MANIFEST = os.path.join(ASSETS, 'imported_layout.json')
WORK = os.path.join(REPO, 'build', 'underground_import')
MAP_DATA_DIR = os.path.join(REPO, 'res', 'field', 'maps', 'data')
ORDER = os.path.join(MAP_DATA_DIR, 'map_data.order')
MESON = os.path.join(MAP_DATA_DIR, 'meson.build')
MATRIX = os.path.join(REPO, 'res', 'field', 'matrices', 'map_matrix_002.json')
MAPS_TXT = os.path.join(REPO, 'generated', 'maps.txt')
SCRIPTS = os.path.join(REPO, 'res', 'field', 'scripts', 'scripts_underground.s')
ARRIVALS_H = os.path.join(REPO, 'include', 'data', 'underground_arrivals.h')
DOORS_H = os.path.join(REPO, 'include', 'data', 'underground_hideaway_doors.h')

FIRST_ID = 666
MAX_DISTINCT_BLOCKS = 96
BASE_BLOCK = 649
STUB = 6
N = 15
HIDEAWAY_HEADER = 'MAP_HEADER_GRAND_UNDERGROUND_HIDEAWAY_1'
HIDEAWAY_DEST = (11, 2)
SIDES = {'N': (-1, 0), 'S': (1, 0), 'W': (0, -1), 'E': (0, 1)}


def read_text(path):
    raw = open(path, 'rb').read().decode('utf-8')
    return raw.replace('\r\n', '\n'), '\r\n' in raw


def write_text(path, text, crlf):
    if crlf:
        text = text.replace('\n', '\r\n')
    open(path, 'wb').write(text.encode('utf-8'))


def grid_of(name):
    return [list(r) for r in json.load(open(os.path.join(BLOCKS, name + '.json')))['tiles']]


def parse_cell(v):
    if v == 'HIDEAWAY':
        return 'big', None
    n = int(v.split('_')[1])
    return ('h' if v.endswith('_HIDEAWAY') else 'plain'), n


def edge(g, side):
    if side == 'N':
        return g[0]
    if side == 'S':
        return g[31]
    if side == 'W':
        return [r[0] for r in g]
    return [r[31] for r in g]


def runs(bits):
    out, start = [], None
    for i, b in enumerate(list(bits) + [False]):
        if b and start is None:
            start = i
        if not b and start is not None:
            out.append((start, i - 1))
            start = None
    return out


def set_tile(g, side, along, depth, value, only_rock=True):
    if side == 'N':
        z, x = depth, along
    elif side == 'S':
        z, x = 31 - depth, along
    elif side == 'W':
        z, x = along, depth
    else:
        z, x = along, 31 - depth
    if not only_rock or g[z][x] == '#':
        g[z][x] = value


def main():
    if len(sys.argv) < 2:
        print('usage: import_underground_layout.py layout.json')
        return 1
    layout = json.load(open(sys.argv[1]))
    cells = [[parse_cell(v) for v in row] for row in layout['maps']]
    assert len(cells) == N and all(len(r) == N for r in cells)

    base = [[None] * N for _ in range(N)]
    for r in range(N):
        for c in range(N):
            kind, n = cells[r][c]
            if kind == 'plain':
                base[r][c] = grid_of('block_%d' % n)
            elif kind == 'h':
                base[r][c] = grid_of('block_%d_H' % n)
            else:
                base[r][c] = [['#'] * 32 for _ in range(32)]
    final = copy.deepcopy(base)
    opposite = {'N': 'S', 'S': 'N', 'W': 'E', 'E': 'W'}

    for r in range(N):
        for c in range(N):
            kind, n = cells[r][c]
            if kind == 'plain':
                continue
            for side, (dr, dc) in SIDES.items():
                rr, cc = r + dr, c + dc
                if not (0 <= rr < N and 0 <= cc < N) or cells[rr][cc] == ('plain', BASE_BLOCK):
                    continue
                theirs = edge(base[rr][cc], opposite[side])
                mine = edge(final[r][c], side)
                for a, b in runs([theirs[i] == '.' and mine[i] != '.' for i in range(32)]):
                    for depth in range(STUB):
                        for along in range(a, b + 1):
                            set_tile(final[r][c], side, along, depth, '.')
                    set_tile(final[r][c], side, (a + b) // 2, STUB, 'D')

    dead_ends = []
    for r in range(N):
        for c in range(N):
            if cells[r][c] == ('plain', BASE_BLOCK):
                continue
            for side, (dr, dc) in SIDES.items():
                rr, cc = r + dr, c + dc
                if not (0 <= rr < N and 0 <= cc < N) or cells[rr][cc] == ('plain', BASE_BLOCK):
                    continue
                mine, theirs = edge(final[r][c], side), edge(final[rr][cc], opposite[side])
                bad = [i for i in range(32) if mine[i] == '.' and theirs[i] != '.']
                if bad:
                    dead_ends.append((r, c, side, bad[0], bad[-1]))

    previous = json.load(open(MANIFEST)) if os.path.exists(MANIFEST) else {'ids': []}
    unique = {}
    assignments = {}
    for r in range(N):
        for c in range(N):
            kind, n = cells[r][c]
            if kind == 'plain':
                assignments[(r, c)] = n
                continue
            nbs = {}
            for side, (dr, dc) in SIDES.items():
                rr, cc = r + dr, c + dc
                if 0 <= rr < N and 0 <= cc < N:
                    nbs[side] = [''.join(row) for row in final[rr][cc]]
            tiles = [''.join(row) for row in final[r][c]]
            source = n if kind == 'h' else None
            nsrc = {}
            for side, (dr, dc) in SIDES.items():
                rr, cc = r + dr, c + dc
                if 0 <= rr < N and 0 <= cc < N and cells[rr][cc][0] in ('plain', 'h') and cells[rr][cc][1] != BASE_BLOCK:
                    nsrc[side] = cells[rr][cc][1]
            key = json.dumps([tiles, source, nsrc, {k: [v[i][:3] + v[i][-3:] for i in range(32)] + [v[0], v[1], v[2], v[29], v[30], v[31]]
                                      for k, v in nbs.items()}], sort_keys=True)
            if key not in unique:
                unique[key] = (len(unique), tiles, nbs, cells[r][c], source, nsrc)
            assignments[(r, c)] = FIRST_ID + unique[key][0]

    distinct = len(unique) + len({n for kind, n in (cells[r][c] for r in range(N) for c in range(N)) if kind == 'plain'})
    if distinct > MAX_DISTINCT_BLOCKS:
        print('stopping: the layout needs %d different blocks, the game can hold %d' % (distinct, MAX_DISTINCT_BLOCKS))
        return 1

    os.makedirs(WORK, exist_ok=True)
    built = []
    for key, (k, tiles, nbs, cell, source, nsrc) in sorted(unique.items(), key=lambda kv: kv[1][0]):
        mid = FIRST_ID + k
        name = 'map_data_%d' % mid
        blob, info = ub.build_block(tiles, name, WORK, nbs, quiet=True, source=source, neighbour_sources=nsrc)
        if blob is None:
            print('stopping: could not build %s' % name)
            return 1
        open(os.path.join(MAP_DATA_DIR, name + '.bin'), 'wb').write(blob)
        json.dump({'name': name, 'tiles': tiles, 'neighbours': nbs, 'source': source, 'neighbour_sources': nsrc},
                  open(os.path.join(WORK, name + '.json'), 'w'), indent=1)
        built.append(mid)
    for mid in previous.get('ids', []):
        if mid not in built:
            p = os.path.join(MAP_DATA_DIR, 'map_data_%d.bin' % mid)
            if os.path.exists(p):
                os.remove(p)

    text, crlf = read_text(ORDER)
    lines = [l for l in text.split('\n') if l and not (re.fullmatch(r'map_data_(\d+)\.bin', l) and int(re.fullmatch(r'map_data_(\d+)\.bin', l).group(1)) >= FIRST_ID)]
    lines += ['map_data_%d.bin' % m for m in built]
    write_text(ORDER, '\n'.join(lines) + '\n', crlf)

    text, crlf = read_text(MESON)
    out, entries, first_at = [], [], None
    for l in text.split('\n'):
        m = re.fullmatch(r"\s*'map_data_(\d+)\.bin',?", l)
        if m:
            if first_at is None:
                first_at = len(out)
                out.append(None)
            if int(m.group(1)) < FIRST_ID:
                entries.append(int(m.group(1)))
            continue
        out.append(l)
    entries += built
    block = ',\n'.join("    'map_data_%03d.bin'" % e for e in entries)
    out[first_at] = block
    write_text(MESON, '\n'.join(out), crlf)

    text, crlf = read_text(MAPS_TXT)
    keep = [l for l in text.split('\n') if l and not (re.fullmatch(r'MAP_(\d+)', l) and int(l[4:]) >= FIRST_ID)]
    at = next(i for i, l in enumerate(keep) if l.startswith('MAP_NONE'))
    keep[at:at] = ['MAP_%d' % m for m in built]
    write_text(MAPS_TXT, '\n'.join(keep) + '\n', crlf)

    text, crlf = read_text(MATRIX)
    matrix = json.loads(text)
    matrix['maps'] = [['MAP_%d' % assignments[(r, c)] for c in range(N)] for r in range(N)]
    write_text(MATRIX, json.dumps(matrix, indent=4) + '\n', crlf)

    floor = [[False] * (N * 32) for _ in range(N * 32)]
    for r in range(N):
        for c in range(N):
            if cells[r][c] == ('plain', BASE_BLOCK):
                continue
            for z in range(32):
                for x in range(32):
                    floor[r * 32 + z][c * 32 + x] = final[r][c][z][x] == '.'

    def nearest(x, z, taken=()):
        seen = {(x, z)}
        q = collections.deque([(x, z)])
        while q:
            px, pz = q.popleft()
            if 0 <= px < N * 32 and 0 <= pz < N * 32 and floor[pz][px] and (px, pz) not in taken:
                return px, pz
            for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, nz = px + dx, pz + dz
                if 0 <= nx < N * 32 and 0 <= nz < N * 32 and (nx, nz) not in seen:
                    seen.add((nx, nz))
                    q.append((nx, nz))
        return x, z

    rows = []
    for mz in range(N):
        cols = []
        for mx in range(N):
            subs = []
            for sub in range(4):
                lx, lz = (23 if sub & 1 else 8), (23 if sub & 2 else 8)
                subs.append('{ %d, %d }' % nearest(mx * 32 + lx, mz * 32 + lz))
            cols.append('{ ' + ', '.join(subs) + ' }')
        rows.append('    { ' + ', '.join(cols) + ' },')
    write_text(ARRIVALS_H, '#ifndef POKEPLATINUM_DATA_UNDERGROUND_ARRIVALS_H\n#define POKEPLATINUM_DATA_UNDERGROUND_ARRIVALS_H\n\n'
               '#define UNDERGROUND_ARRIVAL_MATRIX_SIZE %d\n\n'
               'static const u16 sUndergroundArrivals[%d][%d][4][2] = {\n%s\n};\n\n#endif\n' % (N, N, N, '\n'.join(rows)), False)

    doors = []
    for r in range(N):
        for c in range(N):
            for z in range(32):
                for x in range(32):
                    if final[r][c][z][x] == 'D':
                        doors.append((c * 32 + x, r * 32 + z))
    write_text(DOORS_H, '#ifndef POKEPLATINUM_DATA_UNDERGROUND_HIDEAWAY_DOORS_H\n#define POKEPLATINUM_DATA_UNDERGROUND_HIDEAWAY_DOORS_H\n\n'
               'static const HideawayEntrance sHideawayEntrances[] = {\n%s\n};\n\n#endif\n'
               % '\n'.join('    { %d, %d, %s, %d, %d },' % (x, z, HIDEAWAY_HEADER, HIDEAWAY_DEST[0], HIDEAWAY_DEST[1]) for x, z in doors), False)

    text, crlf = read_text(SCRIPTS)
    moved = []
    taken = {(x + dx, z + dz) for x, z in doors for dx, dz in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1))}
    out = []
    for l in text.split('\n'):
        m = re.match(r'(\s*SetObjectEventPos\s+(\w+),\s*)(\d+),\s*(\d+)\s*$', l)
        if m:
            x, z = int(m.group(3)), int(m.group(4))
            nx, nz = nearest(x, z, taken)
            taken.add((nx, nz))
            if (nx, nz) != (x, z):
                moved.append((m.group(2), (x, z), (nx, nz)))
            l = '%s%d, %d' % (m.group(1), nx, nz)
        out.append(l)
    write_text(SCRIPTS, '\n'.join(out), crlf)

    json.dump({'source': os.path.basename(sys.argv[1]), 'ids': built}, open(MANIFEST, 'w'), indent=2)
    print('%d new blocks (map_data_%d to map_data_%d), %d doors' % (len(built), FIRST_ID, FIRST_ID + len(built) - 1, len(doors)))
    for name, a, b in moved:
        print('moved %s from %s to %s' % (name, a, b))
    for r, c, side, a, b in dead_ends:
        print('dead end: row %d column %d %s edge tiles %d-%d run into rock next door' % (r, c, side, a, b))
    if os.path.isdir(os.path.join(ASSETS, 'hideaways')):
        import install_hideaways
        return install_hideaways.main()
    return 0


if __name__ == '__main__':
    sys.exit(main())
