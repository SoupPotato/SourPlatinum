#ifndef POKEPLATINUM_SYSTEM_H
#define POKEPLATINUM_SYSTEM_H

#include "constants/heap.h"
#include "constants/system.h"

#include "sys_task_manager.h"

typedef void (*Callback)(void *);
typedef void (*UnkCallback)(void);

enum ButtonMode {
    BUTTON_MODE_NORMAL = 0,
    BUTTON_MODE_START_IS_X = 1,
    BUTTON_MODE_SWAP_XY = 2,
    BUTTON_MODE_L_IS_A = 3,
};

enum SleepType {
    SLEEP_TYPE_SAVE_DATA = 1,
};

#define PAD_KEY                (PAD_KEY_UP | PAD_KEY_DOWN | PAD_KEY_LEFT | PAD_KEY_RIGHT)
#define JOY_NEW(buttons)       (gSystem.pressedKeys & (buttons))
#define JOY_HELD(buttons)      (gSystem.heldKeys & (buttons))
#define JOY_REPEAT(buttons)    (gSystem.pressedKeysRepeatable & (buttons))
#define JOY_NEW_ONLY(buttons)  (JOY_NEW(buttons) == (buttons))
#define JOY_HELD_ONLY(buttons) (JOY_HELD(buttons) == (buttons))

typedef struct System {
    Callback vblankCallback;
    void *vblankCallbackData;
    Callback hblankCallback;
    void *hblankCallbackData;
    UnkCallback dummyCallback_10;
    UnkCallback dummyCallback_14;
    SysTaskManager *mainTaskMgr;
    SysTaskManager *vBlankTaskMgr;
    SysTaskManager *postVBlankTaskMgr;
    SysTaskManager *printTaskMgr;
    u32 *unused_28;
    u32 vblankCounter;
    u32 frameCounter;
    enum ButtonMode buttonMode;
    u32 heldKeysRaw;
    u32 pressedKeysRaw;
    u32 pressedKeysRepeatableRaw;
    u32 heldKeys;
    u32 pressedKeys;
    u32 pressedKeysRepeatable;
    int autorepeatTimer;
    int autorepeatRate;
    int autorepeatDelay;
    u16 touchX;
    u16 touchY;
    u16 touchPressed;
    u16 touchHeld;
    u8 touchAutoSampling;
    u8 whichScreenIs3D;
    u8 gbaCartridgeVersion;
    u8 inhibitSleep;
    u8 inhibitReset;
    u8 padding_69[3];
    BOOL showTitleScreenIntro;
    u32 *heapCanary;
    // Sour Platinum 60 fps mode (used in battle, see sourplatinum_config.h).
    // When fps60 is set the main loop runs once per VBlank instead of once per two VBlanks.
    // Everything that was written for the original 30 Hz loop still runs on "logic ticks"
    // (every other VBlank) so it keeps its original pace; tasks marked as native (tickDiv 1)
    // run on every tick.
    BOOL fps60;
    BOOL logicTick; // TRUE if this loop iteration runs original-rate logic (always TRUE when fps60 is off)
    BOOL vblankCallbackEveryTick; // call vblankCallback on every tick, not just logic ticks
    u32 vblankIsrCounter; // counts every VBlank, incremented in the VBlank interrupt
    u8 execTickDiv; // tickDiv of the task that is currently running; 2 outside of tasks
} System;

extern System gSystem;

// Sour Platinum: speed of the move animation that is playing, in percent (100 = normal). Set by the
// SetAnimSpeed animation script command and reset when the animation starts and ends.
extern u16 gBattleAnimSpeedPercent;

// Sour Platinum: wild Pokemon modifier (see SP_DEBUG_WILD_MODIFIER). gDebugCalcValue is the number that is
// currently shown on the Poketch calculator; 0 / 0 / -1 mean "no override".
extern s32 gDebugCalcValue;
extern u16 gDebugWildSpecies;
extern u8 gDebugWildLevel;
extern s8 gDebugWildNature;
extern u16 gDebugCurMap; // map the player is on
extern u16 gDebugWildMap; // map the modifier was set on, it is cleared when the player changes map

void SetDummyVBlankIntr(void);
void SetVBlankCallback(Callback cb, void *data);
void SetFps60Mode(BOOL enabled);
void DisableHBlank(void);
BOOL SetHBlankCallback(Callback cb, void *data);
void InitSystem(void);
void InitVRAM(void);
void *ReadFileToHeap(enum HeapID heapID, const char *filename);
void ReadFileToBuffer(const char *filename, void **buf);
void ClearUnusedSystemCache(void);
void InitKeypadAndTouchpad(void);
void SetGBACartridgeVersion(int version);
void SleepLock(u8 mask);
void SleepUnlock(u8 mask);
void ReadKeypadAndTouchpad(void);
void SetAutorepeat(int rate, int delay);
void ResetLock(u8 mask);
void ResetUnlock(u8 mask);
void InitHeapCanary(enum HeapID param0);
void FreeHeapCanary(void);
BOOL HeapCanaryOK(void);

#endif // POKEPLATINUM_SYSTEM_H
