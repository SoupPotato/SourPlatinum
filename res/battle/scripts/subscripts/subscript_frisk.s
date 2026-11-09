#include "macros/btlcmd.inc"


_000:
    WaitButtonABTime 15
    ShowAbilityBanner BTLSCR_MSG_BATTLER_TEMP
    Wait 
    // {0} frisked its foe and found one {1}!
    PrintMessage BattleStrings_Text_PokemonFriskedItsFoeAndFoundOneItem_Ally, TAG_NICKNAME_ITEM, BTLSCR_MSG_TEMP, BTLSCR_MSG_TEMP
    Wait 
    WaitButtonABTime 30
    End 
