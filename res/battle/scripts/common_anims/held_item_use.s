#include "macros/btlanimcmd.inc"

.data

L_0:
    LoadParticleResource 0, 28
    CreateEmitter 0, 0, EMITTER_CB_SET_POS_TO_ATTACKER
    Delay 5
    Func_FadeBattlerSprite BATTLE_ANIM_ATTACKER, 0, 1, BATTLE_COLOR_WHITE, 10, 0
    // Sour Platinum: the squash and stretch play 30% faster (their sound plays with each squash). The particles keep
    // their speed: 77% of 130% is 100%.
    SetAnimSpeed 130
    SetParticleSpeed 0, 77
    BeginLoop 2
    PlayPannedSoundEffect SEQ_SE_DP_W207_sseq, BATTLE_SOUND_PAN_LEFT
    Func_ScaleBattlerSprite BATTLE_ANIM_BATTLER_SPRITE_ATTACKER, 100, 80, 100, 140, 100, 1, 327685
    Delay 10
    Func_ScaleBattlerSprite BATTLE_ANIM_BATTLER_SPRITE_ATTACKER, 100, 120, 100, 80, 100, 1, 327685
    Delay 10
    EndLoop
    SetAnimSpeed 100
    SetParticleSpeed 0, 100
    PlayPannedSoundEffect SEQ_SE_DP_BT_001_sseq, BATTLE_SOUND_PAN_LEFT
    WaitForAllEmitters
    UnloadParticleSystem 0
    End
