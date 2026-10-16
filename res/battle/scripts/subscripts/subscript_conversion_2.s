#include "macros/btlcmd.inc"


_000:
    TryConversion2 _012
    // Sour Platinum: Conversion 2 targets the user, so its animation took the type from the user instead of from the
    // battler whose move is copied (set by TryConversion2)
    PrintAttackMessage 
    Wait 
    PlayMoveAnimationOnMons BTLSCR_ATTACKER, BTLSCR_ATTACKER, BTLSCR_MSG_BATTLER_TEMP
    Wait 
    // {0} transformed into the {1} type!
    PrintMessage BattleStrings_Text_PokemonTransformedIntoType_Ally, TAG_NICKNAME_TYPE, BTLSCR_ATTACKER, BTLSCR_MSG_TEMP
    Wait 
    WaitButtonABTime 30
    End 

_012:
    UpdateVar OPCODE_FLAG_ON, BTLVAR_MOVE_STATUS_FLAGS, MOVE_STATUS_FAILED
    End 
