#include "macros/btlcmd.inc"


_000:
    // Sour Platinum: the banner names the ability, so its message is the plain one. Without the banner, the ability is named.
    CheckAbilityBannerAvailable _PlainyMadeItShudder
    // {1}’s {0} made it shudder!
    PrintMessage BattleStrings_Text_PokemonsAbilityMadeItShudder_Ally, TAG_ABILITY_NICKNAME, BTLSCR_MSG_BATTLER_TEMP, BTLSCR_MSG_TEMP
    GoTo _PlainyMadeItShudderDone

_PlainyMadeItShudder:
    // {1} shuddered!
    PrintMessage BattleStrings_Text_PokemonShuddered_Ally, TAG_ABILITY_NICKNAME, BTLSCR_MSG_BATTLER_TEMP, BTLSCR_MSG_TEMP

_PlainyMadeItShudderDone:
    Wait 
    WaitButtonABTime 30
    End 
