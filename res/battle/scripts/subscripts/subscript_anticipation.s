#include "macros/btlcmd.inc"


_000:
    CheckAbilityBannerAvailable _PlainyMadeItShudder
    // {1}’s {0} made it shudder!
    PrintMessage BattleStrings_Text_PokemonsAbilityMadeItShudder_Ally, TAG_ABILITY_NICKNAME, BTLSCR_MSG_BATTLER_TEMP, BTLSCR_MSG_TEMP
    GoTo _PlainyMadeItShudderDone

_PlainyMadeItShudder:
    PrintMessage BattleStrings_Text_PokemonShuddered_Ally, TAG_ABILITY_NICKNAME, BTLSCR_MSG_BATTLER_TEMP, BTLSCR_MSG_TEMP

_PlainyMadeItShudderDone:
    Wait 
    WaitButtonABTime 30
    End 
