#include "macros/btlcmd.inc"


_000:
    // Sour Platinum: the ability banner comes in before the effect
    ShowAbilityBanner BTLSCR_MSG_BATTLER_TEMP
    Wait 
    PlayBattleAnimation BTLSCR_PLAYER, BATTLE_ANIMATION_WEATHER_SUN
    Wait 
    // Sour Platinum: the banner names the ability, so its message is the plain one. Without the banner, the ability is named.
    CheckAbilityBannerAvailable _PrintPlainMessage
    // {0}’s {1} intensified the sun’s rays!
    PrintMessage BattleStrings_Text_PokemonsAbilityIntensifiedTheSunsRays_Ally, TAG_NICKNAME_ABILITY, BTLSCR_MSG_TEMP, BTLSCR_MSG_BATTLER_TEMP
    GoTo _MessagePrinted

_PrintPlainMessage:
    // The sunlight turned harsh!
    PrintMessage BattleStrings_Text_TheSunlightTurnedHarsh, TAG_NONE

_MessagePrinted:
    Wait 
    WaitButtonABTime 30
    UpdateVar OPCODE_FLAG_OFF, BTLVAR_FIELD_CONDITIONS, FIELD_CONDITION_WEATHER
    UpdateVar OPCODE_FLAG_ON, BTLVAR_FIELD_CONDITIONS, FIELD_CONDITION_SUNNY_PERM
    End 
