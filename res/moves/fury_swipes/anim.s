#include "macros/btlanimcmd.inc"

L_0:
    SetAnimSpeed 120 // Sour Platinum: 20% faster, twice (1.2 x 1.2)
    LoadParticleResource 0, fury_swipes_spa
    LoadParticleResource 1, pound_spa
    CreateEmitter 0, 0, EMITTER_CB_SET_POS_TO_DEFENDER
    CreateEmitter 0, 1, EMITTER_CB_SET_POS_TO_DEFENDER
    PlayLoopedSoundEffectR SEQ_SE_DP_W010_sseq, 5, 2 // Sour Platinum: the second swipe sound comes 6 frames after the first instead of 9
    Delay 2 // Sour Platinum: 3 originally
    CreateEmitter 1, 1, EMITTER_CB_SET_POS_TO_DEFENDER
    CreateEmitter 1, 0, EMITTER_CB_SET_POS_TO_DEFENDER
    Func_Shake 1, 0, 1, 4, BATTLE_ANIM_BATTLER_SPRITE_DEFENDER
    WaitForAllEmitters
    UnloadParticleSystem 0
    End
