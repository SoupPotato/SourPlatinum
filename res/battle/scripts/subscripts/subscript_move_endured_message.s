#include "macros/btlcmd.inc"


_000:
    CompareVarToValue OPCODE_FLAG_NOT, BTLVAR_MOVE_STATUS_FLAGS, MOVE_STATUS_ENDURED_ITEM, _037
    PlayBattleAnimation BTLSCR_DEFENDER, BATTLE_ANIMATION_HELD_ITEM
    Wait 
    // {0} hung on using its {1}!
    PrintMessage BattleStrings_Text_PokemonHungOnUsingItsItem_Ally, TAG_NICKNAME_ITEM, BTLSCR_DEFENDER, BTLSCR_DEFENDER
    CheckItemHoldEffect CHECK_NOT_HAVE, BTLSCR_DEFENDER, HOLD_EFFECT_ENDURE, _032
    RemoveItem BTLSCR_DEFENDER

_032:
    Wait 
    WaitButtonABTime 30
    GoTo _end

_037:
    CompareVarToValue OPCODE_FLAG_NOT, BTLVAR_MOVE_STATUS_FLAGS, MOVE_STATUS_ENDURED, _end
    CompareMonDataToValue OPCODE_NEQ, BTLSCR_DEFENDER, BATTLEMON_CUR_HP, 1, _end
    CompareVarToValue OPCODE_FLAG_NOT, BTLVAR_MOVE_STATUS_FLAGS, MOVE_STATUS_ENDURED_STURDY, _EnduredBannerShown
    ShowAbilityBanner BTLSCR_DEFENDER
    Wait 

_EnduredBannerShown:
    // {0} endured the hit!
    PrintMessage BattleStrings_Text_PokemonEnduredTheHit_Ally, TAG_NICKNAME, BTLSCR_DEFENDER
    Wait 
    WaitButtonABTime 30
    GoTo _end

_end:
    End 
