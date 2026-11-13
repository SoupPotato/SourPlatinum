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
WALLS = json.load(open(os.path.join(ASSETS, 'hideaway_walls.json')))
PROP_SET = 'prop_model_set_049'
TERRAIN_H = os.path.join(REPO, 'include', 'data', 'underground_hideaway_terrain.h')
ENCOUNTERS_H = os.path.join(REPO, 'include', 'data', 'underground_hideaway_encounters.h')
SLOTS = 12
DEFAULT_BATTLE_BG = 'BACKGROUND_CAVE_3'
DEFAULT_TERRAIN = {'grassland': 'TERRAIN_GRASS', 'riverbank': 'TERRAIN_GRASS', 'swampy': 'TERRAIN_GREAT_MARSH',
                   'icy': 'TERRAIN_ICE', 'whiteout': 'TERRAIN_SNOW', 'rocky': 'TERRAIN_SAND', 'sandsear': 'TERRAIN_SAND',
                   'volcanic': 'TERRAIN_MOUNTAIN', 'fountainspring': 'TERRAIN_PLAIN'}


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
    for path in paths:
        data = json.load(open(path))
        out_dir = os.path.join(WORK, data['name'])
        if BH.build(path, out_dir) != 0:
            print('stopping: could not build %s' % data['name'])
            return 1
        info = json.load(open(os.path.join(out_dir, data['name'] + '_info.json')))
        built.append((data, info, out_dir))

    next_map = first_map
    map_files = []
    new_state = {'area_base': area_base, 'tex_base': tex_base, 'matrix_base': matrix_base, 'hideaways': {}}
    conv = BH.B.find_converter()
    for k, (data, info, out_dir) in enumerate(built):
        shutil.copyfile(os.path.join(out_dir, info['texture_set']), os.path.join(TEX_DIR, 'map_texture_set_%03d.nsbtx' % (tex_base + k)))
        walls = data.get('walls') or BH.BIOMES[data['biome']]['walls']
        lighting = data.get('lighting') or WALLS.get(walls, {}).get('lighting', 'lighting_set_001')
        area = {'mapPropSet': PROP_SET, 'mapTextureSet': 'map_texture_set_%03d' % (tex_base + k), 'lightingSet': lighting, 'dummy': 0}
        text, crlf = read_text(os.path.join(AREA_DIR, 'area_data_000.json'))
        write_text(os.path.join(AREA_DIR, 'area_data_%03d.json' % (area_base + k)), json.dumps(area, indent=4) + '\n', crlf)

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
                                                'area_data': 'area_data_%03d' % (area_base + k),
                                                'maps': [row[:] for row in grid], 'exits': info['exits'],
                                                'header': data.get('header'),
                                                'battle_bg': data.get('battle_bg') or DEFAULT_BATTLE_BG,
                                                'battle_terrain': data.get('battle_terrain') or DEFAULT_TERRAIN.get(data['biome'], 'TERRAIN_CAVE'),
                                                'encounters': data.get('encounters') or {}}
    new_state['map_files'] = map_files
    map_ids = list(range(first_map, next_map))

    set_list(os.path.join(MAP_DATA_DIR, 'map_data.order'), os.path.join(MAP_DATA_DIR, 'meson.build'),
             'map_data', '.bin', first_map, map_ids)
    set_list(os.path.join(AREA_DIR, 'area_data.order'), os.path.join(AREA_DIR, 'meson.build'),
             'area_data', '.json', area_base, [area_base + k for k in range(len(built))])
    set_list(os.path.join(TEX_DIR, 'map_texture_sets.order'), os.path.join(TEX_DIR, 'meson.build'),
             'map_texture_set', '.nsbtx', tex_base, [tex_base + k for k in range(len(built))])
    set_list(os.path.join(MATRIX_DIR, 'map_matrices.order'), os.path.join(MATRIX_DIR, 'meson.build'),
             'map_matrix', '.json', matrix_base, [matrix_base + k for k in range(len(built))])
    for old in glob.glob(os.path.join(AREA_DIR, 'area_data_*.json')):
        n = int(re.search(r'(\d+)', os.path.basename(old)).group(1))
        if n >= area_base + len(built):
            os.remove(old)
    for old in glob.glob(os.path.join(TEX_DIR, 'map_texture_set_*.nsbtx')):
        n = int(re.search(r'(\d+)', os.path.basename(old)).group(1))
        if n >= tex_base + len(built):
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

    terrains = []
    encounters = []
    for name, h in new_state['hideaways'].items():
        if h['header']:
            apply_header(h)
            terrains.append((h['header'], h['battle_terrain']))
            encounters.append((name, h['header'], h['encounters']))
    write_terrains(terrains)
    write_encounters(encounters)
    json.dump(new_state, open(STATE, 'w'), indent=1)
    print('installed %d hideaway(s): maps %d-%d, area data %d-%d, texture sets %d-%d' % (
        len(built), first_map, next_map - 1, area_base, area_base + len(built) - 1, tex_base, tex_base + len(built) - 1))
    return 0


def write_terrains(terrains):
    rows = ''.join('    { %s, %s },\n' % t for t in terrains) or '    { MAP_HEADER_INVALID, TERRAIN_MAX },\n'
    text = ('#ifndef POKEPLATINUM_DATA_UNDERGROUND_HIDEAWAY_TERRAIN_H\n#define POKEPLATINUM_DATA_UNDERGROUND_HIDEAWAY_TERRAIN_H\n\n'
            'static const HideawayTerrain sHideawayTerrains[] = {\n' + rows + '};\n\n#endif\n')
    write_text(TERRAIN_H, text, False)


