#include "macros/btlanimcmd.inc"

L_0:
    SetAnimSpeed 120
    LoadParticleResource 1, pound_spa
    LoadParticleResource 0, endeavor_spa
    CreateEmitter 0, 2, EMITTER_CB_SET_POS_TO_ATTACKER
    BeginLoop 3
    // Sour Platinum: the bounce sound is played by each loop, so that it matches the squash (it was a looped sound with its
    // own timing, every 20 frames, 4 times)
    PlaySoundEffectL SEQ_SE_DP_W039_sseq
    Func_FadeBattlerSprite BATTLE_ANIM_ATTACKER, 0, 1, BATTLE_COLOR_YELLOW, 6, 
    Func_ScaleBattlerSprite BATTLE_ANIM_BATTLER_SPRITE_ATTACKER, 100, 120, 100, 80, 100, CYCLES(1), SCALE_F(4) | RESTORE_F(4)
    Delay 7
    CreateEmitter 1, 1, EMITTER_CB_SET_POS_TO_DEFENDER
    CreateEmitter 1, 1, EMITTER_CB_SET_POS_TO_DEFENDER
    Func_ScaleBattlerSprite BATTLE_ANIM_BATTLER_SPRITE_ATTACKER, 100, 80, 100, 140, 100, CYCLES(1), SCALE_F(4) | RESTORE_F(4)
    Func_Shake 1, 0, 1, 2, BATTLE_ANIM_BATTLER_SPRITE_DEFENDER
    Delay 3
    PlaySoundEffectR SEQ_SE_DP_030_sseq
    // Sour Platinum: no wait between loops (4 frames originally)
    EndLoop
    WaitForAllEmitters
    UnloadParticleSystem 0
    End
