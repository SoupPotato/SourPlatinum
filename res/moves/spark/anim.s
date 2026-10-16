#include "macros/btlanimcmd.inc"

L_0:
    LoadParticleResource 0, spark_spa
    CreateEmitter 0, 2, EMITTER_CB_SET_POS_TO_ATTACKER
    CreateEmitter 0, 3, EMITTER_CB_SET_POS_TO_ATTACKER
    PlaySoundEffectL SEQ_SE_DP_W209_sseq
    Func_FadeBattlerSprite BATTLE_ANIM_ATTACKER, 1, 1, BATTLE_COLOR_LIGHT_YELLOW1, 10, 
    // A delay of -1 fades in steps of 3 instead of 2, which makes the flashes about 20% faster
    BeginLoop 3
    Func_FadeBg FADE_BG_TYPE_BASE, -1, 0, 8, BATTLE_COLOR_LIGHT_YELLOW1
    WaitForAnimTasks
    Func_FadeBg FADE_BG_TYPE_BASE, -1, 8, 0, BATTLE_COLOR_LIGHT_YELLOW1
    WaitForAnimTasks
    EndLoop
    Delay 5
    // The impact lands as the user lunges forward
    Func_MoveBattlerX2 2, 24, BATTLE_ANIM_BATTLER_SPRITE_ATTACKER
    Func_FadeBattlerSprite BATTLE_ANIM_DEFENDER, 1, 1, BATTLE_COLOR_LIGHT_YELLOW1, 10, 
    CreateEmitter 0, 1, EMITTER_CB_SET_POS_TO_DEFENDER
    CreateEmitter 0, 0, EMITTER_CB_SET_POS_TO_DEFENDER
    CreateEmitter 0, 3, EMITTER_CB_SET_POS_TO_DEFENDER
    Func_Shake 1, 0, 1, 6, BATTLE_ANIM_BATTLER_SPRITE_DEFENDER
    PlaySoundEffectR SEQ_SE_DP_W086_sseq
    Delay 5
    Func_MoveBattlerX2 2, -24, BATTLE_ANIM_BATTLER_SPRITE_ATTACKER
    WaitForAnimTasks
    WaitForAllEmitters
    UnloadParticleSystem 0
    End
