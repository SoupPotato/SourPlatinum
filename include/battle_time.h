#ifndef POKEPLATINUM_BATTLE_TIME_H
#define POKEPLATINUM_BATTLE_TIME_H

#include "sourplatinum_config.h"
#include "system.h"

static inline int BattleTime_TicksPerFrame(void)
{
    return gSystem.fps60 ? 2 : 1;
}

static inline BOOL BattleTime_IsNativeContext(void)
{
    return gSystem.fps60 && gSystem.execTickDiv == 1;
}

static inline u32 BattleTime_Frames(u32 originalFrames, int pacePercent)
{
    if (!gSystem.fps60) {
        return originalFrames;
    }

    pacePercent = pacePercent * gBattleAnimSpeedPercent / 100;

    u32 ticks = (originalFrames * 2 * 100) / pacePercent;
    return (ticks == 0 && originalFrames != 0) ? 1 : ticks;
}

static inline u32 BattleTime_ScaleBySpeed(u32 frames)
{
    u32 scaled = (frames * 100 + gBattleAnimSpeedPercent / 2) / gBattleAnimSpeedPercent;

    return (scaled == 0 && frames != 0) ? 1 : scaled;
}

static inline u32 BattleTime_ToFrames(u32 ticks, int pacePercent)
{
    return gSystem.fps60 ? (ticks * pacePercent) / 200 : ticks;
}

static inline int BattleTime_UpdateSubsteps(void)
{
    return (gSystem.fps60 && !BattleTime_IsNativeContext()) ? 2 : 1;
}

static inline BOOL BattleTime_IsLogicTick(void)
{
    return gSystem.logicTick;
}

#endif
