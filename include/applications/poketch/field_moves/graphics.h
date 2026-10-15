#ifndef POKEPLATINUM_POKETCH_FIELD_MOVES_GRAPHICS_H
#define POKEPLATINUM_POKETCH_FIELD_MOVES_GRAPHICS_H

#include "applications/poketch/poketch_task.h"

#include "bg_window.h"
#include "message.h"
#include "string_gf.h"
#include "touch_screen.h"

// Sour Platinum: Poketch app that uses the HM moves without a Pokemon that knows them.

#define FIELD_MOVES_TASK_SLOTS 3
#define FIELD_MOVES_BUTTON_COUNT 8
#define FIELD_MOVES_NO_BUTTON    -1

typedef struct FieldMovesData {
    u8 moveAvailable[FIELD_MOVES_BUTTON_COUNT]; //!< Whether the player has the HM of each button's move (the others are not shown)
    s8 pressedButton; //!< The button that is drawn as pressed, or FIELD_MOVES_NO_BUTTON
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

// The area of the screen that a button covers, for the Poketch button manager
void PoketchFieldMovesGraphics_GetButtonRect(int button, TouchScreenRect *rect);

// The move (FIELD_MOVE_*) that a button uses
int PoketchFieldMovesGraphics_GetButtonMove(int button);

// The HM item that a button's move needs
int PoketchFieldMovesGraphics_GetButtonItem(int button);

#endif // POKEPLATINUM_POKETCH_FIELD_MOVES_GRAPHICS_H
