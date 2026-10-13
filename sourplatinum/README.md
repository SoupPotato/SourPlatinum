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
| Hidden Power always has 60 base power; its type still depends on IVs | `src/battle/battle_script.c`, `res/moves/hidden_power/data.json` |
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
