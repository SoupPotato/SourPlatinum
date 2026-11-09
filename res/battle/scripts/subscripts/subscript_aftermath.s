#include "macros/btlcmd.inc"


_000:
    ShowAbilityBanner BTLSCR_DEFENDER
    Wait 
    UpdateVar OPCODE_FLAG_ON, BTLVAR_BATTLE_CTX_STATUS, SYSCTL_SKIP_SPRITE_BLINK
    Call BATTLE_SUBSCRIPT_UPDATE_HP
    CheckAbilityBannerAvailable _PrintIsHurt
    // {2} was hurt by {0}’s {1}!
    PrintMessage BattleStrings_Text_PokemonWasHurtByPokemonsAbility_AllyAlly, TAG_NICKNAME_ABILITY_NICKNAME, BTLSCR_DEFENDER, BTLSCR_DEFENDER, BTLSCR_ATTACKER
    GoTo _Printed

_PrintIsHurt:
    PrintMessage BattleStrings_Text_PokemonIsHurt_Ally, TAG_NICKNAME, BTLSCR_ATTACKER

_Printed:
    Wait 
    WaitButtonABTime 30
    End 
