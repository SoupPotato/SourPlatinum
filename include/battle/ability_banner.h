#ifndef POKEPLATINUM_BATTLE_ABILITY_BANNER_H
#define POKEPLATINUM_BATTLE_ABILITY_BANNER_H

#include "struct_decls/battle_system.h"

#include "battle/battle_context.h"

// Sour Platinum: Gen 5 style ability banner. When a battle message that names an ability is printed, a plate with the
// name of the Pokemon and its ability slides in from the side of the screen that the Pokemon is on, flashes, and
// disappears when the message is done.
//
// Abilities whose effect comes before their message (Intimidate, Static...) use the ShowAbilityBanner and
// ShowBufferedAbilityBanner battle script commands first. They print BattleStrings_Text_AbilityBanner, an empty message
// with the Pokemon and its ability that only brings in the banner. The banner then stays for the message of the ability.

#define ABILITY_BANNER_NO_MESSAGE 0xFF

// Shows the banner for a message if it is one that names the ability of a Pokemon.
// msgIdx: The text printer that prints the message; the banner stays until it is done. ABILITY_BANNER_NO_MESSAGE for a
// message that only brings in the banner: the banner then stays for the next message about the same ability.
void AbilityBanner_TryShow(BattleSystem *battleSys, const BattleMessage *battleMsg, u8 msgIdx);

// TRUE for BattleStrings_Text_AbilityBanner, which is not printed. Checked before printing, which changes the message ID.
BOOL AbilityBanner_IsBannerOnlyMessage(const BattleMessage *battleMsg);

// TRUE if the message names the ability of a Pokemon (and would show the banner)
BOOL AbilityBanner_MessageNamesAbility(const BattleMessage *battleMsg);

// TRUE while the banner slides in, flashes and plays its sounds. Battle messages don't report that they are done until
// this is over, so the effect of the ability comes after it, like in Black and White.
BOOL AbilityBanner_IsIntroPlaying(void);

#endif // POKEPLATINUM_BATTLE_ABILITY_BANNER_H
