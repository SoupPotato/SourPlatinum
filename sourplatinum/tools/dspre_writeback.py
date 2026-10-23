# Write edits made in the DSPRE fork back into this tree's source files.
# usage (in WSL, from the Windows tree): python3 sourplatinum/tools/dspre_writeback.py CONTENTS_DIR
#     [--baseline build/dspre/sourplatinum.baseline.nds] [--clone ~/SourPlatinum] [--dry-run] [--report OUT.json]
#   or: python3 sourplatinum/tools/dspre_writeback.py --self-test
# CONTENTS_DIR is DSPRE's <rom>_DSPRE_contents folder for build/dspre/sourplatinum.nds (Windows paths are accepted).
#
# Every NARC member DSPRE unpacked is compared with the same member in the baseline ROM that dspre_build.py published.
# Changed members of a supported kind (trainers, wild encounters, species stats/learnsets/evolutions, items, text) are
# decoded, diffed field by field against the baseline and only the changed fields are written into the matching
# source file, so untouched fields keep their exact text. Anything else that changed (other NARCs, ARM9, overlays) is
# listed as not written back; it is lost on the next build.
# --self-test decodes every member of the baseline and checks it against the source files, which proves the decoders
# still match the build tools after either side changes.
import argparse, hashlib, json, os, re, struct, subprocess, sys, tempfile
import ndspy.codeCompression, ndspy.narc, ndspy.rom

TOOLS = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(TOOLS))
sys.path.insert(0, TOOLS)
from dspre_offsets import load_rom
import jfmt

# DSPRE's Platinum folder names (RomInfo.SetNarcDirs) -> NARC path in the ROM
NARCS = {
    'personalPokeData': 'poketool/personal/pl_personal.narc', 'pokemonBattleSprites': 'poketool/pokegra/pl_pokegra.narc',
    'otherPokemonBattleSprites': 'poketool/pokegra/pl_otherpoke.narc', 'pokemonSpriteOffsets': 'poketool/poke_edit/pl_poke_data.narc',
    'pokeHeight': 'poketool/pokegra/height.narc', 'pokeHeightForms': 'poketool/pokegra/height_o.narc',
    'battleBg': 'battle/graphic/pl_batt_bg.narc', 'battleObj': 'battle/graphic/pl_batt_obj.narc',
    'synthOverlay': 'data/weather_sys.narc', 'dynamicHeaders': 'debug/cb_edit/d_test.narc',
    'textArchives': 'msgdata/pl_msg.narc', 'matrices': 'fielddata/mapmatrix/map_matrix.narc',
    'maps': 'fielddata/land_data/land_data.narc', 'exteriorBuildingModels': 'fielddata/build_model/build_model.narc',
    'buildingConfigFiles': 'fielddata/areadata/area_build_model/area_build.narc',
    'buildingTextures': 'fielddata/areadata/area_build_model/areabm_texset.narc',
    'mapTextures': 'fielddata/areadata/area_map_tex/map_tex_set.narc', 'areaData': 'fielddata/areadata/area_data.narc',
    'eventFiles': 'fielddata/eventdata/zone_event.narc', 'OWSprites': 'data/mmodel/mmodel.narc',
    'scripts': 'fielddata/script/scr_seq.narc', 'trainerProperties': 'poketool/trainer/trdata.narc',
    'trainerParty': 'poketool/trainer/trpoke.narc', 'trainerGraphics': 'poketool/trgra/trfgra.narc',
    'moveData': 'poketool/waza/pl_waza_tbl.narc', 'monIcons': 'poketool/icongra/pl_poke_icon.narc',
    'encounters': 'fielddata/encountdata/pl_enc_data.narc', 'encounterExtended': 'arc/encdata_ex.narc',
    'learnsets': 'poketool/personal/wotbl.narc', 'evolutions': 'poketool/personal/evo.narc',
    'battleTowerTrainers': 'battle/b_pl_tower/pl_btdtr.narc', 'battleTowerPokemon': 'battle/b_pl_tower/pl_btdpm.narc',
    'itemData': 'itemtool/itemdata/pl_item_data.narc', 'itemIcons': 'itemtool/itemdata/item_icon.narc',
    'tradeData': 'fielddata/pokemon_trade/fld_trade.narc', 'trainerTextOffset': 'poketool/trmsg/trtblofs.narc',
    'trainerTextTable': 'poketool/trmsg/trtbl.narc',
}

def to_wsl(path):
    return subprocess.check_output(['wslpath', '-u', path], text=True).strip() if re.match(r'^[A-Za-z]:[\\/]', path) else path

def lines(rel):
    return [l.strip() for l in open(os.path.join(REPO, rel)) if l.strip()]

# --- JSON formatting per directory (see CLAUDE.md, "JSON formatting") -------------------------------------------------

def species_inline(path, v):
    if path[-1:] in (('types',), ('egg_groups',), ('abilities',)):
        return True
    if path[-3:] == ('learnset', 'by_level', '[]') or path[-2:] == ('icon_palette', '[]'):
        return True
    if path[-2:] == ('evolutions', '[]') and len(v) == 2:
        return True
    return len(v) == 1 and not isinstance(v[0], (list, dict))

def dumps(rel, data):
    if rel.startswith('res/pokemon/'):
        return jfmt.dumps(data, species_inline)
    indent = 2 if rel.startswith(('res/items/data/', 'res/text/')) else 4
    return json.dumps(data, indent=indent, ensure_ascii=False)

MISSING = object()

def apply_changes(src, old, new):
    """Copy into src (a source JSON object) only the values that differ between the old and new decodes."""
    for key, nv in new.items():
        ov, sv = old.get(key, MISSING), src.get(key, MISSING)
        if nv == ov:
            continue
        if isinstance(nv, dict) and isinstance(ov, dict) and isinstance(sv, dict):
            apply_changes(sv, ov, nv)
        elif (isinstance(nv, list) and isinstance(ov, list) and isinstance(sv, list) and len(nv) == len(ov) == len(sv)
              and all(isinstance(o, dict) or o == s for o, s in zip(ov, sv))):
            for i, (n, o) in enumerate(zip(nv, ov)):
                if n != o:
                    if isinstance(n, dict) and isinstance(o, dict) and isinstance(sv[i], dict):
                        apply_changes(sv[i], o, n)
                    else:
                        sv[i] = n
        else:
            src[key] = nv

