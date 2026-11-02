#include "macros/btlanimcmd.inc"

L_0:
    LoadParticleResource 0, healing_wish_spa
    JumpIfEffectChanceOdd L_1, L_2
    End

L_1:
    SetAnimSpeed 120 // Sour Platinum: 20% faster (the sound is played once, so it is unchanged)
    Func_FadeBg FADE_BG_TYPE_BASE, 0, 0, 12, BATTLE_COLOR_BLACK
    WaitForAnimTasks
    Delay 12 // Sour Platinum: 30 originally; 12 is a 10 frame pause at this speed
    CreateEmitter 0, 0, EMITTER_CB_GENERIC
    SetExtraParams 0, 1, 2, 0, 0, 0
    CreateEmitter 0, 3, EMITTER_CB_GENERIC
    SetExtraParams 0, 1, 2, 0, 0, 0
    PlaySoundEffectL SEQ_SE_DP_W361_sseq
    WaitForAllEmitters
    UnloadParticleSystem 0
    Func_FadeBg FADE_BG_TYPE_BASE, 0, 12, 0, BATTLE_COLOR_BLACK
    WaitForAnimTasks
    End

L_2:
    Func_FadeBg FADE_BG_TYPE_BASE, 0, 0, 12, BATTLE_COLOR_BLACK
    WaitForAnimTasks
    CreateEmitter 0, 1, EMITTER_CB_GENERIC
    SetExtraParams 0, 1, 2, 0, 0, 0
    CreateEmitter 0, 2, EMITTER_CB_GENERIC
    SetExtraParams 0, 1, 2, 0, 0, 0
    PlaySoundEffectL SEQ_SE_DP_W361_sseq
    Delay 30
    Func_FadeBattlerSprite BATTLE_ANIM_ATTACKER, 0, 1, BATTLE_COLOR_WHITE, 10, 0
    WaitForAllEmitters
    UnloadParticleSystem 0
    Func_FadeBg FADE_BG_TYPE_BASE, 0, 12, 0, BATTLE_COLOR_BLACK
    WaitForAnimTasks
    End
