#include "macros/btlcmd.inc"


_000:
    // Sour Platinum: Generation 6-7, Oblivious prevents Taunt (Mold Breaker ignores it)
    CheckIgnorableAbility CHECK_HAVE, BTLSCR_DEFENDER, ABILITY_OBLIVIOUS, _blocked
    CompareMonDataToValue OPCODE_NEQ, BTLSCR_DEFENDER, BATTLEMON_TAUNTED_TURNS, 0, _028
    CompareVarToValue OPCODE_FLAG_SET, BTLVAR_MOVE_STATUS_FLAGS, MOVE_STATUS_MISSED|MOVE_STATUS_SEMI_INVULNERABLE, _028
    Call BATTLE_SUBSCRIPT_ATTACK_MESSAGE_AND_ANIMATION
    Random 2, 3
    UpdateMonDataFromVar OPCODE_SET, BTLSCR_DEFENDER, BATTLEMON_TAUNTED_TURNS, BTLVAR_CALC_TEMP
    // {0} fell for the taunt!
    PrintMessage BattleStrings_Text_PokemonFellForTheTaunt_Ally, TAG_NICKNAME, BTLSCR_DEFENDER
    Wait 
    WaitButtonABTime 30
    End 

_028:
    UpdateVar OPCODE_FLAG_ON, BTLVAR_MOVE_STATUS_FLAGS, MOVE_STATUS_FAILED
    End 

_blocked:
    PrintAttackMessage
    Wait
    WaitButtonABTime 30
    // {0}’s {1} made {2} ineffective!
    PrintMessage BattleStrings_Text_PokemonsAbilityMadeMoveIneffective_Ally, TAG_NICKNAME_ABILITY_MOVE, BTLSCR_DEFENDER, BTLSCR_DEFENDER, BTLSCR_ATTACKER
    Wait
    WaitButtonABTime 30
    End 
