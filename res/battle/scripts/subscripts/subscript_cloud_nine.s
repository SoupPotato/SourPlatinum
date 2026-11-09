#include "macros/btlcmd.inc"


_000:
    ShowAbilityBanner BTLSCR_MSG_BATTLER_TEMP
    Wait 
    PrintMessage BattleStrings_Text_TheEffectsOfWeatherDisappeared, TAG_NONE
    Wait 
    WaitButtonABTime 30
    End 
