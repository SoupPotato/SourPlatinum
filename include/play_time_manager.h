#ifndef POKEPLATINUM_PLAY_TIME_MANAGER_H
#define POKEPLATINUM_PLAY_TIME_MANAGER_H

#include "play_time.h"

void PlayTime_FlagNotStarted(void);
void PlayTime_Start(PlayTime *playTime);
void PlayTime_IncrementTimer(void);
void PlayTime_SetPaused(BOOL paused);

#endif // POKEPLATINUM_PLAY_TIME_MANAGER_H
