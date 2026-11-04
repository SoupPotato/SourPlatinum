#include "macros/btlcmd.inc"


_000:
    CheckIgnorableAbility CHECK_HAVE, BTLSCR_ALL_BATTLERS, ABILITY_DAMP, _038
    CompareVarToValue OPCODE_FLAG_SET, BTLVAR_BATTLE_CTX_STATUS, SYSCTL_MON_SELFDESTRUCTED, _035
    UpdateVar OPCODE_SET, BTLVAR_CALC_TEMP, 0x10000000
    UpdateVarFromVar OPCODE_LEFT_SHIFT, BTLVAR_CALC_TEMP, BTLVAR_ATTACKER
    UpdateVarFromVar OPCODE_FLAG_ON, BTLVAR_BATTLE_CTX_STATUS, BTLVAR_CALC_TEMP
    UpdateMonData OPCODE_SET, BTLSCR_ATTACKER, BATTLEMON_CUR_HP, 0
    UpdateVar OPCODE_SET, BTLVAR_HP_CALC_TEMP, 32767
    UpdateHealthBar BTLSCR_ATTACKER
    Wait 
    Call BATTLE_SUBSCRIPT_ATTACK_MESSAGE_AND_ANIMATION

_035:
    CalcCrit 
    CalcDamage 
    End 

_038:
    PrintAttackMessage 
    Wait 
    WaitButtonABTime 30
    // Sour Platinum: the ability banner comes in before the effect
    ShowAbilityBanner BTLSCR_ABILITY_MON
    Wait 
    // Sour Platinum: the banner names the ability, so its message is the plain one. Without the banner, the ability is named.
    CheckAbilityBannerAvailable _PlainnFromUsingMove0
    // {0}’s {1} prevents {2} from using {3}!
    PrintMessage BattleStrings_Text_PokemonsAbilityPreventsPokemonFromUsingMove_AllyAlly, TAG_NICKNAME_ABILITY_NICKNAME_MOVE, BTLSCR_ABILITY_MON, BTLSCR_ABILITY_MON, BTLSCR_ATTACKER, BTLSCR_ATTACKER
    GoTo _PlainnFromUsingMove0Done

_PlainnFromUsingMove0:
    // {0} cannot use {1}!
    PrintMessage BattleStrings_Text_PokemonCannotUseMove_Ally, TAG_NICKNAME_MOVE, BTLSCR_ATTACKER, BTLSCR_ATTACKER

_PlainnFromUsingMove0Done:
    Wait 
    WaitButtonABTime 30
    UpdateVar OPCODE_FLAG_ON, BTLVAR_BATTLE_CTX_STATUS, SYSCTL_CHECK_LOOP_ONLY_ONCE
    UpdateVar OPCODE_FLAG_ON, BTLVAR_MOVE_STATUS_FLAGS, MOVE_STATUS_NO_MORE_WORK
    End 