def mismatches(src, dec, path=''):
    """Paths where a decode disagrees with the source (keys only in the source are ignored)."""
    out = []
    if isinstance(dec, dict) and isinstance(src, dict):
        for k, v in dec.items():
            out += mismatches(src.get(k, MISSING), v, f'{path}.{k}')
    elif isinstance(dec, list) and isinstance(src, list) and len(dec) == len(src):
        for i, (s, d) in enumerate(zip(src, dec)):
            out += mismatches(s, d, f'{path}[{i}]')
    elif src != dec:
        out.append(f'{path}: source {"(missing)" if src is MISSING else json.dumps(src, ensure_ascii=False)[:60]} '
                   f'!= decoded {json.dumps(dec, ensure_ascii=False)[:60]}')
    return out

class Ctx:
    def __init__(self, contents, baseline, clone, dry_run):
        self.contents, self.baseline, self.clone, self.dry_run = contents, baseline, clone, dry_run
        self.rom = ndspy.rom.NintendoDSRom.fromFile(baseline)
        self._narcs, self._enums, self._json = {}, {}, {}
        self.written, self.not_written, self.errors = [], [], []

    # members
    def old(self, dirname, i):
        if dirname not in self._narcs:
            self._narcs[dirname] = ndspy.narc.NARC(self.rom.getFileByName(NARCS[dirname])).files
        files = self._narcs[dirname]
        return files[i] if i < len(files) else None

    def count(self, dirname):
        self.old(dirname, 0)
        return len(self._narcs[dirname])

    def new(self, dirname, i):
        """DSPRE's copy of a member, or the baseline one if DSPRE never unpacked it."""
        path = self.contents and os.path.join(self.contents, 'unpacked', dirname, '%04d' % i)
        return open(path, 'rb').read() if path and os.path.exists(path) else self.old(dirname, i)

    def changed(self, dirname):
        """Indices of members DSPRE changed or added."""
        d = os.path.join(self.contents, 'unpacked', dirname)
        out = []
        if os.path.isdir(d):
            for f in os.listdir(d):
                if not f.isdigit():
                    continue
                old, new = self.old(dirname, int(f)), open(os.path.join(d, f), 'rb').read()
                # DSPRE's Pokémon editor saves an absent female height (an empty file) as a single 0 byte
                if old != new and not (dirname == 'pokeHeight' and old == b'' and new == b'\0'):
                    out.append(int(f))
        return sorted(out)

    # value <-> name
    def enum(self, module):
        """{value: name} from build/generated/<module>.py in the clone (written by metang)."""
        if module not in self._enums:
            vals = {}
            for line in open(os.path.join(self.clone, 'build', 'generated', module + '.py')):
                m = re.match(r'\s+([A-Z][A-Z0-9_]*)\s*=\s*([0-9()<\s]+)$', line)
                if m:
                    vals.setdefault(eval(m.group(2), {'__builtins__': {}}), m.group(1))
            self._enums[module] = vals
        return self._enums[module]

    def defs(self, header, prefix):
        """{value: name} for '#define PREFIX_...' constants in include/<header>."""
        key = (header, prefix)
        if key not in self._enums:
            vals = {}
            for line in open(os.path.join(REPO, 'include', header), encoding='utf-8'):
                m = re.match(rf'#define\s+({prefix}_[A-Z0-9_]+)\s+(.+?)\s*(//.*)?$', line)
                if m and re.fullmatch(r'[0-9xA-Fa-f()<>| ]+', m.group(2)):
                    vals.setdefault(eval(m.group(2), {'__builtins__': {}}), m.group(1))
            self._enums[key] = vals
        return self._enums[key]

    def name(self, module, value, table=None):
        try:
            return (table if table is not None else self.enum(module))[value]
        except KeyError:
            raise ValueError(f'{value} is not a known {module} value')

    # source files
    def json(self, rel):
        if rel not in self._json:
            text = open(os.path.join(REPO, rel), encoding='utf-8', newline='').read()
            self._json[rel] = (json.loads(text), text)
        return self._json[rel][0]

    def flush(self):
        for rel, (data, text) in self._json.items():
            out = dumps(rel, data) + ('\n' if text.endswith('\n') else '')
            if out != text:
                if not self.dry_run:
                    with open(os.path.join(REPO, rel), 'w', encoding='utf-8', newline='\n') as f:
                        f.write(out)
                self.written.append(rel)

# --- record kinds: one NARC member (or one member per NARC) <-> one source JSON file ----------------------------------

class Kind:
    dirs = ()

    def __init__(self, ctx):
        self.ctx = ctx

    def target(self, i):
        """Source file for member i, or raise LookupError with the reason it has none."""
        raise NotImplementedError

    def decode(self, get, i):
        raise NotImplementedError

    def indices(self):
        return range(self.ctx.count(self.dirs[0]))

    def writeback(self):
        ctx = self.ctx
        for i in sorted(set(i for d in self.dirs for i in ctx.changed(d))):
            try:
                rel = self.target(i)
                old, new = self.decode(ctx.old, i), self.decode(ctx.new, i)
            except LookupError as e:
                ctx.not_written.append(f'{self.dirs[0]} {i}: {e}'); continue
            except (ValueError, struct.error, TypeError) as e:
                ctx.errors.append(f'{self.dirs[0]} {i}: {e}'); continue
            self.apply(rel, old, new)

    def apply(self, rel, old, new):
        apply_changes(self.ctx.json(rel), old, new)

    def self_test(self):
        bad = 0
        for i in self.indices():
            try:
                rel = self.target(i)
            except LookupError:
                continue
            try:
                problems = mismatches(self.ctx.json(rel), self.decode(self.ctx.old, i))
            except (ValueError, struct.error, TypeError) as e:
                problems = [f'decode failed: {e}']
            if problems:
                bad += 1
                if bad <= 5:
                    print(f'  {rel}:', *problems[:4], sep='\n    ')
        print(f'{type(self).__name__}: {bad} file(s) disagree with the build')
        return bad

