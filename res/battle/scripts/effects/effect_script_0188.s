#include "macros/btlcmd.inc"


_000:
    // Sour Platinum: Generation 5, the power is boosted by 50% if the target holds an item that can be knocked off. The
    // boost also applies if Sticky Hold or a Substitute stops the item from being removed.
    CompareMonDataToValue OPCODE_EQU, BTLSCR_DEFENDER, BATTLEMON_HELD_ITEM, ITEM_NONE, _no_boost
    CompareMonDataToValue OPCODE_EQU, BTLSCR_DEFENDER, BATTLEMON_ABILITY, ABILITY_MULTITYPE, _no_boost
    CompareMonDataToValue OPCODE_EQU, BTLSCR_DEFENDER, BATTLEMON_HELD_ITEM, ITEM_GRISEOUS_ORB, _no_boost
    CompareMonDataToValue OPCODE_NEQ, BTLSCR_DEFENDER, BATTLEMON_QUICK_CLAW, 0, _no_boost
    CompareMonDataToValue OPCODE_NEQ, BTLSCR_DEFENDER, BATTLEMON_CUSTAP_BERRY, 0, _no_boost
    UpdateVar OPCODE_SET, BTLVAR_POWER_MULTI, 15

_no_boost:
    UpdateVar OPCODE_SET, BTLVAR_SIDE_EFFECT_FLAGS_INDIRECT, MOVE_SIDE_EFFECT_ON_HIT|MOVE_SUBSCRIPT_PTR_KNOCK_OFF
    CalcCrit 
    CalcDamage 
    End 
