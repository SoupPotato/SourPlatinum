#include "macros/btlcmd.inc"


_000:
    CheckAbility CHECK_HAVE, BTLSCR_ATTACKER, ABILITY_MAGIC_GUARD, _054
    CompareVarToValue OPCODE_FLAG_NOT, BTLVAR_BATTLE_CTX_STATUS, SYSCTL_CRASH_DAMAGE, _054
    // {0} kept going and crashed!
    PrintMessage BattleStrings_Text_PokemonKeptGoingAndCrashed_Ally, TAG_NICKNAME, BTLSCR_ATTACKER
    Wait 
    WaitButtonABTime 30
    // Sour Platinum: Generation 5, the user loses half of its own max HP (rounded down). It used to be half the damage
    // the move would have done, at most half the target's max HP.
    UpdateMonDataFromVar OPCODE_GET, BTLSCR_ATTACKER, BATTLEMON_MAX_HP, BTLVAR_HP_CALC_TEMP
    DivideVarByValue BTLVAR_HP_CALC_TEMP, 2
    UpdateVar OPCODE_MUL, BTLVAR_HP_CALC_TEMP, -1
    UpdateVarFromVar OPCODE_SET, BTLVAR_MSG_BATTLER_TEMP, BTLVAR_ATTACKER
    UpdateVar OPCODE_FLAG_ON, BTLVAR_BATTLE_CTX_STATUS, SYSCTL_SKIP_SPRITE_BLINK
    Call BATTLE_SUBSCRIPT_UPDATE_HP

_054:
    End 
