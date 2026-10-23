# Write the dspre_offsets.json that lets the custom DSPRE (branch sourplatinum-offsets) edit a SourPlatinum build.
# DSPRE hardcodes retail Platinum offsets; this finds each table in the build's link map and checks it in the ROM.
# usage: dspre_offsets.py [--map build/main.nef.xMAP] [--rom build/pokeplatinum.us.nds] [-o OUT.json]
# OUT defaults to the ROM path with .dspre_offsets.json, which DSPRE picks up when it sits next to the ROM.
# The map must come from the same build as the ROM (debug and release builds lay out differently).
import argparse, hashlib, json, re, struct, sys

def blz_decompress(data):
    hdr, inc = struct.unpack_from('<II', data, len(data) - 8)
    out = bytearray(data) + bytearray(inc)
    src, dst, stop = len(data) - (hdr >> 24), len(out), len(data) - (hdr & 0xFFFFFF)
    while src > stop:
        src -= 1; flags = data[src]
        for _ in range(8):
            if src <= stop: break
            if flags & 0x80:
                src -= 2; v = data[src] | data[src + 1] << 8
                for _ in range((v >> 12) + 3):
                    dst -= 1; out[dst] = out[dst + (v & 0xFFF) + 3]
            else:
                src -= 1; dst -= 1; out[dst] = data[src]
            flags = flags << 1 & 0xFF
    return bytes(out)

