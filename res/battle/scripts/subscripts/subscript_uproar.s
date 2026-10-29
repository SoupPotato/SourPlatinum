#include "macros/btlcmd.inc"


_000:
    UpdateVarFromVar OPCODE_SET, BTLVAR_ATTACKER_LOCKED_MOVE, BTLVAR_CURRENT_MOVE
    // Sour Platinum: Generation 5, the uproar always lasts 3 turns (it used to last a random 2-5 turns). The end of turn
    // check treats a counter of 3 as the turn the uproar started, see Battle_UproarJustStarted
    UpdateVar OPCODE_SET, BTLVAR_CALC_TEMP, 3
    UpdateVar OPCODE_LEFT_SHIFT, BTLVAR_CALC_TEMP, 0x00000004
    UpdateMonDataFromVar OPCODE_FLAG_ON, BTLSCR_ATTACKER, BATTLEMON_VOLATILE_STATUS, BTLVAR_CALC_TEMP
    UpdateVarFromVar OPCODE_FLAG_INDEX, BTLVAR_CALC_TEMP, BTLVAR_ATTACKER
    UpdateVar OPCODE_LEFT_SHIFT, BTLVAR_CALC_TEMP, 0x00000008
    UpdateVarFromVar OPCODE_FLAG_ON, BTLVAR_FIELD_CONDITIONS, BTLVAR_CALC_TEMP
    // {0} caused an uproar!
    PrintMessage BattleStrings_Text_PokemonCausedAnUproar_Ally, TAG_NICKNAME, BTLSCR_ATTACKER
    Wait 
    WaitButtonABTime 30
    End 
