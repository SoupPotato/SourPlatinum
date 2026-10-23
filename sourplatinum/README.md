# Sour Platinum

Sour Platinum is a Pokémon Platinum (US, Rev 1) hack by SourApple. This branch of
[pret/pokeplatinum](https://github.com/pret/pokeplatinum) rebuilds it from source. The edits
from the original ROM hack are converted back into the decomp's own formats (JSON data, text
banks, field scripts, PNG graphics and C code), so they can be read, diffed and changed like
the rest of the codebase.

Build it the same way as pokeplatinum (see `INSTALL.md`), then run `make`. The checksum
against retail Platinum is turned off by default. The output is `build/pokeplatinum.us.nds`.

## What the hack changes

| Area | Where it lives |
| --- | --- |
| Base stats, types, abilities, EV yields, catch rates, TM compatibility, evolutions and level-up learnsets for most species | `res/pokemon/*/data.json` |
| 83 moves rebalanced (power, accuracy, PP, type, effects) | `res/moves/*/data.json` |
| Trade evolutions replaced: King's Rock, Metal Coat, Dragon Scale, Up-Grade, Protector, Electirizer, Magmarizer, Dubious Disc, Reaper Cloth and the DeepSea items can be used from the bag like evolution stones | `res/items/data/*.json`, `res/pokemon/*/data.json` |
| New **Linking Cord** item (it replaces the Loot Sack, `ITEM_LINKING_CORD`), with its own icon, sold at the Veilstone Game Corner for 3000 coins in place of TM27 | `res/items/data/linking_cord.json`, `src/scrcmd_game_corner_prize.c`, `res/field/scripts/scripts_veilstone_city_prize_exchange.s` |
| Reusable TMs: teaching a TM no longer consumes it, and the bag hides TM quantities | `src/applications/party_menu/callbacks.c`, `src/applications/bag/windows.c` |
| Hidden Power always has 60 base power; its type still depends on IVs. The trainer AI's damage estimate uses the same fixed power | `src/battle/battle_script.c`, `src/battle/trainer_ai/trainer_ai.c`, `res/moves/hidden_power/data.json` |
| Fury Cutter starts at 20 base power instead of 40 and stops doubling at 160 (20, 40, 80, 160) | `res/moves/fury_cutter/data.json`, `src/battle/battle_script.c` (`BtlCmd_CalcFuryCutterPower`) |
| Battles run at 60 fps without changing their pace (details below) | `include/sourplatinum_config.h`, `src/main.c`, `src/battle/battle_main.c` and others |
| HP and EXP bars move at a constant speed no matter how much HP or EXP is involved (like Gen 5) | `src/battle/healthbox.c`, `src/battle/battle_display.c` |
| Honey trees: each honey tree route has a tree you can slather. It starts an immediate level 12 battle with Combee, Wurmple, Burmy, Cherubi, Aipom, Heracross or Munchlax | `res/field/events/*.json`, `res/field/scripts/*.s` (`*_HoneyTree`), `res/text/*.json` |
| Wild encounter changes on Eterna Forest, the Lost Tower and Routes 206, 214, 218, 221 and 222 | `res/field/encounters/*.json` |
| Text decapitalized throughout (BULBASAUR → Bulbasaur, NORMAL → Normal, OPTIONS → Options, …), plus dialogue and description edits | `res/text/*.json`, species/item/move/trainer JSON |
| New-style party and box icons with updated icon palettes | `res/pokemon/**/icon.png`, `icon_palette` in `data.json` |
| Battle sprite and palette edits (including alternate forms and the Substitute doll), sprite Y offsets and shadows | `res/pokemon/**/*.png`, `*.pal`, `sprite_data.json` |
| Maylene's encounter mugshot and the Shadow Force particle effect | `res/trainers/classes/leader_maylene/mugshot.png`, `res/graphics/battle/particles/shadow_force.spa` |

## How this build differs from the original ROM

The conversion was checked against the original ROM file by file. Every data archive matches,
with these intended exceptions:

- **Code** is now C, so arm9, the battle overlay and the bag overlay are no longer byte-identical.
  They behave the same. The compiled icon-palette and Game Corner prize tables match the
  original exactly.