def load_rom(path):
    rom = open(path, 'rb').read()
    game_code = rom[0xC:0x10].decode('ascii')
    arm9_off, _, arm9_ram, arm9_size = struct.unpack_from('<4I', rom, 0x20)
    fat_off, = struct.unpack_from('<I', rom, 0x48)
    ovt_off, ovt_size = struct.unpack_from('<II', rom, 0x50)
    arm9 = rom[arm9_off:arm9_off + arm9_size]
    mp = arm9.find(struct.pack('<II', 0xDEC00621, 0x2106C0DE)) - 0x1C   # module params
    comp_end = struct.unpack_from('<I', arm9, mp + 0x14)[0] if mp >= 0 else 0
    if comp_end:
        n = comp_end - arm9_ram
        arm9 = blz_decompress(arm9[:n]) + arm9[n:]
    overlays = []
    for i in range(ovt_size // 32):
        ov_id, ram, size, bss, _, _, fid, flags = struct.unpack_from('<8I', rom, ovt_off + i * 32)
        start, end = struct.unpack_from('<II', rom, fat_off + fid * 8)
        data = rom[start:end]
        if flags >> 24 & 1:
            data = blz_decompress(data[:flags & 0xFFFFFF])
        overlays.append((ram, size + bss, data))
    return game_code, (arm9_ram, arm9), overlays, hashlib.sha1(rom).hexdigest()

def load_map(path):
    """Returns {section: [(addr, size, name)]} for the code/data sections, in link order."""
    secs, cur = {}, None
    for l in open(path, encoding='latin1'):
        m = re.match(r'# \.(\S+)\s*$', l)
        if m:
            cur = secs.setdefault(m.group(1), []); continue
        m = re.match(r'\s+([0-9A-F]{8}) ([0-9A-F]{8}) (\S+)\s+(\S+)\s+\(', l)
        if m and cur is not None and m.group(4) not in ('$d', '$t', '$a') and not m.group(4).startswith('.'):
            cur.append((int(m.group(1), 16), int(m.group(2), 16), m.group(4)))
    return secs

class Build:
    def __init__(self, map_path, rom_path):
        self.game_code, self.arm9, self.overlays, self.sha1 = load_rom(rom_path)
        secs = load_map(map_path)
        names = list(secs)
        # overlay sections follow ARM9 in overlay ID order, from dummy1 up to the first non-overlay section
        first = names.index('dummy1')
        ovs = [n for n in names[first:] if not n.endswith('.bss')]
        ovs = ovs[:next(i for i, n in enumerate(ovs) if '.' in n)]
        if len(ovs) != len(self.overlays):
            sys.exit(f'map has {len(ovs)} overlay sections but the ROM has {len(self.overlays)} overlays; wrong map for this ROM?')
        for i, n in enumerate(ovs):
            ram, size, _ = self.overlays[i]
            if secs[n] and not ram <= secs[n][0][0] < ram + size:
                sys.exit(f'map section .{n} does not sit at overlay {i} (0x{ram:08X}); wrong map for this ROM?')
        self.sections = {'main': secs['main'], **{i: secs[n] for i, n in enumerate(ovs)}}

    def sym(self, where, name):
        hits = [s for s in self.sections[where] if s[2] == name]
        if len(hits) != 1:
            raise LookupError(f'{len(hits)} symbols named {name} in {"ARM9" if where == "main" else f"overlay {where}"}')
        return hits[0]

    def file(self, where):
        """(RAM base, decompressed bytes) of the ARM9 or an overlay."""
        if where == 'main':
            return self.arm9
        ram, _, data = self.overlays[where]
        return ram, data

    def offset(self, where, addr):
        base, data = self.file(where)
        if not base <= addr < base + len(data):
            raise LookupError(f'0x{addr:08X} is outside the file')
        return addr - base

# Each entry: DSPRE key, where it lives ('main' = ARM9, or an overlay ID), how to find it, and the symbol(s).
#   data:    the table's own offset
#   literal: offset of the literal-pool word inside FUNC that points at the table
#   code:    a fixed spot inside FUNC, checked by CHECK so an edited function is caught instead of misread
def u16(d, o): return struct.unpack_from('<H', d, o)[0]
def u32(d, o): return struct.unpack_from('<I', d, o)[0]

SPECS = [
    ('headerTableOffset',                     'main', 'data', 'sMapHeaders'),
    ('arm9spawnOffset',                       'main', 'data', 'sPlayerStartLocation'),
    ('flyTableOffset',                        'main', 'data', 'sSpawnLocations'),
    ('itemTableOffset',                       'main', 'data', 'sItemArchiveIDs'),
    ('machineMoveOffset',                     'main', 'data', 'sTMHMMoves'),
    ('trainerClassGenderTableVanillaOffset',  'main', 'data', 'sTrainerClassGender'),
    ('trainerClassGenderTablePointerOffset',  'main', 'literal', 'TrainerClass_Gender', 'sTrainerClassGender'),
    ('monIconPalTablePointerOffset',          'main', 'literal', 'PokeIconPaletteIndex', 'sPokemonIconPaletteIndex'),
    ('effectsComboTableOffsetToRAMAddress',   'main', 'literal', 'EncEffects_CutInEffectForPair', 'sEncEffectsTable'),
    ('encounterMusicTableOffsetToRAMAddress', 'main', 'literal', 'FieldBGM_GetEyesMeetForTrainer', 'sTrainerEncounterBGMs'),
    ('trainerNameLenOffset',                  'main', 'code', 'Trainer_Encounter', 0x6E,
        lambda d, o: d[o + 1] == 0x22, 'movs r2, #len'),
    ('OWTableOffset',                         5, 'data', 'gObjectEventGfxTexturesTable'),
    ('cameraTblOffsetsToRAMaddress',          5, 'literal', 'FieldCamera_Create', 'sCameraTypes'),
    ('eggMoveTableOffset',                    5, 'data', 'sEggMoves'),
    ('griseousOrbScriptIdOffset',             9, 'code', 'sMapObjectEventTurnbackCaveRoom_GriseousOrbItem', 0x12,
        lambda d, o: u16(d, o) >= 7000, 'an item script ID (7000+)'),
    ('pickupCommonItemsOffset',               16, 'data', 'sCommonPickupItems'),
    ('pickupRareItemsOffset',                 16, 'data', 'sRarePickupItems'),
    ('pickupWeightTableOffset',               16, 'data', 'sCommonPickupRate'),
    ('pickupActivationDivisorOffset',         16, 'code', 'BtlCmd_GenerateEndOfBattleItem', 0x72,
        lambda d, o: d[o + 1] == 0x21 and d[o] > 0, 'movs r1, #divisor'),
    ('trainerClassPrizeMulTableVanillaOffset', 16, 'data', 'sTrainerClassPrizeMul'),
    ('trainerClassPrizeMulTablePointerOffset', 16, 'literal', 'BattleScript_CalcPrizeMoney', 'sTrainerClassPrizeMul'),
    ('initialMoneyOverlayOffset',             57, 'code', 'StartNewSave', 0x28,
        lambda d, o: u32(d, o) <= 999999, 'the starting money (0-999999)'),
    ('starterSpeciesOffset',                  78, 'code', 'GetSelectedSpecies', 0x24,
        lambda d, o: all(1 <= u32(d, o + 4 * i) <= 493 for i in range(3)), 'three species IDs'),
]

# DSPRE keeps these overlay IDs fixed (some are not even overridable), so the build must keep them too.
EXPECTED_OVERLAYS = {'OWTableOffset': 5, 'eggMoveTableOffset': 5, 'griseousOrbScriptIdOffset': 9}

def resolve(b, spec):
    key, where, kind = spec[:3]
    _, data = b.file(where)
    if kind == 'data':
        addr, size, _ = b.sym(where, spec[3])
        return b.offset(where, addr), size
    if kind == 'literal':
        faddr, fsize, _ = b.sym(where, spec[3])
        taddr, tsize, _ = b.sym(where, spec[4])
        start = b.offset(where, faddr)
        hits = [o for o in range((start + 3) & ~3, start + fsize - 3, 4) if u32(data, o) == taddr]
        if not hits:
            raise LookupError(f'no pointer to {spec[4]} inside {spec[3]}')
        return hits[0], tsize
    faddr, fsize, _ = b.sym(where, spec[3])
    rel, check, what = spec[4:7]
    o = b.offset(where, faddr) + rel
    if rel >= fsize or not check(data, o):
        raise LookupError(f'{spec[3]}+0x{rel:X} is no longer {what}; the function changed, update its entry in {__file__}')
    return o, None

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--map', default='build/main.nef.xMAP')
    ap.add_argument('--rom', default='build/pokeplatinum.us.nds')
    ap.add_argument('-o', '--out')
    args = ap.parse_args()
    out_path = args.out or re.sub(r'\.nds$', '', args.rom, flags=re.I) + '.dspre_offsets.json'

    b = Build(args.map, args.rom)
    if b.game_code != 'CPUE':
        sys.exit(f'game code is {b.game_code}; DSPRE offsets here are for Platinum US (CPUE)')

    result, errors = {}, []
    for spec in SPECS:
        key, where = spec[:2]
        try:
            if key in EXPECTED_OVERLAYS and where != EXPECTED_OVERLAYS[key]:
                raise LookupError(f'expected in overlay {EXPECTED_OVERLAYS[key]}')
            off, size = resolve(b, spec)
        except LookupError as e:
            errors.append(f'{key}: {e}'); continue
        result[key] = [f'0x{off:X}'] if key == 'cameraTblOffsetsToRAMaddress' else f'0x{off:X}'
        print(f'{key:40} {"ARM9" if where == "main" else f"ov{where}":5} 0x{off:X}')

        # table sizes DSPRE assumes for retail
        _, data = b.file(where)
        if key == 'flyTableOffset':
            if size % 16: errors.append(f'sSpawnLocations is 0x{size:X} bytes, not whole 16-byte entries')
            result['flyTableSize'] = size // 16
        elif key == 'trainerClassGenderTableVanillaOffset':
            result['trainerClassGenderTableVanillaCount'] = size
        elif key == 'trainerClassPrizeMulTableVanillaOffset':
            result['trainerClassPrizeMulTableVanillaCount'] = size
        elif key == 'effectsComboTableOffsetToRAMAddress' and size != 35 * 4:
            errors.append(f'sEncEffectsTable has {size // 4} entries but DSPRE always reads 35 for Platinum')
        elif key == 'encounterMusicTableOffsetToRAMAddress' and data[off - 10] != size // 4:
            errors.append(f'DSPRE reads the encounter music entry count from 10 bytes before the pointer, '
                          f'but finds {data[off - 10]} there instead of {size // 4}')

    if errors:
        print('\nnot written, these need fixing first:\n  ' + '\n  '.join(errors), file=sys.stderr)
        sys.exit(1)

    doc = {'_comment': 'Generated by sourplatinum/tools/dspre_offsets.py; regenerate after every build.',
           '_rom': args.rom.replace('\\', '/').split('/')[-1], '_romSha1': b.sha1, 'gameCode': b.game_code, **result}
    with open(out_path, 'w', newline='\n') as f:
        json.dump(doc, f, indent=2)
        f.write('\n')
    print(f'\nwrote {out_path}')

if __name__ == '__main__':
    main()