def encounter_table(name, kind, enc):
    rate = int(enc.get(kind + '_rate', 0) or 0)
    slots = list(enc.get(kind, []))[:SLOTS]
    slots += [{}] * (SLOTS - len(slots))
    rows = []
    for s in slots:
        species = s.get('species') or 'SPECIES_NONE'
        lo = max(1, min(100, int(s.get('min', 1) or 1)))
        hi = max(1, min(100, int(s.get('max', lo) or lo)))
        rows.append((species, min(lo, hi), max(lo, hi)))
    if rate and any(r[0] == 'SPECIES_NONE' for r in rows):
        print('warning: %s %s encounters have empty slots, so they are turned off' % (name, kind))
        rate = 0
    return rate, rows


def write_encounters(entries):
    body = []
    for name, header, enc in entries:
        land_rate, land = encounter_table(name, 'land', enc)
        water_rate, water = encounter_table(name, 'water', enc)
        fmt = lambda rows: ',\n'.join('            { %s, %d, %d }' % r for r in rows)
        body.append('    {\n        %s,\n        %d,\n        %d,\n        {\n%s,\n        },\n        {\n%s,\n        },\n    },\n'
                    % (header, land_rate, water_rate, fmt(land), fmt(water)))
    if not body:
        empty = ',\n'.join(['            { SPECIES_NONE, 1, 1 }'] * SLOTS)
        body.append('    {\n        MAP_HEADER_INVALID,\n        0,\n        0,\n        {\n%s,\n        },\n        {\n%s,\n        },\n    },\n' % (empty, empty))
    text = ('#ifndef POKEPLATINUM_DATA_UNDERGROUND_HIDEAWAY_ENCOUNTERS_H\n#define POKEPLATINUM_DATA_UNDERGROUND_HIDEAWAY_ENCOUNTERS_H\n\n'
            'static const HideawayEncounters sHideawayEncounters[] = {\n' + ''.join(body) + '};\n\n#endif\n')
    write_text(ENCOUNTERS_H, text, False)


def camel(stem):
    return ''.join(part.capitalize() for part in stem.split('_'))


def write_exit_scripts(header, exits):
    stem = header[len('MAP_HEADER_'):].lower()
    name = camel(stem)
    facings = []
    for ex in exits:
        if ex['facing'] not in facings:
            facings.append(ex['facing'])
    words = {'N': 'North', 'S': 'South', 'E': 'East', 'W': 'West'}
    lines = ['#include "macros/scrcmd.inc"', '#include "res/text/bank/%s.h"' % stem, '#include "res/field/events/events_%s.h"' % stem, '', '']
    for f in facings:
        lines.append('    ScriptEntry %s_Exit%s' % (name, words[f]))
    lines += ['    ScriptEntryEnd', '']
    for f in facings:
        back = next(ex['step_back'] for ex in exits if ex['facing'] == f)
        lines += ['%s_Exit%s:' % (name, words[f]),
                  '    LockAll',
                  '    Message %s_Text_ReturnToTheUnderground' % name,
                  '    ShowYesNoMenu VAR_RESULT',
                  '    GoToIfEq VAR_RESULT, MENU_NO, %s_Stay%s' % (name, words[f]),
                  '    CloseMessage',
                  '    ReturnToUnderground VAR_HIDEAWAY_RETURN_X, VAR_HIDEAWAY_RETURN_Z',
                  '    End',
                  '',
                  '%s_Stay%s:' % (name, words[f]),
                  '    CloseMessage',
                  '    ApplyMovement LOCALID_PLAYER, %s_Movement_StepBack%s' % (name, words[f]),
                  '    WaitMovement',
                  '    ReleaseAll',
                  '    End',
                  '']
    lines.append('    .balign 4, 0')
    for f in facings:
        back = next(ex['step_back'] for ex in exits if ex['facing'] == f)
        lines += ['%s_Movement_StepBack%s:' % (name, words[f]), '    WalkNormal%s' % back, '    EndMovement', '']
    script_path = os.path.join(FIELD, 'scripts', 'scripts_%s.s' % stem)
    text, crlf = read_text(script_path)
    write_text(script_path, '\n'.join(lines), crlf)
    events_path = os.path.join(FIELD, 'events', 'events_%s.json' % stem)
    text, crlf = read_text(events_path)
    events = json.loads(text)
    events['object_events'] = []
    events['coord_events'] = [{'script': facings.index(ex['facing']) + 1, 'x': ex['tile'][0], 'z': ex['tile'][1], 'y': 0,
                               'width': 1, 'length': 1, 'var': 'VAR_MAP_LOCAL_0x00', 'value': 0} for ex in exits]
    write_text(events_path, json.dumps(events, indent=4) + '\n', crlf)


def apply_header(h):
    header = h['header']
    text, crlf = read_text(HEADERS)
    m = re.search(r'(\[%s\]\s*=\s*\{)(.*?)(\n    \})' % header, text, re.S)
    body = re.sub(r'\.areaDataArchiveID = \w+', '.areaDataArchiveID = %s' % h['area_data'], m.group(2))
    body = re.sub(r'\.mapMatrixID = \w+', '.mapMatrixID = %s' % h['matrix'], body)
    body = re.sub(r'\.battleBG = \w+', '.battleBG = %s' % h['battle_bg'], body)
    write_text(HEADERS, text[:m.start(2)] + body + text[m.end(2):], crlf)
    if not h['exits']:
        return
    ex = h['exits'][0]
    write_exit_scripts(header, h['exits'])
    text, crlf = read_text(DOORS_H)
    text = re.sub(r'(%s, )\d+, \d+( \})' % header, r'\g<1>%d, %d\2' % tuple(ex['arrive']), text)
    write_text(DOORS_H, text, crlf)


if __name__ == '__main__':
    sys.exit(main())
