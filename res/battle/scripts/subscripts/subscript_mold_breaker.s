#include "macros/btlcmd.inc"


_000:
    CheckAbilityBannerAvailable _PlainemonWasAbility
    // {0} has {1}!
    PrintMessage BattleStrings_Text_PokemonWasAbility_Ally, TAG_NICKNAME_ABILITY, BTLSCR_MSG_TEMP, BTLSCR_MSG_BATTLER_TEMP
    GoTo _PlainemonWasAbilityDone

_PlainemonWasAbility:
    PrintMessage BattleStrings_Text_PokemonBreaksTheMold_Ally, TAG_NICKNAME_ABILITY, BTLSCR_MSG_TEMP, BTLSCR_MSG_BATTLER_TEMP

_PlainemonWasAbilityDone:
    Wait 
    WaitButtonABTime 30
    End 
