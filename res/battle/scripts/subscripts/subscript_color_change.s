#include "macros/btlcmd.inc"


_000:
    // Sour Platinum: the banner names the ability, so its message is the plain one. Without the banner, the ability is named.
    CheckAbilityBannerAvailable _PlainlityMadeItType
    // {0}’s {1} made it the {2} type!
    PrintMessage BattleStrings_Text_PokemonsAbilityMadeItType_Ally, TAG_NICKNAME_ABILITY_TYPE, BTLSCR_DEFENDER, BTLSCR_DEFENDER, BTLSCR_MSG_TEMP
    GoTo _PlainlityMadeItTypeDone

_PlainlityMadeItType:
    ShowAbilityBanner BTLSCR_DEFENDER
    Wait 
    // {0} transformed into the {1} type!
    PrintMessage BattleStrings_Text_PokemonTransformedIntoType_Ally, TAG_NICKNAME_TYPE, BTLSCR_DEFENDER, BTLSCR_MSG_TEMP

_PlainlityMadeItTypeDone:
    Wait 
    WaitButtonABTime 30
    UpdateMonDataFromVar OPCODE_SET, BTLSCR_DEFENDER, BATTLEMON_TYPE_1, BTLVAR_MSG_TEMP
    UpdateMonDataFromVar OPCODE_SET, BTLSCR_DEFENDER, BATTLEMON_TYPE_2, BTLVAR_MSG_TEMP
    End 
