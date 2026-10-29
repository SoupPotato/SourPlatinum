#include "macros/btlcmd.inc"


_000:
    RapidSpin 
    // Sour Platinum: when it hits, Rapid Spin also raises the user's Speed by one stage
    UpdateVarFromVar OPCODE_SET, BTLVAR_SIDE_EFFECT_MON, BTLVAR_ATTACKER
    UpdateVar OPCODE_SET, BTLVAR_SIDE_EFFECT_PARAM, MOVE_SUBSCRIPT_PTR_SPEED_UP_1_STAGE
    Call BATTLE_SUBSCRIPT_UPDATE_STAT_STAGE
    End 
