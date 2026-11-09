#include "macros/btlcmd.inc"


_000:
    WaitButtonABTime 15
    CompareVarToValue OPCODE_FLAG_NOT, BTLVAR_MOVE_STATUS_FLAGS, MOVE_STATUS_SPLASH, _011
    // But nothing happened!
    PrintMessage BattleStrings_Text_ButNothingHappened, TAG_NONE
    GoTo _095

_011:
    CompareVarToValue OPCODE_FLAG_SET, BTLVAR_MOVE_STATUS_FLAGS, MOVE_STATUS_ENDURED_ITEM, _067
    CompareVarToValue OPCODE_FLAG_NOT, BTLVAR_MOVE_STATUS_FLAGS, MOVE_STATUS_ENDURED, _057
    CompareMonDataToValue OPCODE_EQU, BTLSCR_DEFENDER, BATTLEMON_CUR_HP, 1, _067

_057:
    CompareVarToValue OPCODE_FLAG_NOT, BTLVAR_MOVE_STATUS_FLAGS, MOVE_STATUS_ONE_HIT_KO, _067
    // It’s a one-hit KO!
    PrintMessage BattleStrings_Text_ItsAOneHitKO, TAG_NONE
    GoTo _095

_067:
    CompareVarToValue OPCODE_FLAG_SET, BTLVAR_BATTLE_CTX_STATUS, SYSCTL_IGNORE_TYPE_CHECKS, _098
    CompareVarToValue OPCODE_AND, BTLVAR_MOVE_STATUS_FLAGS, MOVE_STATUS_SUPER_EFFECTIVE|MOVE_STATUS_NOT_VERY_EFFECTIVE, _098
    CompareVarToValue OPCODE_FLAG_NOT, BTLVAR_MOVE_STATUS_FLAGS, MOVE_STATUS_SUPER_EFFECTIVE, _087
    // It’s super effective!
    PrintMessage BattleStrings_Text_ItsSuperEffective, TAG_NONE
    GoTo _095

_087:
    CompareVarToValue OPCODE_FLAG_NOT, BTLVAR_MOVE_STATUS_FLAGS, MOVE_STATUS_NOT_VERY_EFFECTIVE, _098
    // It’s not very effective...
    PrintMessage BattleStrings_Text_ItsNotVeryEffective, TAG_NONE

_095:
    Wait 
    WaitButtonABTime 30

_098:
    End 
