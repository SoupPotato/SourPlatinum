#include "macros/btlcmd.inc"


_000:
    // Sour Platinum: the ability banner comes in before the effect
    ShowAbilityBanner BTLSCR_DEFENDER
    Wait 
    UpdateVar OPCODE_FLAG_ON, BTLVAR_BATTLE_CTX_STATUS, SYSCTL_SKIP_SPRITE_BLINK
    Call BATTLE_SUBSCRIPT_UPDATE_HP
    // Sour Platinum: the banner names the ability, so its message is the plain one. Without the banner, the ability is named.
    CheckAbilityBannerAvailable _PrintIsHurt
    // {2} was hurt by {0}’s {1}!
    PrintMessage BattleStrings_Text_PokemonWasHurtByPokemonsAbility_AllyAlly, TAG_NICKNAME_ABILITY_NICKNAME, BTLSCR_DEFENDER, BTLSCR_DEFENDER, BTLSCR_ATTACKER
    GoTo _Printed

_PrintIsHurt:
    // {0} is hurt!
    PrintMessage BattleStrings_Text_PokemonIsHurt_Ally, TAG_NICKNAME, BTLSCR_ATTACKER

_Printed:
    Wait 
    WaitButtonABTime 30
    End 
