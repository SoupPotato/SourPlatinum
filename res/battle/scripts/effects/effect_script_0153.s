#include "macros/btlcmd.inc"


_000:
    // Sour Platinum: Generation 8, in a trainer battle Teleport switches the user out (it fails if there is no other
    // Pokemon that can battle) instead of failing. In a wild battle the user still flees.
    CompareVarToValue OPCODE_FLAG_SET, BTLVAR_BATTLE_TYPE, BATTLE_TYPE_TRAINER, _009
    UpdateVar OPCODE_SET, BTLVAR_SIDE_EFFECT_FLAGS_DIRECT, MOVE_SIDE_EFFECT_ON_HIT|MOVE_SUBSCRIPT_PTR_TELEPORT
    End 

_009:
    UpdateVar OPCODE_SET, BTLVAR_SIDE_EFFECT_FLAGS_DIRECT, MOVE_SIDE_EFFECT_ON_HIT|MOVE_SUBSCRIPT_PTR_BATON_PASS
    End 
