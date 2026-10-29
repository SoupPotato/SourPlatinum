#include "macros/btlcmd.inc"


_000:
    TryReplaceFaintedMon BTLSCR_ATTACKER, TRUE, _029
    Call BATTLE_SUBSCRIPT_ATTACK_MESSAGE_AND_ANIMATION
    TryRestoreStatusOnSwitch BTLSCR_ATTACKER, _013
    UpdateMonData OPCODE_SET, BTLSCR_ATTACKER, BATTLEMON_STATUS, MON_CONDITION_NONE

_013:
    DeletePokemon BTLSCR_ATTACKER
    Wait 
    HealthBoxSlideOut BTLSCR_ATTACKER
    Wait 
    UpdateVarFromVar OPCODE_SET, BTLVAR_SWITCHED_MON, BTLVAR_ATTACKER
    // Sour Platinum: Teleport (Generation 8) switches the user out through this script, but passes nothing on
    CompareVarToValue OPCODE_EQU, BTLVAR_CURRENT_MOVE, MOVE_TELEPORT, _passes_nothing
    UpdateVar OPCODE_FLAG_ON, BTLVAR_BATTLE_CTX_STATUS, SYSCTL_BATON_PASS

_passes_nothing:
    GoToSubscript BATTLE_SUBSCRIPT_SHOW_PARTY_LIST

_029:
    UpdateVar OPCODE_FLAG_ON, BTLVAR_MOVE_STATUS_FLAGS, MOVE_STATUS_FAILED
    End 
