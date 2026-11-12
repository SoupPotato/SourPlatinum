import glob
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, HERE)
import build_hideaway as BH
from import_underground_layout import read_text, write_text, FIRST_ID, MANIFEST

ASSETS = os.path.join(HERE, 'underground_block_editor_assets')
HIDEAWAY_DIR = os.path.join(ASSETS, 'hideaways')
STATE = os.path.join(ASSETS, 'installed_hideaways.json')
WORK = os.path.join(REPO, 'build', 'hideaways')
FIELD = os.path.join(REPO, 'res', 'field')
MAP_DATA_DIR = os.path.join(FIELD, 'maps', 'data')
TEX_DIR = os.path.join(FIELD, 'maps', 'texture_sets')
AREA_DIR = os.path.join(FIELD, 'area_data')
MATRIX_DIR = os.path.join(FIELD, 'matrices')
MAPS_TXT = os.path.join(REPO, 'generated', 'maps.txt')
HEADERS = os.path.join(REPO, 'include', 'data', 'map_headers.h')
DOORS_H = os.path.join(REPO, 'include', 'data', 'underground_hideaway_doors.h')
WALL_AREAS = {'052': 'area_data_053', '068': 'area_data_069'}


def set_list(order_path, meson_path, prefix, ext, first, ids):
    pat = re.compile(r'%s_(\d+)%s' % (prefix, re.escape(ext)))
    text, crlf = read_text(order_path)
    lines = []
    for l in text.split('\n'):
        m = re.fullmatch(r'%s_(\d+)(%s)?' % (prefix, re.escape(ext)), l.strip())
        if l and not (m and int(m.group(1)) >= first):
            lines.append(l)
    order_ext = ext if any(l.strip().endswith(ext) for l in lines) else ''
    lines += ['%s_%03d%s' % (prefix, i, order_ext) for i in ids]
    write_text(order_path, '\n'.join(lines) + '\n', crlf)
    text, crlf = read_text(meson_path)
    out, entries, at, indent = [], [], None, '    '
    for l in text.split('\n'):
        m = re.fullmatch(r"(\s*)'%s_(\d+)%s',?" % (prefix, re.escape(ext)), l)
        if m:
            if at is None:
                at = len(out)
                indent = m.group(1)
                out.append(None)
            if int(m.group(2)) < first:
                entries.append(int(m.group(2)))
            continue
        out.append(l)
    entries += ids
    out[at] = ',\n'.join("%s'%s_%03d%s'" % (indent, prefix, e, ext) for e in entries)
    write_text(meson_path, '\n'.join(out), crlf)


def next_free(order_path, prefix):
    text, _ = read_text(order_path)
    nums = [int(m.group(1)) for m in re.finditer(r'%s_(\d+)' % prefix, text)]
    return max(nums) + 1


