#include "macros/btlcmd.inc"


_000:
    PrintAttackMessage 
    Wait 
    WaitButtonABTime 15
    // Sour Platinum: the ability banner comes in before the effect
    ShowAbilityBanner BTLSCR_DEFENDER
    Wait 
    // Sour Platinum: the banner names the ability, so its message is the plain one. Without the banner, the ability is named.
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
