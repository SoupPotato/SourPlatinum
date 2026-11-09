#include "macros/btlcmd.inc"


_000:
    CompareVarToValue OPCODE_EQU, BTLVAR_MSG_TEMP, 7, _taunt
    CheckAbilityBannerAvailable _PlainCured
    // {0} cured its {2} status with its {1}!
    PrintMessage BattleStrings_Text_PokemonCuredItsStatusWithItsAbility_Ally, TAG_NICKNAME_ABILITY_STATUS, BTLSCR_MSG_TEMP, BTLSCR_MSG_TEMP, BTLSCR_MSG_TEMP
    GoTo _CuredMessageDone

_PlainCured:
    ReshowAbilityBanner BTLSCR_MSG_BATTLER_TEMP
    Wait 
    CompareVarToValue OPCODE_EQU, BTLVAR_MSG_TEMP, 1, _CuredPoison
    CompareVarToValue OPCODE_EQU, BTLVAR_MSG_TEMP, 2, _CuredBurn
    CompareVarToValue OPCODE_EQU, BTLVAR_MSG_TEMP, 3, _CuredParalysis
    CompareVarToValue OPCODE_EQU, BTLVAR_MSG_TEMP, 4, _CuredFreeze
    CompareVarToValue OPCODE_EQU, BTLVAR_MSG_TEMP, 5, _CuredConfusion
    CompareVarToValue OPCODE_EQU, BTLVAR_MSG_TEMP, 6, _CuredInfatuation
    // {0} woke up!
    PrintMessage BattleStrings_Text_PokemonWokeUp_Ally, TAG_NICKNAME, BTLSCR_MSG_TEMP
    GoTo _CuredMessageDone

_CuredPoison:
    PrintMessage BattleStrings_Text_PokemonWasCuredOfItsPoisoningAbility_Ally, TAG_NICKNAME, BTLSCR_MSG_TEMP
    GoTo _CuredMessageDone

_CuredBurn:
    PrintMessage BattleStrings_Text_PokemonsBurnWasHealedAbility_Ally, TAG_NICKNAME, BTLSCR_MSG_TEMP
    GoTo _CuredMessageDone

_CuredParalysis:
    PrintMessage BattleStrings_Text_PokemonWasCuredOfParalysisAbility_Ally, TAG_NICKNAME, BTLSCR_MSG_TEMP
    GoTo _CuredMessageDone

_CuredFreeze:
    // {0} thawed out!
    PrintMessage BattleStrings_Text_PokemonThawedOut_Ally, TAG_NICKNAME, BTLSCR_MSG_TEMP
    GoTo _CuredMessageDone

_CuredConfusion:
    PrintMessage BattleStrings_Text_PokemonSnappedOutOfItsConfusionAbility_Ally, TAG_NICKNAME, BTLSCR_MSG_TEMP
    GoTo _CuredMessageDone

_CuredInfatuation:
    PrintMessage BattleStrings_Text_PokemonGotOverItsInfatuationAbility_Ally, TAG_NICKNAME, BTLSCR_MSG_TEMP

_CuredMessageDone:
    Wait 
    SetHealthBoxStatusIcon BTLSCR_MSG_TEMP, BATTLE_ANIMATION_NONE
    WaitButtonABTime 30
    CompareVarToValue OPCODE_EQU, BTLVAR_MSG_TEMP, 0, _033
    CompareVarToValue OPCODE_EQU, BTLVAR_MSG_TEMP, 5, _045
    CompareVarToValue OPCODE_EQU, BTLVAR_MSG_TEMP, 6, _052
    UpdateMonData OPCODE_SET, BTLSCR_MSG_TEMP, BATTLEMON_STATUS, MON_CONDITION_NONE
    GoTo _057

_033:
    UpdateMonData OPCODE_SET, BTLSCR_MSG_TEMP, BATTLEMON_STATUS, MON_CONDITION_NONE
    UpdateMonData OPCODE_FLAG_OFF, BTLSCR_MSG_TEMP, BATTLEMON_VOLATILE_STATUS, VOLATILE_CONDITION_NIGHTMARE
    GoTo _057

_045:
    UpdateMonData OPCODE_FLAG_OFF, BTLSCR_MSG_TEMP, BATTLEMON_VOLATILE_STATUS, VOLATILE_CONDITION_CONFUSION
    GoTo _057

_052:
    UpdateMonData OPCODE_FLAG_OFF, BTLSCR_MSG_TEMP, BATTLEMON_VOLATILE_STATUS, VOLATILE_CONDITION_ATTRACT

_057:
    End 

_taunt:
    UpdateMonData OPCODE_SET, BTLSCR_MSG_TEMP, BATTLEMON_TAUNTED_TURNS, 0
    UpdateVar OPCODE_SET, BTLVAR_MSG_MOVE_TEMP, MOVE_TAUNT
    // {0}’s {1} wore off!
    PrintMessage BattleStrings_Text_PokemonsTauntWoreOff_Ally, TAG_NICKNAME_MOVE, BTLSCR_MSG_TEMP, BTLSCR_MSG_TEMP
    Wait
    WaitButtonABTime 30
    End 
