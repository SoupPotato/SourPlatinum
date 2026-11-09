#ifndef POKEPLATINUM_POKETCH_FIELD_MOVES_GRAPHICS_H
#define POKEPLATINUM_POKETCH_FIELD_MOVES_GRAPHICS_H

#include "applications/poketch/poketch_task.h"

#include "bg_window.h"
#include "message.h"
#include "string_gf.h"
#include "touch_screen.h"

#define FIELD_MOVES_TASK_SLOTS 3
#define FIELD_MOVES_BUTTON_COUNT 8
#define FIELD_MOVES_NO_BUTTON    -1

typedef struct FieldMovesData {
    u8 moveAvailable[FIELD_MOVES_BUTTON_COUNT];
    s8 pressedButton;
} FieldMovesData;

typedef struct FieldMovesGraphics {
    const FieldMovesData *data;
    BgConfig *bgConfig;
    u32 activeTasks[POKETCH_TASK_SLOT_BASE + FIELD_MOVES_TASK_SLOTS];
    Window window;
    MessageLoader *msgLoader;
    MessageLoader *appNameLoader;
    String *string;
} FieldMovesGraphics;

enum FieldMovesGraphicsTask {
    FIELD_MOVES_GRAPHICS_INIT = 0,
    FIELD_MOVES_GRAPHICS_FREE,
    FIELD_MOVES_GRAPHICS_REDRAW,
};

BOOL PoketchFieldMovesGraphics_New(FieldMovesGraphics **dest, const FieldMovesData *data, BgConfig *bgConfig);
void PoketchFieldMovesGraphics_Free(FieldMovesGraphics *graphics);
void PoketchFieldMovesGraphics_StartTask(FieldMovesGraphics *graphics, enum FieldMovesGraphicsTask taskID);
BOOL PoketchFieldMovesGraphics_TaskIsNotActive(FieldMovesGraphics *graphics, enum FieldMovesGraphicsTask taskID);
BOOL PoketchFieldMovesGraphics_NoActiveTasks(FieldMovesGraphics *graphics);

void PoketchFieldMovesGraphics_GetButtonRect(int button, TouchScreenRect *rect);

int PoketchFieldMovesGraphics_GetButtonMove(int button);

int PoketchFieldMovesGraphics_GetButtonItem(int button);

#endif
