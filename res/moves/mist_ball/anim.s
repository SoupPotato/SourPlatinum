#include "macros/btlanimcmd.inc"

L_0:
    LoadParticleResource 0, mist_ball_spa
    ResetVars
    SetVar BATTLE_ANIM_VAR_BG_MOVE_STEP_X, -32
    SetVar BATTLE_ANIM_VAR_BG_MOVE_STEP_Y, 0
    SetVar BATTLE_ANIM_VAR_BG_ANIM_MODE, 1
    SetVar BATTLE_ANIM_VAR_BG_SCREEN_MODE, 1
    SwitchBg 10, BATTLE_BG_SWITCH_MODE_FADE | BATTLE_BG_SWITCH_FLAG_MOVE
    WaitForBgSwitch
    PlayLoopedSoundEffectC SEQ_SE_DP_W081_sseq, 2, 4
    // Sour Platinum: like Energy Ball, the ball's emitter is moved from the user to the target and the ball rides on it
    // (mist_ball.spa), so that it arrives with the hit (15 frames) and stays on the target, instead of flying past it
    CreateEmitter 0, 0, EMITTER_CB_SET_POS_TO_ATTACKER
    Func_MoveEmitterA2BLinear 0, 0, 0, 0, 15, 64
    Delay 14 // the hit starts 1 frame before the ball arrives
    PlayLoopedSoundEffectR SEQ_SE_DP_W028_sseq, 2, 4
    Func_FadeBg FADE_BG_TYPE_BASE, 1, 0, 8, BATTLE_COLOR_WHITE
    CreateEmitter 0, 5, EMITTER_CB_SET_POS_TO_DEFENDER
    CreateEmitter 0, 6, EMITTER_CB_SET_POS_TO_DEFENDER
    Func_Shake 1, 0, 1, 2, BATTLE_ANIM_BATTLER_SPRITE_DEFENDER
    JumpIfBattlerSide BATTLER_ROLE_ATTACKER, L_1, L_2
    End

L_1:
    CreateEmitter 0, 1, EMITTER_CB_NONE
    CreateEmitter 0, 2, EMITTER_CB_NONE
    WaitForAnimTasks
    Func_FadeBg FADE_BG_TYPE_BASE, 1, 8, 0, BATTLE_COLOR_WHITE
    Func_FadeBattlerSprite BATTLE_ANIM_DEFENDER, 0, 1, BATTLE_COLOR_WHITE, 10, 0
    Delay 2
    PlaySoundEffectC SEQ_SE_DP_186_sseq
    WaitForAnimTasks
    WaitForAllEmitters
    UnloadParticleSystem 0
    ResetVars
    SetVar BATTLE_ANIM_VAR_BG_MOVE_STEP_X, -32
    SetVar BATTLE_ANIM_VAR_BG_MOVE_STEP_Y, 0
    SetVar BATTLE_ANIM_VAR_BG_ANIM_MODE, 1
    SetVar BATTLE_ANIM_VAR_BG_SCREEN_MODE, 1
    RestoreBg 10, BATTLE_BG_SWITCH_MODE_FADE | BATTLE_BG_SWITCH_FLAG_STOP
    WaitForBgSwitch
    End

L_2:
    CreateEmitter 0, 3, EMITTER_CB_NONE
    CreateEmitter 0, 4, EMITTER_CB_NONE
    WaitForAnimTasks
    Func_FadeBg FADE_BG_TYPE_BASE, 1, 8, 0, BATTLE_COLOR_WHITE
    Func_FadeBattlerSprite BATTLE_ANIM_DEFENDER, 0, 1, BATTLE_COLOR_WHITE, 10, 0
    WaitForAnimTasks
    PlaySoundEffectC SEQ_SE_DP_186_sseq
    WaitForAllEmitters
    UnloadParticleSystem 0
    ResetVars
    SetVar BATTLE_ANIM_VAR_BG_MOVE_STEP_X, -32
    SetVar BATTLE_ANIM_VAR_BG_MOVE_STEP_Y, 0
    SetVar BATTLE_ANIM_VAR_BG_ANIM_MODE, 1
    SetVar BATTLE_ANIM_VAR_BG_SCREEN_MODE, 1
    RestoreBg 10, BATTLE_BG_SWITCH_MODE_FADE | BATTLE_BG_SWITCH_FLAG_STOP
    WaitForBgSwitch
    End
