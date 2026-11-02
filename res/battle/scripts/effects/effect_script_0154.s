#include "macros/btlcmd.inc"


_000:
    // Sour Platinum: Generation 5 Beat Up. BeatUp counts the hits and sets the power of each one, and CalcDamage works out
    // the damage like any other Dark move (it used to be typeless, which is why immunities were ignored). It ends with
    // "Hit X time(s)!" like other multi-hit moves instead of announcing each party member's attack.
    UpdateVar OPCODE_SET, BTLVAR_AFTER_MOVE_MESSAGE_TYPE, AFTER_MOVE_MESSAGE_MULTI_HIT
    CalcCrit 
    BeatUp 
    CalcDamage 
    End 