class Trainers(Kind):
    dirs = ('trainerProperties', 'trainerParty')

    def __init__(self, ctx):
        super().__init__(ctx)
        self.ids = lines('generated/trainers.txt')

    def target(self, i):
        if i == 0:
            raise LookupError('TRAINER_NONE has no source file')
        if i >= len(self.ids):
            raise LookupError('new trainers can only be added in source (generated/trainers.txt)')
        return f'res/trainers/data/{self.ids[i][len("TRAINER_"):].lower()}.json'

    def decode(self, get, i):
        ctx = self.ctx
        mon_type, cls, sprite, size, *rest = struct.unpack('<BBBB4HII', get('trainerProperties', i))
        party = get('trainerParty', i)
        has_moves, has_items = bool(mon_type & 1), bool(mon_type & 2)
        out = {
            'class': ctx.name('trainer_classes', cls),
            'items': [ctx.name('items', x) for x in rest[:4] if x],
            'ai_flags': [ctx.name('ai_flags', 1 << b) for b in range(32) if rest[4] >> b & 1],
            'double_battle': bool(rest[5]), 'party': [],
        }
        o = 0
        for _ in range(size):
            iv, level, species = struct.unpack_from('<3H', party, o); o += 6
            item = moves = None
            if has_items:
                item = ctx.name('items', struct.unpack_from('<H', party, o)[0]); o += 2
            if has_moves:
                moves = [ctx.name('moves', m) for m in struct.unpack_from('<4H', party, o)]; o += 8
                while moves and moves[-1] == 'MOVE_NONE':
                    moves.pop()
            seal, = struct.unpack_from('<H', party, o); o += 2
            out['party'].append({'species': ctx.name('species', species & 0x3FF), 'form': species >> 10, 'level': level,
                                 'item': item, 'moves': moves, 'iv_scale': iv, 'ball_seal': seal})
        return out

    def apply(self, rel, old, new):
        data = self.ctx.json(rel)
        # the first mon's item/moves decide the whole party's format, so a format change rewrites those fields
        if new['party'] and old['party'] and any((new['party'][0][f] is None) != (old['party'][0][f] is None) for f in ('item', 'moves')):
            for n, mon in enumerate(new['party'][:len(data['party'])]):
                data['party'][n]['item'], data['party'][n]['moves'] = mon['item'], mon['moves']
        party_old, party_new = old.pop('party'), new.pop('party')
        apply_changes(data, old, new)
        if len(party_new) == len(party_old) == len(data['party']):
            apply_changes(data, {'party': party_old}, {'party': party_new})
        else:
            for n, mon in enumerate(party_new):
                if n < len(data['party']) and n < len(party_old):
                    apply_changes(data['party'][n], party_old[n], mon)
                elif n < len(data['party']):
                    data['party'][n].update(mon)
                else:
                    data['party'].append(mon)
            del data['party'][len(party_new):]

class Encounters(Kind):
    dirs = ('encounters',)

    def __init__(self, ctx):
        super().__init__(ctx)
        self.order = lines('res/field/encounters/encounters.order')

    def target(self, i):
        if i >= len(self.order):
            raise LookupError('new encounter files can only be added in source (res/field/encounters)')
        return f'res/field/encounters/{self.order[i]}.json'

    def decode(self, get, i):
        b, sp = get('encounters', i), lambda v: self.ctx.name('species', v)
        u32 = lambda o: struct.unpack_from('<I', b, o)[0]
        def water(o):
            return [{'level_max': b[o + 8 * k], 'level_min': b[o + 8 * k + 1], 'species': sp(u32(o + 8 * k + 4))} for k in range(5)]
        out = {'land_rate': u32(0), 'land_encounters': [{'level': u32(4 + 8 * k), 'species': sp(u32(8 + 8 * k))} for k in range(12)]}
        o = 100
        for key, n in (('swarms', 2), ('day', 2), ('night', 2), ('radar', 4)):
            out[key] = [sp(u32(o + 4 * k)) for k in range(n)]; o += 4 * n
        for key in ('rate_form0', 'rate_form1', 'rate_form2', 'rate_form3', 'rate_form4', 'unown_table'):
            out[key] = u32(o); o += 4
        for key in ('ruby', 'sapphire', 'emerald', 'firered', 'leafgreen'):
            out[key] = [sp(u32(o)), sp(u32(o + 4))]; o += 8
        out['surf_rate'] = u32(o); out['surf_encounters'] = water(o + 4); o += 4 + 40 + 44
        for rod in ('old', 'good', 'super'):
            out[f'{rod}_rod_rate'] = u32(o); out[f'{rod}_rod_encounters'] = water(o + 4); o += 44
        return out

ALT_FORMS = ['deoxys/forms/attack', 'deoxys/forms/defense', 'deoxys/forms/speed', 'wormadam/forms/sandy',
             'wormadam/forms/trash', 'giratina/forms/origin', 'shaymin/forms/sky', 'rotom/forms/heat', 'rotom/forms/wash',
             'rotom/forms/frost', 'rotom/forms/fan', 'rotom/forms/mow']   # speciesproc.c alt_forms_with_data, in order
NUM_TMS = 92
EVO_NO_PARAM = {'EVO_NONE', 'EVO_LEVEL_HAPPINESS', 'EVO_LEVEL_HAPPINESS_DAY', 'EVO_LEVEL_HAPPINESS_NIGHT', 'EVO_TRADE',
                'EVO_LEVEL_MAGNETIC_FIELD', 'EVO_LEVEL_MOSS_ROCK', 'EVO_LEVEL_ICE_ROCK'}
