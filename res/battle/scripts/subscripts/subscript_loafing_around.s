#include "macros/btlcmd.inc"


_000:
    // Sour Platinum: like in Black, the ability banner comes in with the message
    ShowAbilityBanner BTLSCR_ATTACKER
    Wait 
    // {0} is loafing around!
    PrintMessage BattleStrings_Text_PokemonIsLoafingAround_Ally, TAG_NICKNAME, BTLSCR_ATTACKER
    Wait 
    WaitButtonABTime 30
    UnlockMoveChoice BTLSCR_ATTACKER
    End 
