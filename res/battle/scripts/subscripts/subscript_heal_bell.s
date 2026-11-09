#include "macros/btlcmd.inc"


_000:
    TryPartyStatusRefresh 
    CompareVarToValue OPCODE_EQU, BTLVAR_CURRENT_MOVE, MOVE_AROMATHERAPY, _010
    // A bell chimed!
    PrintMessage BattleStrings_Text_ABellChimed, TAG_NONE
    GoTo _013

_010:
    // A soothing aroma wafted through the area!
    PrintMessage BattleStrings_Text_ASoothingAromaWaftedThroughTheArea, TAG_NONE

_013:
    Wait 
    WaitButtonABTime 30
    CompareVarToValue OPCODE_EQU, BTLVAR_CURRENT_MOVE, MOVE_AROMATHERAPY, _049
    CompareVarToValue OPCODE_FLAG_NOT, BTLVAR_CALC_TEMP, 0x00000001, _035
    ShowAbilityBanner BTLSCR_ATTACKER
    Wait 
    CheckAbilityBannerAvailable _PlainlityBlocksMove0
    // {0}’s {1} blocks {2}!
    PrintMessage BattleStrings_Text_PokemonsAbilityBlocksMove_Ally, TAG_NICKNAME_ABILITY_MOVE, BTLSCR_ATTACKER, BTLSCR_ATTACKER, BTLSCR_MSG_TEMP
    GoTo _PlainlityBlocksMove0Done

_PlainlityBlocksMove0:
    // It doesn’t affect {0}...
    PrintMessage BattleStrings_Text_ItDoesntAffectPokemon_Ally, TAG_NICKNAME, BTLSCR_ATTACKER

_PlainlityBlocksMove0Done:
    Wait 
    WaitButtonABTime 30

_035:
    CompareVarToValue OPCODE_FLAG_NOT, BTLVAR_CALC_TEMP, 0x00000002, _049
    ShowAbilityBanner BTLSCR_ATTACKER_PARTNER
    Wait 
    CheckAbilityBannerAvailable _PlainlityBlocksMove1
    // {0}’s {1} blocks {2}!
    PrintMessage BattleStrings_Text_PokemonsAbilityBlocksMove_Ally, TAG_NICKNAME_ABILITY_MOVE, BTLSCR_ATTACKER_PARTNER, BTLSCR_ATTACKER_PARTNER, BTLSCR_MSG_TEMP
    GoTo _PlainlityBlocksMove1Done

_PlainlityBlocksMove1:
    // It doesn’t affect {0}...
    PrintMessage BattleStrings_Text_ItDoesntAffectPokemon_Ally, TAG_NICKNAME, BTLSCR_ATTACKER_PARTNER

_PlainlityBlocksMove1Done:
    Wait 
    WaitButtonABTime 30

_049:
    CompareVarToValue OPCODE_FLAG_SET, BTLVAR_CALC_TEMP, 0x00000004, _057
    SetHealthBoxStatusIcon BTLSCR_ATTACKER, BATTLE_ANIMATION_NONE

_057:
    CompareVarToValue OPCODE_FLAG_SET, BTLVAR_CALC_TEMP, 0x00000008, _065
    SetHealthBoxStatusIcon BTLSCR_ATTACKER_PARTNER, BATTLE_ANIMATION_NONE

_065:
    End 