EVO_ITEM_PARAM = {'EVO_TRADE_WITH_HELD_ITEM', 'EVO_USE_ITEM', 'EVO_USE_ITEM_MALE', 'EVO_USE_ITEM_FEMALE',
                  'EVO_LEVEL_WITH_HELD_ITEM_DAY', 'EVO_LEVEL_WITH_HELD_ITEM_NIGHT'}

def species_dirs():
    return [n[len('SPECIES_'):].lower() for n in lines('generated/species.txt')] + ALT_FORMS

class Species(Kind):
    dirs = ('personalPokeData', 'learnsets', 'evolutions')

    def __init__(self, ctx):
        super().__init__(ctx)
        self.registry = species_dirs()

    def target(self, i):
        if i >= len(self.registry):
            raise LookupError('new species can only be added in source (generated/species.txt)')
        rel = f'res/pokemon/{self.registry[i]}/data.json'
        if not os.path.exists(os.path.join(REPO, rel)):
            raise LookupError(f'{rel} does not exist')
        return rel

    def decode(self, get, i):
        ctx = self.ctx
        p = get('personalPokeData', i)
        (hp, atk, df, spe, spa, spd, t0, t1, catch, exp, ev, item_c, item_r, gender, hatch, friend, rate,
         eg0, eg1, ab0, ab1, flee, color) = struct.unpack_from('<6B2BBBH2H4B2B2BBB', p, 0)
        masks = struct.unpack_from('<4I', p, 28)
        tms = [v for v in range(128) if masks[v // 32] >> (v % 32) & 1]
        evs = [ev >> (2 * k) & 3 for k in range(6)]
        out = {
            'base_stats': dict(zip(('hp', 'attack', 'defense', 'speed', 'special_attack', 'special_defense'), (hp, atk, df, spe, spa, spd))),
            'types': [ctx.name('pokemon_types', t0), ctx.name('pokemon_types', t1)],
            'catch_rate': catch, 'base_exp_reward': exp,
            'ev_yields': dict(zip(('hp', 'attack', 'defense', 'speed', 'special_attack', 'special_defense'), evs)),
            'held_items': {'common': ctx.name('items', item_c), 'rare': ctx.name('items', item_r)},
            'gender_ratio': ctx.name('gender_ratios', gender), 'hatch_cycles': hatch, 'base_friendship': friend,
            'exp_rate': ctx.name('exp_rates', rate),
            'egg_groups': [ctx.name('egg_groups', eg0), ctx.name('egg_groups', eg1)],
            'abilities': [ctx.name('abilities', ab0), ctx.name('abilities', ab1)],
            'safari_flee_rate': flee, 'body_color': ctx.name('pokemon_colors', color & 0x7F), 'flip_sprite': bool(color >> 7),
            'learnset': {'by_tm': [f'TM{v + 1:02}' if v < NUM_TMS else f'HM{v - NUM_TMS + 1:02}' for v in tms]},
        }

        by_level, ls = [], get('learnsets', i)
        for o in range(0, len(ls) - 1, 2):
            e, = struct.unpack_from('<H', ls, o)
            if e == 0xFFFF:
                break
            by_level.append([e >> 9, ctx.name('moves', e & 0x1FF)])
        out['learnset']['by_level'] = by_level

        evos, ev_data = [], get('evolutions', i)
        for k in range(7):
            method, param, target = struct.unpack_from('<3H', ev_data, 6 * k)
            m = ctx.name('evolution_methods', method)
            if m == 'EVO_NONE':
                continue
            if m in EVO_NO_PARAM:
                evos.append([m, ctx.name('species', target)]); continue
            if m in EVO_ITEM_PARAM:
                param = ctx.name('items', param)
            elif m == 'EVO_LEVEL_KNOW_MOVE':
                param = ctx.name('moves', param)
            elif m == 'EVO_LEVEL_SPECIES_IN_PARTY':
                param = ctx.name('species', param)
            evos.append([m, param, ctx.name('species', target)])
        out['evolutions'] = evos
        return out

ITEM_FLAGS = [('healSleep', 0, 0), ('healPoison', 0, 1), ('healBurn', 0, 2), ('healFreeze', 0, 3), ('healParalysis', 0, 4),
              ('healConfusion', 0, 5), ('healAttract', 0, 6), ('guardSpec', 0, 7), ('revive', 1, 0), ('reviveAll', 1, 1),
              ('levelUp', 1, 2), ('ppUp', 4, 6), ('ppMax', 4, 7), ('restorePPAllMoves', 5, 1)]
ITEM_NIBBLES = [('atkStages', 1, 4, 15), ('defStages', 2, 0, 15), ('spatkStages', 2, 4, 15), ('spdefStages', 3, 0, 15),
                ('speedStages', 3, 4, 15), ('accStages', 4, 0, 15), ('critStages', 4, 4, 3)]
ITEM_BYTES = [('hpEVs', 7, True), ('atkEVs', 8, True), ('defEVs', 9, True), ('speedEVs', 10, True), ('spatkEVs', 11, True),
              ('spdefEVs', 12, True), ('hpRestored', 13, True), ('ppRestored', 14, False), ('friendshipLow', 15, True),
              ('friendshipMed', 16, True), ('friendshipHigh', 17, True)]

class Items(Kind):
    dirs = ('itemData',)

    def __init__(self, ctx):
        super().__init__(ctx)
        self.items = [n for n in lines('generated/items.txt') if n.startswith('ITEM_') and not n.startswith('ITEM_UNUSED_')]

    def target(self, i):
        if i >= len(self.items):
            raise LookupError('new items can only be added in source (generated/items.txt)')
        return f'res/items/data/{self.items[i][len("ITEM_"):].lower()}.json'

    def decode(self, get, i):
        ctx, b = self.ctx, get('itemData', i)
        d = lambda prefix: ctx.defs('constants/items.h', prefix)
        price, hold, param, pluck, fling, fling_power, gift_power, bits, use_func, battle_use, party_use = \
            struct.unpack_from('<H6BH3B', b, 0)
        gift_type = bits & 31
        out = {
            'price': price, 'effectParam': param, 'holdEffect': ctx.name('item_hold_effects', hold),
            'pluckEffect': ctx.name('PLUCK_EFFECT', pluck, d('PLUCK_EFFECT')),
            'flingEffect': ctx.name('FLING_EFFECT', fling, d('FLING_EFFECT')),
            'flingPower': fling_power, 'naturalGiftPower': gift_power,
            'naturalGiftType': None if gift_type == 31 else ctx.name('pokemon_types', gift_type),
            'preventToss': bool(bits >> 5 & 1), 'canRegister': bool(bits >> 6 & 1),
            'fieldPocket': ctx.name('POCKET', bits >> 7 & 15, d('POCKET')),
            'battlePocket': ctx.name('BATTLE_POCKET_MASK', bits >> 11 & 31, d('BATTLE_POCKET_MASK')),
            'fieldUseFunc': ctx.name('ITEM_USE_FUNC', use_func, d('ITEM_USE_FUNC')),
            'battleUseCategory': ctx.name('BATTLE_USE_CATEGORY', battle_use, d('BATTLE_USE_CATEGORY')),
        }
        if party_use:
            p, params = b[14:34], {}
            for key, byte, bit in ITEM_FLAGS:
                if p[byte] >> bit & 1:
                    params[key] = True
            for key, byte, shift, mask in ITEM_NIBBLES:
                if p[byte] >> shift & mask:
                    params[key] = p[byte] >> shift & mask
            for key, byte, signed in ITEM_BYTES:
                v = struct.unpack_from('<b' if signed else '<B', p, byte)[0]
                if key == 'ppRestored':   # stored in 7 bits, so the source's -1 ("all PP") comes back as 127
                    v = -1 if v & 0x7F == 0x7F else v & 0x7F
                if v:
                    params[key] = v
            out['itemUseParams'] = params
        else:
            out['itemUseParams'] = None
        return out

    def apply(self, rel, old, new):
        data = self.ctx.json(rel)
        # itemUseParams is a set of non-default keys, so a changed set replaces the whole object
        if new.get('itemUseParams', MISSING) != old.get('itemUseParams', MISSING):
            data['itemUseParams'] = new.pop('itemUseParams', None); old.pop('itemUseParams', None)
        apply_changes(data, old, new)

# --- text banks: decoded with the repo's own msgenc -------------------------------------------------------------------

class Text:
    def __init__(self, ctx):
        self.ctx = ctx
        self.order = [l.strip() for l in open(os.path.join(ctx.clone, 'build', 'res', 'text', 'text_banks.order')) if l.strip()]
        trainers = lines('generated/trainers.txt')
        items = lines('generated/items.txt')
        moves = lines('generated/moves.txt')
        species = species_dirs()
        item_rel = lambda i: f'res/items/data/{items[i][len("ITEM_"):].lower()}.json'
        move_rel = lambda i: f'res/moves/{moves[i][len("MOVE_"):].lower()}/data.json'
        # generated banks: message i -> (source file, key path), for the ones DSPRE's editors change
        def species_rel(i):
            if i == 0:
                raise LookupError('SPECIES_NONE\'s name is fixed by speciesproc')
            return f'res/pokemon/{species[i]}/data.json'
        self.generated = {
            'species_name': lambda i: (species_rel(i), ('pokedex_data', 'en', 'name')),
            'item_names': lambda i: (item_rel(i), ('name',)),
            'item_names_plural': lambda i: (item_rel(i), ('plural',)),
            'item_descriptions': lambda i: (item_rel(i), ('description',)),
            'npc_trainer_names': lambda i: (f'res/trainers/data/{trainers[i][len("TRAINER_"):].lower()}.json', ('name',)),
            'move_names': lambda i: (move_rel(i), ('name',)),
            'move_descriptions': lambda i: (move_rel(i), ('description',)),
        }

    @staticmethod
    def field_value(bank, message):
        """A generated bank's message as its source field stores it."""
        value = message.get('en_US')
        if bank == 'npc_trainer_names' and isinstance(value, str):
            value = value.replace('{TRNAME}', '', 1)   # msgenc marks the compressed trainer-name encoding this way
        return value

    def decode(self, data):
        """[{'en_US': ...} or {'garbage': n}] for a bank, via msgenc -d --json."""
        with tempfile.TemporaryDirectory() as tmp:
            bin_path, json_path = os.path.join(tmp, 'bank.bin'), os.path.join(tmp, 'bank.json')
            open(bin_path, 'wb').write(data)
            r = subprocess.run([os.path.join(self.ctx.clone, 'build', 'tools', 'msgenc', 'msgenc'), '-d', '--json',
                                '-c', os.path.join(self.ctx.clone, 'tools', 'msgenc', 'charmap.txt'), json_path, bin_path],
                               capture_output=True, text=True)
            if r.returncode != 0:
                raise ValueError((r.stderr or r.stdout).strip())
            return [{k: v for k, v in m.items() if k != 'id'} for m in json.load(open(json_path, encoding='utf-8'))['messages']]

    def target(self, bank, i, n_messages):
        """(source file, key path) for message i, or raise LookupError."""
        rel = f'res/text/{bank}.json'
        if os.path.exists(os.path.join(REPO, rel)):
            return rel, ('messages', i)
        if bank in self.generated:
            try:
                rel, path = self.generated[bank](i)
            except IndexError:
                raise LookupError(f'message {i} of {bank} has no source entry')
            if os.path.exists(os.path.join(REPO, rel)):
                return rel, path
            raise LookupError(f'{rel} does not exist')
        raise LookupError(f'{bank} is generated from other source files (see generated_text_banks in res/text/meson.build)')

    def set(self, bank, rel, path, message):
        data = self.ctx.json(rel)
        if path[0] == 'messages':
            msgs = data['messages']
            if path[1] < len(msgs):
                entry = msgs[path[1]]
                for k in ('en_US', 'garbage'):
                    entry.pop(k, None)
                entry.update(message)
            else:
                msgs.append({'id': f'{os.path.basename(rel)[:-5]}_dspre_{path[1]:04}', **message})
            return
        if 'en_US' not in message:
            raise ValueError(f'{rel}: a garbage message has no place in {".".join(path)}')
        for k in path[:-1]:
            data = data[k]
        value = self.field_value(bank, message)
        data[path[-1]] = [value] if isinstance(data.get(path[-1]), list) and isinstance(value, str) else value

    def writeback(self):
        ctx = self.ctx
        for i in ctx.changed('textArchives'):
            bank = self.order[i] if i < len(self.order) else f'#{i}'
            try:
                old = self.decode(ctx.old('textArchives', i)) if ctx.old('textArchives', i) else []
                new = self.decode(ctx.new('textArchives', i))
            except ValueError as e:
                ctx.errors.append(f'text bank {bank}: {e}'); continue
            if len(new) < len(old):
                ctx.not_written.append(f'text bank {bank}: removed messages (scripts refer to them by ID, so remove them in source)')
            for n, message in enumerate(new):
                if n < len(old) and message == old[n]:
                    continue
                try:
                    rel, path = self.target(bank, n, len(new))
                    self.set(bank, rel, path, message)
                except LookupError as e:
                    ctx.not_written.append(f'text bank {bank} message {n}: {e}')
                    break
                except ValueError as e:
                    ctx.errors.append(str(e))

    def self_test(self):
        bad = 0
        for i, bank in enumerate(self.order):
            decoded = self.decode(self.ctx.old('textArchives', i))
            for n, message in enumerate(decoded):
                try:
                    rel, path = self.target(bank, n, len(decoded))
                except LookupError:
                    break
                data = self.ctx.json(rel)
                if path[0] == 'messages':
                    src = data['messages'][n] if n < len(data['messages']) else {}
                    src = {k: v for k, v in src.items() if k != 'id'}
                else:
                    for k in path:
                        data = data.get(k, MISSING) if isinstance(data, dict) else MISSING
                    src, message = data, self.field_value(bank, message)
                    if isinstance(src, list) and isinstance(message, str):
                        message = [message]
                if src != message:
                    bad += 1
                    if bad <= 5:
                        print(f'  {bank} message {n} ({rel}): source {json.dumps(src, ensure_ascii=False)[:70]}'
                              f' != decoded {json.dumps(message, ensure_ascii=False)[:70]}')
        print(f'Text: {bad} message(s) disagree with the build')
        return bad

# --- Pokémon icons: res/pokemon/**/icon.png <- pl_poke_icon.narc, palettes <- sPokemonIconPaletteIndex in ARM9 -------

class Icons:
    SHARED = 7   # pl_poke_icon.narc members before the first icon: shared palettes, cells and animations

    def __init__(self, ctx):
        self.ctx = ctx
        species = [n[len('SPECIES_'):].lower() for n in lines('generated/species.txt')]
        # species icons up to the egg (bad_egg has none), then the form icons in res/pokemon/meson.build order
        self.icons = [(s, None) for s in species[:species.index('egg') + 1]]
        form_vars = {}
        for s in species:
            mb = os.path.join(REPO, 'res', 'pokemon', s, 'meson.build')
            if os.path.exists(mb):
                for var, form in re.findall(r"(\w+_icon)\s*=\s*files\('forms/(\w+)/icon\.png'\)", open(mb).read()):
                    form_vars[var] = (s, form)
        block = re.search(r'poke_icon_files \+= \[(.*?)\]', open(os.path.join(REPO, 'res', 'pokemon', 'meson.build')).read(), re.S)
        self.icons += [form_vars[v] for v in re.findall(r'(\w+_icon)', block.group(1))]
        self.table = None
        mp = os.path.join(ctx.clone, 'build', 'main.nef.xMAP')
        m = re.search(r'^\s+([0-9A-F]{8}) ([0-9A-F]{8}) \.rodata\s+sPokemonIconPaletteIndex\s', open(mp, encoding='latin1').read(), re.M)
        if m and int(m.group(2), 16) == len(self.icons):
            self.table = int(m.group(1), 16) - 0x02000000
        _, (_, self.arm9_old), _, _ = load_rom(ctx.baseline)
        arm9_new = ctx.contents and next((os.path.join(ctx.contents, p) for p in ('arm9/arm9.bin', 'arm9.bin')
                                          if os.path.exists(os.path.join(ctx.contents, p))), None)
        self.arm9_new = open(arm9_new, 'rb').read() if arm9_new else self.arm9_old

    def png_rel(self, k):
        s, form = self.icons[k]
        return f'res/pokemon/{s}/' + (f'forms/{form}/' if form else '') + 'icon.png'

    def palette_slot(self, k):
        """(data.json, key path) holding icon k's palette, or None."""
        s, form = self.icons[k]
        rel = f'res/pokemon/{s}/data.json'
        value = self.ctx.json(rel).get('icon_palette')
        if isinstance(value, list):
            for n, (name, _) in enumerate(value):
                if name == (form or 'base'):
                    return rel, ('icon_palette', n, 1)
            return None
        if form is None:
            return rel, ('icon_palette',)
        form_rel = f'res/pokemon/{s}/forms/{form}/data.json'
        if os.path.exists(os.path.join(REPO, form_rel)) and 'icon_palette' in self.ctx.json(form_rel):
            return form_rel, ('icon_palette',)
        return None

    def palette(self, arm9, k):
        return arm9[self.table + k] if self.table is not None else None

    def handled_arm9(self):
        return range(self.table, self.table + len(self.icons)) if self.table is not None else range(0)

    def nitrogfx(self, *args):
        r = subprocess.run([os.path.join(self.ctx.clone, 'build', 'tools', 'nitrogfx', 'nitrogfx'), *args], capture_output=True, text=True)
        if r.returncode:
            raise ValueError((r.stderr or r.stdout).strip()[:300])

    def to_png(self, ncgr, palette):
        """(PNG bytes, re-encoded tile bytes) for an icon NCGR, drawn with shared palette `palette`."""
        with tempfile.TemporaryDirectory() as tmp:
            pals, src, png, back = (os.path.join(tmp, n) for n in ('pals.NCLR', 'icon.NCGR', 'icon.png', 'back.NCGR'))
            open(pals, 'wb').write(self.ctx.old('monIcons', 0)); open(src, 'wb').write(ncgr)
            self.nitrogfx(src, png, '-palette', pals, '-width', '4', '-palindex', str(palette + 1))
            self.nitrogfx(png, back, '-clobbersize', '-version101')
            return open(png, 'rb').read(), open(back, 'rb').read()[0x30:]

    @staticmethod
    def same_image(png_a, png_b):
        from PIL import Image
        import io
        a, b = Image.open(io.BytesIO(png_a)), Image.open(io.BytesIO(png_b))
        return a.size == b.size and list(a.getdata()) == list(b.getdata()) and (a.getpalette() or [])[:48] == (b.getpalette() or [])[:48]

    def writeback(self):
        ctx = self.ctx
        members = ctx.changed('monIcons')
        for m in members:
            if m < self.SHARED or m - self.SHARED >= len(self.icons):
                ctx.not_written.append(f'monIcons member {m}: only species and form icons can be written back')
        pixels = {m - self.SHARED for m in members if self.SHARED <= m < self.SHARED + len(self.icons)}
        palettes = {k for k in range(len(self.icons)) if self.table is not None and self.palette(self.arm9_new, k) != self.palette(self.arm9_old, k)}
        for k in sorted(pixels | palettes):
            rel, pal = self.png_rel(k), self.palette(self.arm9_new, k)
            try:
                if pal is None or pal > 2:
                    raise ValueError(f'icon palette {pal} is not one of the three shared palettes')
                if k in palettes:
                    slot = self.palette_slot(k)
                    if slot is None:
                        raise LookupError('its palette has no source field')
                    data = ctx.json(slot[0])
                    for key in slot[1][:-1]:
                        data = data[key]
                    data[slot[1][-1]] = pal
                ncgr = ctx.new('monIcons', k + self.SHARED)
                png, tiles = self.to_png(ncgr, pal)
                if tiles != ncgr[0x30:0x30 + len(tiles)]:
                    raise ValueError('the icon doesn\'t survive conversion to PNG and back')
                path = os.path.join(REPO, rel)
                if not (os.path.exists(path) and self.same_image(open(path, 'rb').read(), png)):
                    if not ctx.dry_run:
                        open(path, 'wb').write(png)
                    ctx.written.append(rel)
            except LookupError as e:
                ctx.not_written.append(f'{rel}: {e}')
            except ValueError as e:
                ctx.errors.append(f'{rel}: {e}')

    def self_test(self):
        bad = 0
        if self.table is None:
            print('Icons: sPokemonIconPaletteIndex not found in the build map'); return 1
        for k in range(len(self.icons)):
            rel, pal = self.png_rel(k), self.palette(self.arm9_old, k)
            problems = []
            slot = self.palette_slot(k)
            if slot:
                data = self.ctx.json(slot[0])
                for key in slot[1]:
                    data = data[key]
                if data != pal:
                    problems.append(f'icon_palette {data} != {pal} in the build')
            png, tiles = self.to_png(self.ctx.old('monIcons', k + self.SHARED), pal)
            if not self.same_image(open(os.path.join(REPO, rel), 'rb').read(), png):
                problems.append('icon.png differs from the build\'s icon')
            if problems:
                bad += 1
                if bad <= 5:
                    print(f'  {rel}: ' + '; '.join(problems))
        print(f'Icons: {bad} of {len(self.icons)} icon(s) disagree with the build')
        return bad

# --- field scripts: res/field/scripts/<file>.s, patched by dspre_scripts.py -------------------------------------------

class Scripts:
    def __init__(self, ctx):
        self.ctx = ctx
        self.order = lines('res/field/scripts/scripts.order')
        from dspre_scripts import ScriptPatcher, Unsupported
        self.patcher, self.Unsupported = ScriptPatcher(ctx.clone), Unsupported

    def source(self, rel):
        """The file as the build saw it (the clone's copy), after checking this tree hasn't changed it since."""
        if os.path.basename(rel).startswith('scripts_init_'):
            raise self.Unsupported('level scripts (scripts_init_*) aren\'t written back; edit them in source')
        here = open(os.path.join(REPO, rel), encoding='utf-8', newline='').read()
        built = open(os.path.join(self.ctx.clone, rel), encoding='utf-8', newline='').read()
        if here.replace('\r\n', '\n') != built.replace('\r\n', '\n'):
            raise self.Unsupported('the file changed after the build DSPRE opened')
        return here

    def writeback(self):
        ctx = self.ctx
        for i in ctx.changed('scripts'):
            if i >= len(self.order):
                ctx.not_written.append(f'script file {i}: new script files can only be added in source'); continue
            rel = f'res/field/scripts/{self.order[i]}.s'
            try:
                here = self.source(rel)
                patched = self.patcher.patch(here.replace('\r\n', '\n'), ctx.old('scripts', i), ctx.new('scripts', i))
            except self.Unsupported as e:
                ctx.not_written.append(f'{rel}: {e}'); continue
            except Exception as e:   # DSPRE wrote something the disassembler can't read
                ctx.not_written.append(f'{rel}: {type(e).__name__}: {e}'); continue
            if '\r\n' in here:
                patched = patched.replace('\n', '\r\n')
            if patched != here:
                if not ctx.dry_run:
                    with open(os.path.join(REPO, rel), 'w', encoding='utf-8', newline='') as f:
                        f.write(patched)
                ctx.written.append(rel)

    def self_test(self):
        bad, unsupported, level = 0, [], 0
        for i, name in enumerate(self.order):
            rel = f'res/field/scripts/{name}.s'
            if name.startswith('scripts_init_'):
                level += 1; continue
            try:
                text = self.source(rel).replace('\r\n', '\n')
                if self.patcher.patch(text, self.ctx.old('scripts', i), self.ctx.old('scripts', i)) != text:
                    raise RuntimeError('an unchanged script was rewritten')
            except self.Unsupported as e:
                unsupported.append(f'{name} ({e})')
            except Exception as e:
                if 'no primitive' in str(e):   # a command whose macro scrdis can't express (conditional fields)
                    unsupported.append(f'{name} ({str(e).split(" at ")[0]})'); continue
                bad += 1
                if bad <= 8:
                    print(f'  {rel}: {type(e).__name__}: {str(e)[:150]}')
        print(f'Scripts: {bad} file(s) disagree with the build; edit in source only: {level} level scripts and',
              f'{len(unsupported)} others', *('    ' + u for u in unsupported), sep='\n' if unsupported else ' ')
        return bad

# ---------------------------------------------------------------------------------------------------------------------

KINDS = [Trainers, Encounters, Species, Items]
HANDLED_DIRS = {d for k in KINDS for d in k.dirs} | {'textArchives', 'scripts', 'monIcons'}

def code_changes(ctx, baseline, handled_arm9=range(0)):
    """ARM9/overlay edits (spawn point, fly table, item table...) live in code tables this tool doesn't write.
    handled_arm9: ARM9 offsets another writer already took care of (the icon palette table)."""
    out = []
    _, (_, arm9), overlays, _ = load_rom(baseline)
    path = next((p for p in ('arm9/arm9.bin', 'arm9.bin') if os.path.exists(os.path.join(ctx.contents, p))), None)
    if path:
        # ds-rom projects keep ITCM/DTCM out of arm9.bin, so only the part DSPRE has is compared
        mine = open(os.path.join(ctx.contents, path), 'rb').read()
        if any(a != b and i not in handled_arm9 for i, (a, b) in enumerate(zip(arm9, mine))):
            out.append('ARM9 (tables such as the spawn point, fly destinations, item data index, TM list)')
    for i, (_, _, data) in enumerate(overlays):
        for p in (f'arm9_overlays/ov{i:03}.bin', f'overlay/overlay_{i:04}.bin'):
            path = os.path.join(ctx.contents, p)
            if os.path.exists(path):
                edited = open(path, 'rb').read()
                if edited != data and ndspy.codeCompression.decompress(edited) != data:
                    out.append(f'overlay {i}' + (' (egg moves, VS Seeker, overworld tables)' if i == 5 else ''))
                break
    return out

def report_error(args, message):
    if args.report:
        with open(to_wsl(args.report), 'w') as f:
            json.dump({'written': [], 'notWritten': [], 'errors': [message]}, f, indent=2)
    sys.exit(message)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('contents', nargs='?')
    ap.add_argument('--baseline', default=os.path.join(REPO, 'build', 'dspre', 'sourplatinum.baseline.nds'))
    ap.add_argument('--clone', default='~/SourPlatinum', help='WSL build clone with build/generated (default ~/SourPlatinum)')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--report', help='also write the result as JSON (for DSPRE)')
    ap.add_argument('--self-test', action='store_true', help='check every decoder against the baseline build and exit')
    args = ap.parse_args()
    baseline, clone = to_wsl(args.baseline), os.path.expanduser(args.clone)

    if args.self_test:
        ctx = Ctx(None, baseline, clone, dry_run=True)
        bad = sum(kind(ctx).self_test() for kind in KINDS) + Text(ctx).self_test() + Icons(ctx).self_test() + Scripts(ctx).self_test()
        sys.exit(1 if bad else 0)

    if not args.contents:
        ap.error('CONTENTS_DIR is required unless --self-test is given')
    contents = to_wsl(args.contents)
    if not os.path.isdir(os.path.join(contents, 'unpacked')):
        report_error(args, f'{contents} is not a DSPRE contents folder')
    stamp = os.path.join(contents, 'dspre_repo_baseline.sha1')   # written by DSPRE when it opened the repo build
    if os.path.exists(stamp):
        if hashlib.sha1(open(baseline, 'rb').read()).hexdigest() != open(stamp).read().strip():
            report_error(args, f'{baseline} is from a later build than the one DSPRE opened, so DSPRE\'s edits can\'t be '
                               'told apart from the rebuild. Write back from DSPRE before building outside it.')
    ctx = Ctx(contents, baseline, clone, args.dry_run)

    for kind in KINDS:
        kind(ctx).writeback()
    Text(ctx).writeback()
    icons = Icons(ctx)
    icons.writeback()
    ctx.flush()
    if ctx.changed('scripts'):
        Scripts(ctx).writeback()
    for dirname in sorted(NARCS):
        if dirname not in HANDLED_DIRS:
            members = ctx.changed(dirname)
            if members:
                ctx.not_written.append(f'{dirname} ({NARCS[dirname]}) members {members[:20]}{" ..." if len(members) > 20 else ""}')
    ctx.not_written += code_changes(ctx, baseline, icons.handled_arm9())

    verb = 'would write' if args.dry_run else 'wrote'
    print(f'{verb} {len(ctx.written)} file(s)', *('  ' + w for w in ctx.written), sep='\n')
    if ctx.not_written:
        print('NOT written back (lost on the next build):', *('  ' + w for w in ctx.not_written), sep='\n')
    if ctx.errors:
        print('errors:', *('  ' + e for e in ctx.errors), sep='\n')
    if args.report:
        with open(to_wsl(args.report), 'w') as f:
            json.dump({'written': ctx.written, 'notWritten': ctx.not_written, 'errors': ctx.errors}, f, indent=2)
    sys.exit(1 if ctx.errors else 0)

if __name__ == '__main__':
    main()
