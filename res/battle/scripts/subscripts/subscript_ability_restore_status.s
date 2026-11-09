#include "macros/btlcmd.inc"


_000:
    UpdateMonData OPCODE_SET, BTLSCR_MSG_TEMP, BATTLEMON_STATUS, MON_CONDITION_NONE
    UpdateMonData OPCODE_FLAG_OFF, BTLSCR_MSG_TEMP, BATTLEMON_VOLATILE_STATUS, VOLATILE_CONDITION_NIGHTMARE
    CheckAbilityBannerAvailable _PlainCuredItsStatus
    // {0}’s {1} cured its {2} status!
    PrintMessage BattleStrings_Text_PokemonsAbilityCuredItsStatus_Ally, TAG_NICKNAME_ABILITY_STATUS, BTLSCR_MSG_TEMP, BTLSCR_MSG_BATTLER_TEMP, BTLSCR_MSG_TEMP
    GoTo _PlainCuredItsStatusDone

_PlainCuredItsStatus:
    ShowAbilityBanner BTLSCR_MSG_BATTLER_TEMP
    Wait 
    CompareVarToValue OPCODE_EQU, BTLVAR_MSG_TEMP, 1, _CuredPoison
    CompareVarToValue OPCODE_EQU, BTLVAR_MSG_TEMP, 2, _CuredBurn
    CompareVarToValue OPCODE_EQU, BTLVAR_MSG_TEMP, 3, _CuredParalysis
    CompareVarToValue OPCODE_EQU, BTLVAR_MSG_TEMP, 4, _CuredFreeze
    // {0} woke up!
    PrintMessage BattleStrings_Text_PokemonWokeUp_Ally, TAG_NICKNAME, BTLSCR_MSG_TEMP
    GoTo _PlainCuredItsStatusDone

_CuredPoison:
    PrintMessage BattleStrings_Text_PokemonWasCuredOfItsPoisoningAbility_Ally, TAG_NICKNAME, BTLSCR_MSG_TEMP
    GoTo _PlainCuredItsStatusDone

_CuredBurn:
    PrintMessage BattleStrings_Text_PokemonsBurnWasHealedAbility_Ally, TAG_NICKNAME, BTLSCR_MSG_TEMP
    GoTo _PlainCuredItsStatusDone

_CuredParalysis:
    PrintMessage BattleStrings_Text_PokemonWasCuredOfParalysisAbility_Ally, TAG_NICKNAME, BTLSCR_MSG_TEMP
    GoTo _PlainCuredItsStatusDone

_CuredFreeze:
    // {0} thawed out!
    PrintMessage BattleStrings_Text_PokemonThawedOut_Ally, TAG_NICKNAME, BTLSCR_MSG_TEMP

_PlainCuredItsStatusDone:
    Wait 
    SetHealthBoxStatusIcon BTLSCR_MSG_TEMP, BATTLE_ANIMATION_NONE
    WaitButtonABTime 30
    End 
