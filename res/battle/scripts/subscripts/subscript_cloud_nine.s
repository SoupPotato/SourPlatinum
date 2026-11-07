#include "macros/btlcmd.inc"


_000:
    // Sour Platinum: like in Black, the ability banner comes in with the message
    ShowAbilityBanner BTLSCR_MSG_BATTLER_TEMP
    Wait 
    // The effects of weather disappeared.
    PrintMessage BattleStrings_Text_TheEffectsOfWeatherDisappeared, TAG_NONE
    Wait 
    WaitButtonABTime 30
    End 
