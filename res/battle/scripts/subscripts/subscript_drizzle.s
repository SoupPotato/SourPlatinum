#include "macros/btlcmd.inc"


_000:
    ShowAbilityBanner BTLSCR_MSG_BATTLER_TEMP
    Wait 
    PlayBattleAnimation BTLSCR_PLAYER, BATTLE_ANIMATION_WEATHER_RAIN
    Wait 
    CheckAbilityBannerAvailable _PrintPlainMessage
    // {0}’s {1} made it rain!
    PrintMessage BattleStrings_Text_PokemonsAbilityMadeItRain_Ally, TAG_NICKNAME_ABILITY, BTLSCR_MSG_TEMP, BTLSCR_MSG_BATTLER_TEMP
    GoTo _MessagePrinted

_PrintPlainMessage:
    // It started to rain!
    PrintMessage BattleStrings_Text_ItStartedToRain, TAG_NONE

_MessagePrinted:
    Wait 
    WaitButtonABTime 30
    UpdateVar OPCODE_FLAG_OFF, BTLVAR_FIELD_CONDITIONS, FIELD_CONDITION_WEATHER
    UpdateVar OPCODE_FLAG_ON, BTLVAR_FIELD_CONDITIONS, FIELD_CONDITION_RAINING_PERM
    End 
