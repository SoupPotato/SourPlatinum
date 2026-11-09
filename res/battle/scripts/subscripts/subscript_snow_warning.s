#include "macros/btlcmd.inc"


_000:
    ShowAbilityBanner BTLSCR_MSG_BATTLER_TEMP
    Wait 
    PlayBattleAnimation BTLSCR_PLAYER, BATTLE_ANIMATION_WEATHER_HAIL
    Wait 
    CheckAbilityBannerAvailable _PrintPlainMessage
    // {0}’s {1} whipped up a hailstorm!
    PrintMessage BattleStrings_Text_PokemonsAbilityWhippedUpAHailstorm_Ally, TAG_NICKNAME_ABILITY, BTLSCR_MSG_TEMP, BTLSCR_MSG_BATTLER_TEMP
    GoTo _MessagePrinted

_PrintPlainMessage:
    // It started to hail!
    PrintMessage BattleStrings_Text_ItStartedToHail, TAG_NONE

_MessagePrinted:
    Wait 
    WaitButtonABTime 30
    UpdateVar OPCODE_FLAG_OFF, BTLVAR_FIELD_CONDITIONS, FIELD_CONDITION_WEATHER
    UpdateVar OPCODE_FLAG_ON, BTLVAR_FIELD_CONDITIONS, FIELD_CONDITION_HAILING_PERM
    End 
