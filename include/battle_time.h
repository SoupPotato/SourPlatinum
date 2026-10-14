#ifndef POKEPLATINUM_BATTLE_TIME_H
#define POKEPLATINUM_BATTLE_TIME_H

#include "sourplatinum_config.h"
#include "system.h"

// Sour Platinum 60 fps mode helpers.
//
// In 60 fps mode a "tick" is one VBlank. Code that was written for the original 30 Hz loop runs
// on every other tick (a "logic tick"). Durations in that code are measured in logic frames.
// Code that runs natively on every tick has to measure the same durations in ticks, which is what
// the helpers below are for.

// How many ticks there are in one original logic frame (1 outside of 60 fps mode).
static inline int BattleTime_TicksPerFrame(void)
{
    return gSystem.fps60 ? 2 : 1;
}

// TRUE if the code that is running right now is called on every tick (a native task).
static inline BOOL BattleTime_IsNativeContext(void)
{
    return gSystem.fps60 && gSystem.execTickDiv == 1;
}

// Converts a duration given in original logic frames to ticks.
// pacePercent is one of the SP_PACE_* settings: 100 keeps the original pace, 50 makes it twice as
// slow, 200 twice as fast. Outside of 60 fps mode the duration is returned unchanged.
static inline u32 BattleTime_Frames(u32 originalFrames, int pacePercent)
{
    if (!gSystem.fps60) {
        return originalFrames;
    }

    u32 ticks = (originalFrames * 2 * 100) / pacePercent;
    return (ticks == 0 && originalFrames != 0) ? 1 : ticks;
}

// The opposite of BattleTime_Frames(): turns a tick count (for example the remaining steps of a lerp
// context) back into original logic frames.
static inline u32 BattleTime_ToFrames(u32 ticks, int pacePercent)
{
    return gSystem.fps60 ? (ticks * pacePercent) / 200 : ticks;
}

// A lerp/step context initialised with BattleTime_Frames() has its step counter in ticks.
// When it is updated from code that only runs on logic ticks, it has to advance two ticks per call;
// when it is updated from a native task, one.
static inline int BattleTime_UpdateSubsteps(void)
{
    return (gSystem.fps60 && !BattleTime_IsNativeContext()) ? 2 : 1;
}

// For native code: TRUE on the ticks where the original-rate logic also runs.
// Use it to guard things that must still happen once per original frame (sprite animation ticks, sound, counters).
static inline BOOL BattleTime_IsLogicTick(void)
{
    return gSystem.logicTick;
}

#endif // POKEPLATINUM_BATTLE_TIME_H
