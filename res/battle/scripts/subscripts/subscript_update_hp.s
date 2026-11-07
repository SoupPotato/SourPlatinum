#include "macros/btlcmd.inc"


_000:
    CompareVarToValue OPCODE_FLAG_SET, BTLVAR_BATTLE_CTX_STATUS, SYSCTL_SKIP_SPRITE_BLINK, _016
    PlayMoveHitSound BTLSCR_MSG_TEMP
    FlickerMon BTLSCR_MSG_TEMP
    // Sour Platinum: the HP bar moves while the Pokemon flashes, and the Wait after it lasts until both are done. Only
    // a type resist berry goes between them, since it halves the damage the bar shows.
    CompareVarToValue OPCODE_EQU, BTLVAR_WAITING_BATTLERS, 0, _016
    GetItemHoldEffect BTLSCR_MSG_TEMP, BTLVAR_SCRIPT_TEMP
    CompareVarToValue OPCODE_LTE, BTLVAR_SCRIPT_TEMP, 18, _016
    CompareVarToValue OPCODE_GT, BTLVAR_SCRIPT_TEMP, 35, _016
    Wait 
    Call BATTLE_SUBSCRIPT_TYPE_RESIST_BERRY

_016:
    UpdateVar OPCODE_FLAG_OFF, BTLVAR_BATTLE_CTX_STATUS, SYSCTL_SKIP_SPRITE_BLINK
    UpdateHealthBar BTLSCR_MSG_TEMP
    Wait 
    UpdateHealthBarValue BTLSCR_MSG_TEMP
    TryFaintMon BTLSCR_MSG_TEMP
    CompareVarToValue OPCODE_GT, BTLVAR_HP_CALC_TEMP, 0, _036
    UpdateVarFromVar OPCODE_SET, BTLVAR_MSG_BATTLER_TEMP_ASSURANCE_DAMAGE_MASK, BTLVAR_HP_CALC_TEMP

_036:
    End 
