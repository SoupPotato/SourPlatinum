import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, HERE)
from underground_block_builder import read_png
from make_underground_top_screen import png_indices, png_palette, write_png

DIR = os.path.join(REPO, 'res', 'graphics', 'underground_top_screen')
FULL = os.path.join(DIR, 'background_full.png')
ORIGINAL = os.path.join(DIR, 'background_full_original.png')
MAP_TILES = os.path.join(HERE, 'underground_layout_editor_assets', 'map_tiles_10.png')
MAP_TILES_INDEX = os.path.join(HERE, 'underground_layout_editor_assets', 'map_tiles_10.json')
ZOOM = os.path.join(DIR, 'zoom_full.png')
SHEET = os.path.join(HERE, 'underground_layout_editor_assets', 'dual_tunnel_tiles.png')

VARIANTS = {653: (55, 95), 654: (93, 95), 656: (143, 95), 657: (182, 95), 662: (228, 95), 663: (267, 95), 659: (318, 95),
            652: (55, 133), 651: (93, 133), 655: (143, 133), 658: (182, 133), 661: (228, 133), 664: (267, 133), 660: (318, 133)}
BIG = (9, 114)
WALL = (58, 40, 30)
FLOOR = (214, 186, 140)
BASE_WALL = (79, 64, 79)
BASE_FLOOR = (181, 159, 150)
ZOOM_PALETTE = [(0, 0, 0), WALL, FLOOR, BASE_WALL, BASE_FLOOR]
MAP_WALL_INDEX, MAP_FLOOR_INDEX = 1, 14
MAP_TILE = 10
MAP_X, MAP_Y = 57, 6


def nearest(c, palette):
    return min(range(1, len(palette)), key=lambda i: sum((a - b) ** 2 for a, b in zip(c, palette[i])))


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if not args:
        print('usage: make_underground_map_images.py layout.json [--small-map]')
        return 1
    layout = json.load(open(args[0]))['maps']
    small_map = '--small-map' in sys.argv
    sw, sh, sheet = read_png(SHEET)
    zoom = [[1] * 480 for _ in range(480)]
    for r in range(15):
        for c in range(15):
            v = layout[r][c]
            if v == 'HIDEAWAY' or v.endswith('_HIDEAWAY'):
                sx, sy = BIG if v == 'HIDEAWAY' else VARIANTS[int(v.split('_')[1])]
                for z in range(32):
                    for x in range(32):
                        zoom[r * 32 + z][c * 32 + x] = nearest(sheet[sy + z][sx + x][:3], ZOOM_PALETTE[:3])
                continue
            n = int(v.split('_')[1])
            d = open(os.path.join(REPO, 'res', 'field', 'maps', 'data', 'map_data_%03d.bin' % n), 'rb').read()
            for z in range(32):
                for x in range(32):
                    solid = struct.unpack_from('<H', d, 16 + 2 * (z * 32 + x))[0] & 0x8000
                    if n == 649:
                        zoom[r * 32 + z][c * 32 + x] = 3 if solid else 4
                    else:
                        zoom[r * 32 + z][c * 32 + x] = 1 if solid else 2
    write_png(ZOOM, 480, 480, zoom, ZOOM_PALETTE + [(0, 0, 0)] * (16 - len(ZOOM_PALETTE)))

    if not small_map:
        print('wrote zoom_full.png (480x480); background_full.png left as it is (add --small-map to redraw it from the 10x10 tiles)')
        return 0

    tw, th, tiles = read_png(MAP_TILES)
    index = json.load(open(MAP_TILES_INDEX))
    w, h, px = png_indices(ORIGINAL)
    palette = png_palette(ORIGINAL)[:16]
    palette += [(0, 0, 0)] * (16 - len(palette))
    palette[MAP_WALL_INDEX] = WALL
    palette[MAP_FLOOR_INDEX] = FLOOR
    for r in range(2, 15):
        for c in range(1, 15):
            sx, sy = index[layout[r][c]]
            for z in range(MAP_TILE):
                for x in range(MAP_TILE):
                    floor = nearest(tiles[sy + z][sx + x][:3], ZOOM_PALETTE[:3]) == 2
                    px[MAP_Y + (r - 2) * MAP_TILE + z][MAP_X + (c - 1) * MAP_TILE + x] = MAP_FLOOR_INDEX if floor else MAP_WALL_INDEX
    write_png(FULL, w, h, px, palette)
    print('wrote zoom_full.png (480x480) and background_full.png (256x192)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
