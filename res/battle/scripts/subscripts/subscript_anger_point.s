#include "macros/btlcmd.inc"


_000:
    // Sour Platinum: the ability banner comes in before the effect
    ShowAbilityBanner BTLSCR_DEFENDER
    Wait 
    PlayBattleAnimation BTLSCR_DEFENDER, BATTLE_ANIMATION_STAT_BOOST
    Wait 
    UpdateMonData OPCODE_SET, BTLSCR_DEFENDER, BATTLEMON_ATTACK_STAGE, 12
    UpdateVar OPCODE_SET, BTLVAR_MSG_TEMP, 1
    // Sour Platinum: the banner names the ability, so its message is the plain one. Without the banner, the ability is named.
    CheckAbilityBannerAvailable _PlaintatWithAbility0
    // {0} maxed its {2} with {1}!
    PrintMessage BattleStrings_Text_PokemonMaxedItsStatWithAbility_Ally, TAG_NICKNAME_ABILITY_STAT, BTLSCR_DEFENDER, BTLSCR_DEFENDER, BTLSCR_MSG_TEMP
    GoTo _PlaintatWithAbility0Done

_PlaintatWithAbility0:
    // {0} maxed its Attack!
    PrintMessage BattleStrings_Text_PokemonMaxedItsAttack_Ally, TAG_NICKNAME, BTLSCR_DEFENDER

_PlaintatWithAbility0Done:
    Wait 
    WaitButtonABTime 30
    End 
