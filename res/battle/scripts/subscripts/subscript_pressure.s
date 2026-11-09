#include "macros/btlcmd.inc"


_000:
    CheckAbilityBannerAvailable _PlaintingItsAbility
    // {0} is exerting its {1}!
    PrintMessage BattleStrings_Text_PokemonIsExertingItsAbility_Ally, TAG_NICKNAME_ABILITY, BTLSCR_MSG_TEMP, BTLSCR_MSG_BATTLER_TEMP
    GoTo _PlaintingItsAbilityDone

_PlaintingItsAbility:
    PrintMessage BattleStrings_Text_PokemonIsExertingItsPressure_Ally, TAG_NICKNAME_ABILITY, BTLSCR_MSG_TEMP, BTLSCR_MSG_BATTLER_TEMP

_PlaintingItsAbilityDone:
    Wait 
    WaitButtonABTime 30
    End 
