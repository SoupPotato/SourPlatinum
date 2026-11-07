#include "play_time_manager.h"

#include <nitro.h>
#include <string.h>

#include "play_time.h"
#include "timer.h"

static BOOL sStarted = FALSE;
static u64 sDummy = 0;
static u64 sLastTimestamp = 0;
static u64 sCurrentTimestamp = 0;
static PlayTime *sPlayTime = NULL;
static BOOL sPaused = FALSE; // Sour Platinum: the play time is in the save, so it holds still while the game saves

void PlayTime_FlagNotStarted()
{
    sStarted = FALSE;
}

void PlayTime_Start(PlayTime *playTime)
{
    sStarted = TRUE;
    sDummy = 0;
    sLastTimestamp = 0;
    sPlayTime = playTime;
    sCurrentTimestamp = Timer_GetCurrentTimestamp();
}

// Sour Platinum: the seconds that pass while paused are added once it is unpaused
void PlayTime_SetPaused(BOOL paused)
{
    sPaused = paused;
}

void PlayTime_IncrementTimer(void)
{
    if (sStarted && !sPaused) {
        u64 currentTimestamp = Timer_TicksToSeconds(Timer_GetCurrentTimestamp() - sCurrentTimestamp);

        if (currentTimestamp > sLastTimestamp) {
            PlayTime_Increment(sPlayTime, currentTimestamp - sLastTimestamp);
            sLastTimestamp = currentTimestamp;
        }
    }
}
