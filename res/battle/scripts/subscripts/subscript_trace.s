#include "macros/btlcmd.inc"


_000:
    WaitButtonABTime 15
    // Sour Platinum: like in Black, the banner comes in with the old ability and pixelates into the new one
    ShowAbilityBanner BTLSCR_MSG_BATTLER_TEMP
    Wait 
    UpdateMonDataFromVar OPCODE_GET, BTLSCR_MSG_DEFENDER, BATTLEMON_ABILITY, BTLVAR_CALC_TEMP
    UpdateMonDataFromVar OPCODE_SET, BTLSCR_MSG_TEMP, BATTLEMON_ABILITY, BTLVAR_CALC_TEMP
    ChangeAbilityBanner BTLSCR_MSG_BATTLER_TEMP
    Wait 
    // {0} traced {1}’s {2}!
    PrintMessage BattleStrings_Text_PokemonTracedPokemonsAbility_AllyAlly, TAG_NICKNAME_NICKNAME_ABILITY, BTLSCR_MSG_TEMP, BTLSCR_MSG_DEFENDER, BTLSCR_MSG_DEFENDER
    Wait 
    WaitButtonABTime 30
    End 
