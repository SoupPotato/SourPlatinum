#include "macros/btlcmd.inc"


_000:
    UpdateVar OPCODE_SET, BTLVAR_MSG_ATTACKER, 0

_003:
    CompareVarToValue OPCODE_FLAG_NOT, BTLVAR_SCRIPT_TEMP, 1, _029
    // Sour Platinum: the ability banner comes in before the effect
    ShowAbilityBanner BTLSCR_MSG_ATTACKER
    Wait 
    UpdateVar OPCODE_FLAG_ON, BTLVAR_BATTLE_CTX_STATUS, SYSCTL_SKIP_SPRITE_BLINK
    Call BATTLE_SUBSCRIPT_UPDATE_HP
    // Sour Platinum: the banner names the ability, so its message is the plain one. Without the banner, the ability is named.
    CheckAbilityBannerAvailable _PrintTormented
    // {2} is tormented by {0}’s {1}!
    PrintMessage BattleStrings_Text_PokemonIsTormentedByPokemonsAbility_AllyAlly, TAG_NICKNAME_ABILITY_NICKNAME, BTLSCR_MSG_ATTACKER, BTLSCR_MSG_ATTACKER, BTLSCR_MSG_TEMP
    GoTo _MessagePrinted

_PrintTormented:
    // {0} is tormented!
    PrintMessage BattleStrings_Text_PokemonIsTormented_Ally, TAG_NICKNAME, BTLSCR_MSG_TEMP

_MessagePrinted:
    Wait 
    WaitButtonABTime 30
    CompareMonDataToValue OPCODE_EQU, BTLSCR_MSG_TEMP, BATTLEMON_CUR_HP, 0, _042

_029:
    UpdateVar OPCODE_ADD, BTLVAR_MSG_ATTACKER, 1
    UpdateVar OPCODE_RIGHT_SHIFT, BTLVAR_SCRIPT_TEMP, 1
    CompareVarToValue OPCODE_NEQ, BTLVAR_SCRIPT_TEMP, 0, _003

_042:
    End 
