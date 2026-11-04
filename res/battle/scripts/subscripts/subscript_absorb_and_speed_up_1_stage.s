#include "macros/btlcmd.inc"


_000:
    PrintAttackMessage 
    Wait 
    WaitButtonABTime 15
    CompareMonDataToValue OPCODE_EQU, BTLSCR_DEFENDER, BATTLEMON_SPEED_STAGE, 12, _032
    // Sour Platinum: the ability banner comes in before the effect
    ShowAbilityBanner BTLSCR_DEFENDER
    Wait 
    PlayBattleAnimation BTLSCR_DEFENDER, BATTLE_ANIMATION_STAT_BOOST
    Wait 
    UpdateMonData OPCODE_ADD, BTLSCR_DEFENDER, BATTLEMON_SPEED_STAGE, 1
    UpdateVar OPCODE_SET, BTLVAR_MSG_TEMP, 3
    // Sour Platinum: the banner names the ability, so its message is the plain one. Without the banner, the ability is named.
    CheckAbilityBannerAvailable _PlainyRaisedItsStat0
    // {0}’s {1} raised its {2}!
    PrintMessage BattleStrings_Text_PokemonsAbilityRaisedItsStat_Ally, TAG_NICKNAME_ABILITY_STAT, BTLSCR_DEFENDER, BTLSCR_DEFENDER, BTLSCR_MSG_TEMP
    GoTo _PlainyRaisedItsStat0Done

_PlainyRaisedItsStat0:
    // {0}’s {2} rose!
    PrintMessage BattleStrings_Text_PokemonsStatRoseFromAbility_Ally, TAG_NICKNAME_ABILITY_STAT, BTLSCR_DEFENDER, BTLSCR_DEFENDER, BTLSCR_MSG_TEMP

_PlainyRaisedItsStat0Done:
    Wait 
    WaitButtonABTime 30
    End 

_032:
    // Sour Platinum: the ability banner comes in before the effect
    ShowAbilityBanner BTLSCR_DEFENDER
    Wait 
    // Sour Platinum: the banner names the ability, so its message is the plain one. Without the banner, the ability is named.
    CheckAbilityBannerAvailable _PlainadeMoveUseless0
    // {0}’s {1} made {2} useless!
    PrintMessage BattleStrings_Text_PokemonsAbilityMadeMoveUseless_Ally, TAG_NICKNAME_ABILITY_MOVE, BTLSCR_DEFENDER, BTLSCR_DEFENDER, BTLSCR_ATTACKER
    GoTo _PlainadeMoveUseless0Done

_PlainadeMoveUseless0:
    // It doesn’t affect {0}...
    PrintMessage BattleStrings_Text_ItDoesntAffectPokemon_Ally, TAG_NICKNAME, BTLSCR_DEFENDER

_PlainadeMoveUseless0Done:
    Wait 
    WaitButtonABTime 30
    End 
