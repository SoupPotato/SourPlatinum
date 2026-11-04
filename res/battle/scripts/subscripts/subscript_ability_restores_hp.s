#include "macros/btlcmd.inc"


_000:
    PrintAttackMessage 
    Wait 
    WaitButtonABTime 15
    UpdateMonDataFromVar OPCODE_GET, BTLSCR_DEFENDER, BATTLEMON_MAX_HP, BTLVAR_CALC_TEMP
    CompareMonDataToVar OPCODE_EQU, BTLSCR_DEFENDER, BATTLEMON_CUR_HP, BTLVAR_CALC_TEMP, _033
    // Sour Platinum: the ability banner comes in before the effect
    ShowAbilityBanner BTLSCR_DEFENDER
    Wait 
    PlayBattleAnimation BTLSCR_DEFENDER, BATTLE_ANIMATION_RESTORE_HP
    Wait 
    UpdateVarFromVar OPCODE_SET, BTLVAR_MSG_BATTLER_TEMP, BTLVAR_DEFENDER
    UpdateVar OPCODE_FLAG_ON, BTLVAR_BATTLE_CTX_STATUS, SYSCTL_SKIP_SPRITE_BLINK
    Call BATTLE_SUBSCRIPT_UPDATE_HP
    // Sour Platinum: the banner names the ability, so its message is the plain one. Without the banner, the ability is named.
    CheckAbilityBannerAvailable _PrintRegainedHealth
    // {0} restored HP using its {1}!
    PrintMessage BattleStrings_Text_PokemonRestoredHPUsingItsAbility_Ally, TAG_NICKNAME_ABILITY, BTLSCR_DEFENDER, BTLSCR_DEFENDER
    GoTo _HealMessagePrinted

_PrintRegainedHealth:
    // {0} regained health!
    PrintMessage BattleStrings_Text_PokemonRegainedHealth_Ally, TAG_NICKNAME, BTLSCR_DEFENDER

_HealMessagePrinted:
    Wait 
    WaitButtonABTime 30
    End 

_033:
    // Sour Platinum: the ability banner comes in before the effect
    ShowAbilityBanner BTLSCR_DEFENDER
    Wait 
    // Sour Platinum: the banner names the ability, so its message is the plain one. Without the banner, the ability is named.
    CheckAbilityBannerAvailable _PrintDoesntAffect
    // {0}’s {1} made {2} useless!
    PrintMessage BattleStrings_Text_PokemonsAbilityMadeMoveUseless_Ally, TAG_NICKNAME_ABILITY_MOVE, BTLSCR_DEFENDER, BTLSCR_DEFENDER, BTLSCR_ATTACKER
    GoTo _UselessMessagePrinted

_PrintDoesntAffect:
    // It doesn’t affect {0}...
    PrintMessage BattleStrings_Text_ItDoesntAffectPokemon_Ally, TAG_NICKNAME, BTLSCR_DEFENDER

_UselessMessagePrinted:
    Wait 
    WaitButtonABTime 30
    End 