- **Field scripts** are laid out differently. The original editor inlined a few branches and
  moved data around. All script logic was compared instruction by instruction and matches.
- **Pokédex height/weight text**: the original editing tool stripped the alignment padding
  from 149 entries, which misaligns them in the Pokédex. This build keeps the padding.
- **"a/an + species name" text bank**: the original tool left these uppercase (`a BULBASAUR`).
  They now follow the decapitalized names.
- **Item names with articles**: the original tool wrote broken text control codes into this bank.
  This build regenerates it correctly.
- **Pokédex area maps** are regenerated from the new wild encounters. The original ROM still
  showed vanilla locations.
- **Four extra icons** sat at the end of the icon archive and the game never loads them. They
  are kept in `sourplatinum/unused_icons/` and are not built.

## 60 fps battles

Single-player battles run the main loop once per VBlank (60 ticks per second) instead of once
per two VBlanks. Link battles stay at the original 30 Hz. Set `SP_BATTLE_60FPS` to `0` in
`include/sourplatinum_config.h` to turn it all off.

- Code written for the original 30 Hz loop (battle logic, scripts, input, sound, most move
  animation tasks) runs on every other tick, so the game keeps its original pace. The text printer
  already ran twice per original frame, so it simply runs once per tick.
- Particles are updated at 60 Hz (`lib/spl`, `SPL_SetDefaultTimeScale`). Lifetimes and emission
  intervals are doubled, rotation is split between the two updates, and velocity, damping,
  gravity and the other behaviors still run once per original frame, so particles follow exactly
  the same paths as before; their movement for each frame is simply covered in two steps. The lerp helpers in
  `src/battle_anim/battle_anim_helpers.c` scale themselves, which lets individual tasks opt in to
  running on every tick (`SysTask_SetTickDiv`, `BattleAnimSystem_StartNativeAnimTask`). The
  projectile and beam emitter movement and the battler lunge/slide moves do this.
- Everything else that moves (Pokémon sprites, 2D sprites, background scroll offsets) is drawn
  halfway between its last shown and its current position on the original-rate tick and at its real
  position on the next tick. Sprites drawn by other tasks are redrawn on the in-between ticks
  (`SpriteList_ReplayDrawLog`, `PokemonSpriteManager_ReplayDrawLog`), and the 3D buffer swap runs
  on every tick.
- HP and EXP bars use `SP_BAR_HP_PIXELS_PER_SECOND` and `SP_BAR_EXP_PIXELS_PER_SECOND`, with
  `SP_PACE_BARS_PERCENT` as a speed multiplier. `SP_PACE_TEXT_PERCENT` does the same for text.
- Fixed a bug in the decomp that this build exposed: `PokemonSpriteManager_New` left `hideShadows`
  uninitialised, which could hide every Pokémon shadow.
- `SP_DEBUG_*` switches in the same header turn individual parts off when tracking down visual
  problems.

## 60 fps menus

`SP_MENUS_60FPS` (on by default) runs converted menu screens at 60 ticks per second with their original pace, using
`MenuFps60_Begin` / `MenuFps60_End` in `src/system.c`. It stays off during link and wireless sessions. Converted so
far: the Party screen and the Pokémon Summary screen (whose 3D Pokémon sprite and Condition graph are redrawn on the
in-between ticks). The Party screen's switch slide runs natively at one tile per tick, twice as fast as the original.

## Hidden Moves Pokétch app

A new Pokétch app (`POKETCH_APPID_FIELDMOVES`, in `src/applications/poketch/field_moves/`, which uses the old unused
fourth app overlay) that uses the HM moves without a Pokémon that knows them. It shows Rock Smash, Cut, Strength, Fly,
Defog, Surf, Rock Climb and Waterfall as framed buttons, but only for the HMs the player has in the Bag. Touching a
button runs the same checks as the party menu (`StartMenu_StartPoketchFieldMove` in `src/start_menu.c`): the badge,
the location and so on, and if it can't be used the field shows the same message as the party menu. Fly opens the Town
Map and returns to the overworld if cancelled. The first Pokémon in the party that isn't an Egg is shown as the user.
The hiker in Oreburgh Gate 1F (`res/field/scripts/scripts_oreburgh_gate_1f.s`) gives the app together with the Rock
Smash HM, or when you talk to him later if you don't have it yet. `SP_DEBUG_REGISTER_FIELD_MOVES_APP` registers the
app from the start for testing.

