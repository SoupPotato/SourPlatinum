#include "macros/btlcmd.inc"


_000:
    PrintAttackMessage 
    Wait 
    WaitButtonABTime 15
    ShowAbilityBanner BTLSCR_DEFENDER
    Wait 
    CheckAbilityBannerAvailable _PlainlityBlocksMove0
    // {0}’s {1} blocks {2}!
    PrintMessage BattleStrings_Text_PokemonsAbilityBlocksMove_Ally, TAG_NICKNAME_ABILITY_MOVE, BTLSCR_DEFENDER, BTLSCR_DEFENDER, BTLSCR_ATTACKER
    GoTo _PlainlityBlocksMove0Done

_PlainlityBlocksMove0:
    // It doesn’t affect {0}...
    PrintMessage BattleStrings_Text_ItDoesntAffectPokemon_Ally, TAG_NICKNAME, BTLSCR_DEFENDER

_PlainlityBlocksMove0Done:
    Wait 
    WaitButtonABTime 30
    End 
