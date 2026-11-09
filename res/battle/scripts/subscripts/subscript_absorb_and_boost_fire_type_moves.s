#include "macros/btlcmd.inc"


_000:
    PrintAttackMessage 
    Wait 
    WaitButtonABTime 15
    CompareMonDataToValue OPCODE_NEQ, BTLSCR_DEFENDER, BATTLEMON_FLASH_FIRE, 0, _023
    PrintMessage BattleStrings_Text_PokemonsAbilityRaisedThePowerOfItsFireTypeMoves_Ally, TAG_NICKNAME_ABILITY, BTLSCR_DEFENDER, BTLSCR_DEFENDER
    Wait 
    WaitButtonABTime 30
    UpdateMonData OPCODE_FLAG_ON, BTLSCR_DEFENDER, BATTLEMON_FLASH_FIRE, 1
    End 

_023:
    ShowAbilityBanner BTLSCR_DEFENDER
    Wait 
    CheckAbilityBannerAvailable _PlainoveIneffective0
    // {0}’s {1} made {2} ineffective!
    PrintMessage BattleStrings_Text_PokemonsAbilityMadeMoveIneffective_Ally, TAG_NICKNAME_ABILITY_MOVE, BTLSCR_DEFENDER, BTLSCR_DEFENDER, BTLSCR_ATTACKER
    GoTo _PlainoveIneffective0Done

_PlainoveIneffective0:
    // It doesn’t affect {0}...
    PrintMessage BattleStrings_Text_ItDoesntAffectPokemon_Ally, TAG_NICKNAME, BTLSCR_DEFENDER

_PlainoveIneffective0Done:
    Wait 
    WaitButtonABTime 30
    End 