Planned follow-ups for the app are in `sourplatinum/TODO.md`.

## Move animation speed commands

Move animation scripts (`res/moves/*/anim.s`) have three commands for adjusting how fast an
animation plays. They work in both 30 and 60 fps mode.

- `SetAnimSpeed percent` speeds up (above 100) or slows down (below 100) what follows in the
  script: particles, `Delay`, looped and delayed sounds, and helper tasks. Set it back to `100` to
  restore normal speed. It is reset at the start and end of every move.
- `SetParticleSpeed particleSystem, percent` changes the speed of one particle system only, so one
  set of particles (the draining orbs) can play faster while another (the healing sparkles) keeps
  its pace. The speed of a system is reset when it is created.
- `StopEmitters particleSystem` stops a system's emitters from emitting new particles. The
  particles already out finish their lives, so the effect ends sooner without moving faster
  (used by Absorb and Leech Seed).
- `SetSmoothChildren enabled` makes child particles that are created every frame (trails, or rings made of child
  copies, like Supersonic's) appear on every 60 Hz update, so they move smoothly. It only applies to the emitters created
  after it and is reset when the animation starts and ends. It makes the trail denser.

Moves tuned with these so far: Absorb, Leech Seed drain, Mega Drain, Quick Attack, Agility, Dream Eater,
Drain Punch, Leech Life, Vital Throw, Foresight, Double Slap and Poison Sting. `Func_QuickAttack` takes an
optional number of spins (Agility uses 2).

Particle children that live one original frame (the white centre of the drain orbs) are emitted
on every update and live one update in 60 fps mode, so they stay exactly under their parent.

## Wild Pokemon modifier (debug builds)

Set `SP_DEBUG_WILD_MODIFIER` to `1` in `include/sourplatinum_config.h` (it is `0` in the normal ROM). Type a number
into the Pokétch calculator and press L (species, National Dex number), R (level, 1-100) or Select (nature,
0-24). Every wild Pokémon created afterwards uses the values. 0 (or 25+ for the nature) turns a setting off, and
all settings reset when you load a different map.

## Editing with DSPRE

Retail DSPRE reads its tables from fixed Platinum offsets, which this build moves. A DSPRE fork (branch
`sourplatinum-offsets`) reads replacement offsets from a `<rom name>.dspre_offsets.json` next to the ROM, and can
open this repository directly (menu **Repository**):

- **Open SourPlatinum Repository...** runs `sourplatinum/tools/dspre_build.py` through WSL: it copies changed files
  from this tree into the WSL build clone (`~/SourPlatinum`), runs `make`, and publishes `build/dspre/sourplatinum.nds`
  with its offsets file and a baseline copy. DSPRE then opens that ROM.
- **Write Back to Repository** runs `sourplatinum/tools/dspre_writeback.py`, which turns the edits DSPRE saved into
  changes to this tree's source files, field by field, so the rest of each file stays as it was.
- **Write Back, Rebuild and Reopen** does both.

What gets written back: trainers, wild encounters (`encounters_*.json`), species stats, TM/HM compatibility, level-up
learnsets and evolutions, item data, text banks (plus species, item, move and trainer names and item/move
descriptions) and field scripts. Changed script blocks are rewritten with the file's own labels and names; new code
gets `<Map>_DSPRE_*` labels at the end of the file. Level scripts (`scripts_init_*`), four scripts using conditional
macros (`scripts_group_connection`, `scripts_mystery_gift_deliveryman`, `scripts_field_moves`,
`scripts_tv_broadcast`) and everything else (maps, events, graphics, ARM9/overlay tables) aren't written back. DSPRE
lists those edits before a rebuild would lose them.

`dspre_writeback.py --self-test` decodes the whole baseline build and checks it against the source; run it after
changing a data format or one of the `tools/dataproc` processors. To make the offsets file by hand (debug and release
builds lay out differently, so the map and ROM must come from the same build):

    python3 sourplatinum/tools/dspre_offsets.py --rom build/pokeplatinum.us.nds -o build/sourplatinum.dspre_offsets.json
