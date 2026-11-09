#include "macros/btlcmd.inc"


_000:
    CheckAbilityBannerAvailable _PlainlertedItToMove
    // {0}’s {1} alerted it to {2}!
    PrintMessage BattleStrings_Text_PokemonsAbilityAlertedItToMove_Ally, TAG_NICKNAME_ABILITY_MOVE, BTLSCR_MSG_TEMP, BTLSCR_MSG_BATTLER_TEMP, BTLSCR_MSG_TEMP
    GoTo _PlainlertedItToMoveDone

_PlainlertedItToMove:
    ShowAbilityBanner BTLSCR_MSG_BATTLER_TEMP
    Wait 
    PrintMessage BattleStrings_Text_ItWasAlertedToPokemonsMove_Ally, TAG_NICKNAME_MOVE, BTLSCR_MSG_ATTACKER, BTLSCR_MSG_TEMP

_PlainlertedItToMoveDone:
    Wait 
    WaitButtonABTime 30
    End 
