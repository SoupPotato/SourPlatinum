import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
from import_underground_layout import read_text, write_text

LIGHT_DIR = os.path.join(ROOT, 'res', 'field', 'lighting')
OUT = os.path.join(HERE, 'underground_block_editor_assets', 'hideaway_lighting.json')
FIRST_FIXED = 4
FIXED = [('Dawn', 3), ('Morning', 4), ('Day', 5), ('Noon', 7), ('Afternoon', 9), ('Sunset', 11), ('Dusk', 13), ('Night', 14)]
CYCLES = {0: 'Outdoors (follows the clock)', 1: 'Cave', 2: 'Dark cave (Mt. Coronet)', 3: 'Lighting set 3'}
WHOLE_DAY = 43200


def summary(seg):
    return {'lights': [{'enabled': l['enabled'], 'color': [l['color']['red'], l['color']['green'], l['color']['blue']],
                        'direction': [l['direction']['x'], l['direction']['y'], l['direction']['z']]} for l in seg['lights']],
            'diffuse': [seg['diffuseColor'][k] for k in ('red', 'green', 'blue')],
            'ambient': [seg['ambientColor'][k] for k in ('red', 'green', 'blue')],
            'emission': [seg['emissionColor'][k] for k in ('red', 'green', 'blue')]}


def main():
    outdoor = json.load(open(os.path.join(LIGHT_DIR, 'lighting_set_000.json')))
    info = {}
    for n, label in CYCLES.items():
        segs = json.load(open(os.path.join(LIGHT_DIR, 'lighting_set_%03d.json' % n)))
        noon = next(s for s in segs if s['endTime'] >= 27000)
        info['lighting_set_%03d' % n] = dict(summary(noon), label=label, fixed=False)
    ids = []
    for k, (label, seg_index) in enumerate(FIXED):
        n = FIRST_FIXED + k
        seg = dict(outdoor[seg_index], endTime=WHOLE_DAY)
        text, crlf = read_text(os.path.join(LIGHT_DIR, 'lighting_set_000.json'))
        write_text(os.path.join(LIGHT_DIR, 'lighting_set_%03d.json' % n), json.dumps([seg], indent=4), crlf)
        name = 'lighting_set_%03d' % n
        info[name] = dict(summary(seg), label='%s (fixed)' % label, fixed=True)
        ids.append(name)
    text, crlf = read_text(os.path.join(LIGHT_DIR, 'lighting_sets.order'))
    lines = [l for l in text.split('\n') if l and not (re.fullmatch(r'lighting_set_(\d+)', l) and int(l[-3:]) >= FIRST_FIXED)]
    write_text(os.path.join(LIGHT_DIR, 'lighting_sets.order'), '\n'.join(lines + ids) + '\n', crlf)
    text, crlf = read_text(os.path.join(LIGHT_DIR, 'meson.build'))
    text = re.sub(r"\n\s*'lighting_set_0(0[4-9]|[1-9]\d)\.json',?", '', text)
    text = text.replace("    'lighting_set_002.json'),", "    'lighting_set_002.json',\n" + ',\n'.join("    '%s.json'" % i for i in ids) + '),')
    write_text(os.path.join(LIGHT_DIR, 'meson.build'), text, crlf)
    info['reference'] = summary(outdoor[7])
    json.dump(info, open(OUT, 'w'), indent=1)
    print('wrote %d fixed lighting sets (%s to %s)' % (len(ids), ids[0], ids[-1]))
    return 0


if __name__ == '__main__':
    sys.exit(main())
