#!/usr/bin/env python3
"""Builds res/fonts/font_banner.png and font_banner.json, the font of the ability banners, from a sheet of Gen 5 glyphs
(res/fonts/font_banner_sheet.png).

The sheet has a cyan background, glyphs with a dark outline and a white fill, one glyph after another with a column of
background between them. Its rows are the digits, A-Z, a-z and (lower down) a few punctuation marks, among them the apostrophe. Every glyph that
isn't on the sheet (accents, most punctuation) keeps the glyph of the system font, so that any name can be printed.

The outline becomes color 2 of the font (the shadow color) and the fill color 1 (the text color). The banner prints with
the white of the art as text color and the dark as shadow color.

Needs Pillow. Usage: make_banner_font.py [repo root]
"""
import json
import os
import re
import sys

from PIL import Image

ROOT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), '..', '..')
FONTS = os.path.join(ROOT, 'res', 'fonts')

CELL = 16
CELL_TOP = 4  # the top of the 9 pixel high glyphs inside the 16 pixel cell, so that the text sits in the middle of the line
BACKGROUND = (0, 186, 243)
OUTLINE = (33, 33, 33)
GLYPH_HEIGHT = 9
COLOR_FILL = 1
COLOR_OUTLINE = 2
SPACE_WIDTH = 2

charmap = {}
for line in open(os.path.join(ROOT, 'tools', 'msgenc', 'charmap.txt'), encoding='utf-8'):
    m = re.match(r'^\s*([0-9A-Fa-f]{4})=(.)$', line.rstrip('\n'))
    if m:
        charmap.setdefault(m.group(2), int(m.group(1), 16))

sheet = Image.open(os.path.join(FONTS, 'font_banner_sheet.png')).convert('RGB')
system = Image.open(os.path.join(FONTS, 'font_system.png'))
widths = json.load(open(os.path.join(FONTS, 'font_system.json')))['glyphWidths']

out = system.copy()


def segments(top):
    """The x ranges of the glyphs in the rows top..top + 8 of the sheet."""
    columns = [x for x in range(sheet.width) if any(sheet.getpixel((x, y)) != BACKGROUND for y in range(top, top + GLYPH_HEIGHT))]
    result, start, prev = [], None, None
    for x in columns:
        if start is None:
            start = x
        elif x != prev + 1:
            result.append((start, prev))
            start = x
        prev = x
    result.append((start, prev))
    return result


def put_char(char, top, span):
    # Glyph number n is the glyph of character code n + 1 (the codes start at the ideographic space), in the sheet of
    # glyphs and in the table of widths
    glyph = charmap[char] - 1
    x0, x1 = span
    width = x1 - x0 + 1
    cx, cy = (glyph % 16) * CELL, (glyph // 16) * CELL

    for y in range(CELL):
        for x in range(CELL):
            out.putpixel((cx + x, cy + y), 0)

    for y in range(GLYPH_HEIGHT):
        for x in range(width):
            pixel = sheet.getpixel((x0 + x, top + y))
            if pixel == BACKGROUND:
                continue
            out.putpixel((cx + x, cy + CELL_TOP + y), COLOR_OUTLINE if pixel == OUTLINE else COLOR_FILL)

    widths[glyph] = width


digits = segments(2)
assert len(digits) == 16
for i in range(10):
    put_char(str(i), 2, digits[i])

upper = segments(12)
lower = segments(22)
assert len(upper) == 26 and len(lower) == 26
for i in range(26):
    put_char(chr(ord('A') + i), 12, upper[i])
    put_char(chr(ord('a') + i), 22, lower[i])

# The hyphen and the full stop are at the start of the fifth row, which sits one pixel lower than the others
punctuation = segments(43)
put_char('-', 43, punctuation[0])
put_char('.', 43, punctuation[1])

# The apostrophe is the eleventh glyph of the fourth row, the one before the parentheses
punctuation = segments(32)
put_char('’', 32, punctuation[10])
put_char('‘', 32, punctuation[10])

# A space is 2 pixels wide
widths[charmap[' '] - 1] = SPACE_WIDTH

out.save(os.path.join(FONTS, 'font_banner.png'))

rows = []
for i in range(0, len(widths), 16):
    rows.append(', '.join('%2d' % w for w in widths[i:i + 16]))
text = '{\n\t"maxGlyphWidth": 16,\n\t"maxGlyphHeight": 16,\n\t"glyphWidths": [\n' + ',\n'.join('        ' + r for r in rows) + '\n    ]\n}\n'
open(os.path.join(FONTS, 'font_banner.json'), 'w', newline='\n').write(text)
print('ok')
