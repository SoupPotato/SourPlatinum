#include "macros/btlcmd.inc"


_000:
    CompareVarToValue OPCODE_EQU, BTLVAR_CRITICAL_MUL, 1, _049
    // A critical hit!
    PrintMessage BattleStrings_Text_ACriticalHit, TAG_NONE
    Wait 
    WaitButtonABTime 30

_049:
    End 
