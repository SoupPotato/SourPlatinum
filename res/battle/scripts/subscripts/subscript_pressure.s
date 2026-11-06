#include "macros/btlcmd.inc"


_000:
    // Sour Platinum: the banner names the ability, so its message is the plain one. Without the banner, the ability is named.
    CheckAbilityBannerAvailable _PlaintingItsAbility
    // {0} is exerting its {1}!
    PrintMessage BattleStrings_Text_PokemonIsExertingItsAbility_Ally, TAG_NICKNAME_ABILITY, BTLSCR_MSG_TEMP, BTLSCR_MSG_BATTLER_TEMP
    GoTo _PlaintingItsAbilityDone

_PlaintingItsAbility:
    // {0} is exerting its pressure!
    PrintMessage BattleStrings_Text_PokemonIsExertingItsPressure_Ally, TAG_NICKNAME_ABILITY, BTLSCR_MSG_TEMP, BTLSCR_MSG_BATTLER_TEMP

_PlaintingItsAbilityDone:
    Wait 
    WaitButtonABTime 30
    End 
