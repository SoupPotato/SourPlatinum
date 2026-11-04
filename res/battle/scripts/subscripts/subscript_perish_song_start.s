#include "macros/btlcmd.inc"


_000:
    TryPerishSong _045
    Call BATTLE_SUBSCRIPT_ATTACK_MESSAGE_AND_ANIMATION
    // All Pokémon hearing the song will faint in three turns!
    PrintMessage BattleStrings_Text_AllPokemonHearingTheSongWillFaintInThreeTurns, TAG_NONE
    Wait 
    WaitButtonABTime 30
    UpdateVar OPCODE_SET, BTLVAR_MSG_MOVE_TEMP, MOVE_PERISH_SONG
    UpdateVar OPCODE_SET, BTLVAR_MSG_ABILITY_TEMP, ABILITY_SOUNDPROOF
    UpdateVar OPCODE_SET, BTLVAR_BATTLER_SPEED_TEMP, 0

_021:
    GetMonBySpeedOrder BTLVAR_MSG_BATTLER_TEMP
    CheckIgnorableAbility CHECK_NOT_HAVE, BTLSCR_MSG_TEMP, ABILITY_SOUNDPROOF, _037
    // Sour Platinum: the ability banner comes in before the effect
    ShowAbilityBanner BTLSCR_MSG_TEMP
    Wait 
    // Sour Platinum: the banner names the ability, so its message is the plain one. Without the banner, the ability is named.
    CheckAbilityBannerAvailable _PlainlityBlocksMove0
    // {0}’s {1} blocks {2}!
    PrintMessage BattleStrings_Text_PokemonsAbilityBlocksMove_Ally, TAG_NICKNAME_ABILITY_MOVE, BTLSCR_MSG_TEMP, BTLSCR_MSG_TEMP, BTLSCR_MSG_TEMP
    GoTo _PlainlityBlocksMove0Done

_PlainlityBlocksMove0:
    // It doesn’t affect {0}...
    PrintMessage BattleStrings_Text_ItDoesntAffectPokemon_Ally, TAG_NICKNAME, BTLSCR_MSG_TEMP

_PlainlityBlocksMove0Done:
    Wait 
    WaitButtonABTime 30

_037:
    UpdateVar OPCODE_ADD, BTLVAR_BATTLER_SPEED_TEMP, 1
    GoToIfValidMon BTLVAR_BATTLER_SPEED_TEMP, _021
    End 

_045:
    UpdateVar OPCODE_FLAG_ON, BTLVAR_MOVE_STATUS_FLAGS, MOVE_STATUS_FAILED
    End 
