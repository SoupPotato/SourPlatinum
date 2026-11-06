#include "macros/btlcmd.inc"


_000:
    // Sour Platinum: the banner names the ability, so its message is the plain one. Without the banner, the ability is named.
    CheckAbilityBannerAvailable _PlainseOfItsAbility
    // {0} can’t get it going because of its {1}!
    PrintMessage BattleStrings_Text_PokemonCantGetItGoingBecauseOfItsAbility_Ally, TAG_NICKNAME_ABILITY, BTLSCR_MSG_TEMP, BTLSCR_MSG_BATTLER_TEMP
    GoTo _PlainseOfItsAbilityDone

_PlainseOfItsAbility:
    // {0} can’t get it going!
    PrintMessage BattleStrings_Text_PokemonCantGetItGoing_Ally, TAG_NICKNAME_ABILITY, BTLSCR_MSG_TEMP, BTLSCR_MSG_BATTLER_TEMP

_PlainseOfItsAbilityDone:
    Wait 
    WaitButtonABTime 30
    End 