def main():
    state = json.load(open(STATE)) if os.path.exists(STATE) else {}
    paths = sorted(glob.glob(os.path.join(HIDEAWAY_DIR, '*.json')))
    if not paths:
        print('no hideaways in %s' % HIDEAWAY_DIR)
        return 1
    manifest = json.load(open(MANIFEST)) if os.path.exists(MANIFEST) else {}
    first_map = max(manifest.get('ids', [FIRST_ID - 1])) + 1
    area_base = state.get('area_base') or next_free(os.path.join(AREA_DIR, 'area_data.order'), 'area_data')
    tex_base = state.get('tex_base') or next_free(os.path.join(TEX_DIR, 'map_texture_sets.order'), 'map_texture_set')
    matrix_base = state.get('matrix_base') or next_free(os.path.join(MATRIX_DIR, 'map_matrices.order'), 'map_matrix')

    for p in state.get('map_files', []):
        full = os.path.join(MAP_DATA_DIR, p)
        if os.path.exists(full):
            os.remove(full)

    built = []
    biomes = []
    for path in paths:
        data = json.load(open(path))
        out_dir = os.path.join(WORK, data['name'])
        if BH.build(path, out_dir) != 0:
            print('stopping: could not build %s' % data['name'])
            return 1
        info = json.load(open(os.path.join(out_dir, data['name'] + '_info.json')))
        built.append((data, info, out_dir))
        if data['biome'] not in biomes:
            biomes.append(data['biome'])

    next_map = first_map
    map_files = []
    new_state = {'area_base': area_base, 'tex_base': tex_base, 'matrix_base': matrix_base, 'hideaways': {}}
    biome_area = {b: area_base + i for i, b in enumerate(biomes)}
    biome_tex = {b: tex_base + i for i, b in enumerate(biomes)}
    for b in biomes:
        paths = {}
        for d, i, o in built:
            if d['biome'] == b:
                for n, rel in i['texture_paths'].items():
                    full = os.path.join(BH.B.ASSETS, rel)
                    if n in paths and os.path.normcase(paths[n]) != os.path.normcase(full):
                        print('warning: two different textures are called %s in %s hideaways' % (n, b))
                    paths.setdefault(n, full)
        conv = BH.B.find_converter()
        base = os.path.join(WORK, 'texture_set_' + b)
        if not conv or BH.write_texture_set(conv, paths, base) is None:
            print('stopping: could not build the %s texture set' % b)
            return 1
        shutil.copyfile(base + '.nsbtx', os.path.join(TEX_DIR, 'map_texture_set_%03d.nsbtx' % biome_tex[b]))
        like = json.load(open(os.path.join(AREA_DIR, WALL_AREAS[BH.BIOMES[b]['walls']] + '.json')))
        area = {'mapPropSet': like['mapPropSet'], 'mapTextureSet': 'map_texture_set_%03d' % biome_tex[b],
                'lightingSet': like['lightingSet'], 'dummy': 0}
        text, crlf = read_text(os.path.join(AREA_DIR, 'area_data_000.json'))
        write_text(os.path.join(AREA_DIR, 'area_data_%03d.json' % biome_area[b]), json.dumps(area, indent=4) + '\n', crlf)

    for k, (data, info, out_dir) in enumerate(built):
        w, h = info['size']
        grid = [[None] * w for _ in range(h)]
        for m in info['maps']:
            mid = next_map
            next_map += 1
            fname = 'map_data_%d.bin' % mid
            shutil.copyfile(os.path.join(out_dir, m['file']), os.path.join(MAP_DATA_DIR, fname))
            map_files.append(fname)
            grid[m['y']][m['x']] = 'MAP_%d' % mid
        matrix_id = matrix_base + k
        text, crlf = read_text(os.path.join(MATRIX_DIR, 'map_matrix_062.json'))
        matrix = {'name': 'hideaway%02d' % k, 'headers': [], 'altitudes': [], 'maps': grid}
        write_text(os.path.join(MATRIX_DIR, 'map_matrix_%03d.json' % matrix_id), json.dumps(matrix, indent=4) + '\n', crlf)
        new_state['hideaways'][data['name']] = {'biome': data['biome'], 'matrix': 'map_matrix_%03d' % matrix_id,
                                                'area_data': 'area_data_%03d' % biome_area[data['biome']],
                                                'maps': [row[:] for row in grid], 'exits': info['exits'],
                                                'header': data.get('header')}
    new_state['map_files'] = map_files
    map_ids = list(range(first_map, next_map))

    set_list(os.path.join(MAP_DATA_DIR, 'map_data.order'), os.path.join(MAP_DATA_DIR, 'meson.build'),
             'map_data', '.bin', first_map, map_ids)
    set_list(os.path.join(AREA_DIR, 'area_data.order'), os.path.join(AREA_DIR, 'meson.build'),
             'area_data', '.json', area_base, [biome_area[b] for b in biomes])
    set_list(os.path.join(TEX_DIR, 'map_texture_sets.order'), os.path.join(TEX_DIR, 'meson.build'),
             'map_texture_set', '.nsbtx', tex_base, [biome_tex[b] for b in biomes])
    set_list(os.path.join(MATRIX_DIR, 'map_matrices.order'), os.path.join(MATRIX_DIR, 'meson.build'),
             'map_matrix', '.json', matrix_base, [matrix_base + k for k in range(len(built))])
    for old in glob.glob(os.path.join(AREA_DIR, 'area_data_*.json')):
        n = int(re.search(r'(\d+)', os.path.basename(old)).group(1))
        if n >= area_base + len(biomes):
            os.remove(old)
    for old in glob.glob(os.path.join(TEX_DIR, 'map_texture_set_*.nsbtx')):
        n = int(re.search(r'(\d+)', os.path.basename(old)).group(1))
        if n >= tex_base + len(biomes):
            os.remove(old)
    for old in glob.glob(os.path.join(MATRIX_DIR, 'map_matrix_*.json')):
        n = int(re.search(r'(\d+)', os.path.basename(old)).group(1))
        if n >= matrix_base + len(built):
            os.remove(old)

    text, crlf = read_text(MAPS_TXT)
    keep = [l for l in text.split('\n') if l and not (re.fullmatch(r'MAP_(\d+)', l) and int(l[4:]) >= first_map)]
    at = next(i for i, l in enumerate(keep) if l.startswith('MAP_NONE'))
    keep[at:at] = ['MAP_%d' % m for m in map_ids]
    write_text(MAPS_TXT, '\n'.join(keep) + '\n', crlf)

    for name, h in new_state['hideaways'].items():
        if h['header']:
            apply_header(h)
    json.dump(new_state, open(STATE, 'w'), indent=1)
    print('installed %d hideaway(s): maps %d-%d, area data %s, texture sets %s' % (
        len(built), first_map, next_map - 1, sorted(biome_area.values()), sorted(biome_tex.values())))
    return 0


def apply_header(h):
    header = h['header']
    text, crlf = read_text(HEADERS)
    m = re.search(r'(\[%s\]\s*=\s*\{)(.*?)(\n    \})' % header, text, re.S)
    body = re.sub(r'\.areaDataArchiveID = \w+', '.areaDataArchiveID = %s' % h['area_data'], m.group(2))
    body = re.sub(r'\.mapMatrixID = \w+', '.mapMatrixID = %s' % h['matrix'], body)
    write_text(HEADERS, text[:m.start(2)] + body + text[m.end(2):], crlf)
    if not h['exits']:
        return
    ex = h['exits'][0]
    stem = header[len('MAP_HEADER_'):].lower()
    events_path = os.path.join(FIELD, 'events', 'events_%s.json' % stem)
    text, crlf = read_text(events_path)
    events = json.loads(text)
    for ev in events.get('coord_events', []):
        ev['x'], ev['z'] = ex['tile']
    write_text(events_path, json.dumps(events, indent=4) + '\n', crlf)
    script_path = os.path.join(FIELD, 'scripts', 'scripts_%s.s' % stem)
    text, crlf = read_text(script_path)
    text = re.sub(r'(_Movement_StepBack:\n\s*)WalkNormal\w+', r'\1WalkNormal%s' % ex['step_back'], text)
    write_text(script_path, text, crlf)
    text, crlf = read_text(DOORS_H)
    text = re.sub(r'(%s, )\d+, \d+( \})' % header, r'\g<1>%d, %d\2' % tuple(ex['arrive']), text)
    write_text(DOORS_H, text, crlf)


if __name__ == '__main__':
    sys.exit(main())
