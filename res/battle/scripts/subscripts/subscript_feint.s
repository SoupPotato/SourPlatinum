#include "macros/btlcmd.inc"


_000:
    // Sour Platinum: Feint now also hits a target that is not protecting itself, so there is only a message if
    // it broke a Protect or Detect
    IfTurnFlag BTLSCR_DEFENDER, TURN_FLAG_PROTECTING, 0, _022
    CompareVarToValue OPCODE_EQU, BTLVAR_CURRENT_MOVE, MOVE_FEINT, _015
    // It broke through {0}’s protection!
    PrintMessage BattleStrings_Text_ItBrokeThroughPokemonsProtection_Ally, TAG_NICKNAME, BTLSCR_DEFENDER
    GoTo _019

_015:
    // {0} fell for the feint!
    PrintMessage BattleStrings_Text_PokemonFellForTheFeint_Ally, TAG_NICKNAME, BTLSCR_DEFENDER

_019:
    Wait 
    WaitButtonABTime 30

_022:
    SetTurnFlag BTLSCR_DEFENDER, TURN_FLAG_PROTECTING, 0
    End 
