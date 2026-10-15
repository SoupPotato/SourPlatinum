#include <nitro.h>
#include <nitro/sinit.h>

#include "generated/badges.h"

#include "applications/poketch/field_moves/graphics.h"
#include "applications/poketch/poketch_button.h"
#include "applications/poketch/poketch_system.h"

#include "bag.h"
#include "bg_window.h"
#include "field_move_tasks.h"
#include "heap.h"
#include "save_player.h"
#include "start_menu.h"
#include "sys_task.h"
#include "sys_task_manager.h"

#include "res/sound/pl_sound_data.naix"

typedef struct PoketchFieldMoves {
    u8 state;
    u8 subState;
    u8 shouldExit;
    s16 pendingMove; //!< The move to use once the released button has been drawn again, or -1
    s8 eventButton; //!< The last button event from the button manager (see ButtonCallback)
    u8 eventState;
    u8 needRedraw;
    PoketchButtonManager *buttonManager;
    TouchScreenRect buttonRects[FIELD_MOVES_BUTTON_COUNT];
    FieldMovesData data;
    FieldMovesGraphics *graphics;
    PoketchSystem *poketchSys;
} PoketchFieldMoves;

typedef BOOL (*StateFunc)(PoketchFieldMoves *);

static void NitroStaticInit(void);

static BOOL New(void **appData, PoketchSystem *poketchSys, BgConfig *bgConfig, u32 appID);
static BOOL Init(PoketchFieldMoves *appData, PoketchSystem *poketchSys, BgConfig *bgConfig, u32 appID);
static void Free(PoketchFieldMoves *appData);
static void Exit(void *appData);
static void ButtonCallback(u32 buttonID, u32 buttonState, u32 touchState, void *appData);

static void Task_Main(SysTask *task, void *appData);
static void ChangeState(PoketchFieldMoves *appData, u32 newState);
static BOOL State_LoadApp(PoketchFieldMoves *appData);
static BOOL State_UpdateApp(PoketchFieldMoves *appData);
static BOOL State_UnloadApp(PoketchFieldMoves *appData);

static void NitroStaticInit(void)
{
    PoketchSystem_SetAppFunctions(New, Exit);
}

static BOOL New(void **appData, PoketchSystem *poketchSys, BgConfig *bgConfig, u32 appID)
{
    PoketchFieldMoves *fieldMoves = Heap_Alloc(HEAP_ID_POKETCH_APP, sizeof(PoketchFieldMoves));

    if (fieldMoves != NULL) {
        if (Init(fieldMoves, poketchSys, bgConfig, appID)) {
            if (SysTask_Start(Task_Main, fieldMoves, 1) != NULL) {
                *appData = fieldMoves;
                return TRUE;
            }
        }

        Heap_Free(fieldMoves);
    }

    return FALSE;
}

static BOOL Init(PoketchFieldMoves *appData, PoketchSystem *poketchSys, BgConfig *bgConfig, u32 appID)
{
    if (PoketchFieldMovesGraphics_New(&appData->graphics, &appData->data, bgConfig)) {
        appData->state = 0;
        appData->subState = 0;
        appData->shouldExit = FALSE;
        appData->pendingMove = -1;
        appData->eventButton = FIELD_MOVES_NO_BUTTON;
        appData->eventState = BUTTON_MANAGER_STATE_NULL;
        appData->needRedraw = FALSE;
        appData->data.pressedButton = FIELD_MOVES_NO_BUTTON;
        appData->poketchSys = poketchSys;

        Bag *bag = SaveData_GetBag(PoketchSystem_GetSaveData(poketchSys));

        // A move is only shown when the player has its HM
        for (int button = 0; button < FIELD_MOVES_BUTTON_COUNT; button++) {
            appData->data.moveAvailable[button] = Bag_CanRemoveItem(bag, PoketchFieldMovesGraphics_GetButtonItem(button), 1, HEAP_ID_POKETCH_APP);
            PoketchFieldMovesGraphics_GetButtonRect(button, &appData->buttonRects[button]);
        }

        appData->buttonManager = PoketchButtonManager_New(appData->buttonRects, FIELD_MOVES_BUTTON_COUNT, ButtonCallback, appData, HEAP_ID_POKETCH_APP);

        return TRUE;
    }

    return FALSE;
}

static void ButtonCallback(u32 buttonID, u32 buttonState, u32 touchState, void *appData)
{
    PoketchFieldMoves *fieldMoves = appData;

    if (buttonState != BUTTON_MANAGER_STATE_NULL) {
        fieldMoves->eventButton = buttonID;
        fieldMoves->eventState = buttonState;
    }
}

static void Free(PoketchFieldMoves *appData)
{
    PoketchButtonManager_Free(appData->buttonManager);
    PoketchFieldMovesGraphics_Free(appData->graphics);
    Heap_Free(appData);
}

static void Task_Main(SysTask *task, void *appData)
{
    static const StateFunc stateFuncs[] = {
        State_LoadApp,
        State_UpdateApp,
        State_UnloadApp
    };

    PoketchFieldMoves *fieldMoves = appData;

    if (fieldMoves->state < NELEMS(stateFuncs)) {
        PoketechSystem_UpdateButtonManager(fieldMoves->poketchSys, fieldMoves->buttonManager);

        if (stateFuncs[fieldMoves->state](fieldMoves)) {
            Free(fieldMoves);
            SysTask_Done(task);
            PoketchSystem_NotifyAppUnloaded(fieldMoves->poketchSys);
        }
    }
}

static void Exit(void *appData)
{
    ((PoketchFieldMoves *)appData)->shouldExit = TRUE;
}

static void ChangeState(PoketchFieldMoves *appData, u32 newState)
{
    if (appData->shouldExit == FALSE) {
        appData->state = newState;
    } else {
        appData->state = 2;
    }

    appData->subState = 0;
}

static BOOL State_LoadApp(PoketchFieldMoves *appData)
{
    switch (appData->subState) {
    case 0:
        PoketchFieldMovesGraphics_StartTask(appData->graphics, FIELD_MOVES_GRAPHICS_INIT);
        appData->subState++;
        break;
    case 1:
        if (PoketchFieldMovesGraphics_TaskIsNotActive(appData->graphics, FIELD_MOVES_GRAPHICS_INIT)) {
            PoketchSystem_NotifyAppLoaded(appData->poketchSys);
            ChangeState(appData, 1);
        }
        break;
    }

    return FALSE;
}

static BOOL State_UpdateApp(PoketchFieldMoves *appData)
{
    if (appData->shouldExit) {
        ChangeState(appData, 2);
        return FALSE;
    }

    // Like the pedometer: a button is drawn pressed while the stylus is on it and as normal again when it is released.
    // The move is started when the button has been drawn as normal again, so that the field message (if the move
    // can't be used here) doesn't appear while the button is still being drawn.
    if (appData->eventState != BUTTON_MANAGER_STATE_NULL) {
        int button = appData->eventButton;
        u32 event = appData->eventState;

        appData->eventState = BUTTON_MANAGER_STATE_NULL;

        if (button != FIELD_MOVES_NO_BUTTON && appData->data.moveAvailable[button]) {
            if (event == BUTTON_MANAGER_STATE_TOUCH && appData->data.pressedButton == FIELD_MOVES_NO_BUTTON && appData->pendingMove == -1) {
                PoketchSystem_PlaySoundEffect(SEQ_SE_DP_POKETCH_003_sseq);
                appData->data.pressedButton = button;
                appData->needRedraw = TRUE;
            } else if (event == BUTTON_MANAGER_STATE_TAP && appData->data.pressedButton == button) {
                appData->data.pressedButton = FIELD_MOVES_NO_BUTTON;
                appData->pendingMove = PoketchFieldMovesGraphics_GetButtonMove(button);
                appData->needRedraw = TRUE;
            } else if (event != BUTTON_MANAGER_STATE_TOUCH && appData->data.pressedButton == button) {
                // The stylus moved off the button
                appData->data.pressedButton = FIELD_MOVES_NO_BUTTON;
                appData->needRedraw = TRUE;
            }
        }
    }

    BOOL redrawIdle = PoketchFieldMovesGraphics_TaskIsNotActive(appData->graphics, FIELD_MOVES_GRAPHICS_REDRAW);

    if (appData->needRedraw) {
        if (redrawIdle) {
            appData->needRedraw = FALSE;
            PoketchFieldMovesGraphics_StartTask(appData->graphics, FIELD_MOVES_GRAPHICS_REDRAW);
        }
    } else if (appData->pendingMove != -1 && redrawIdle) {
        int move = appData->pendingMove;

        appData->pendingMove = -1;
        StartMenu_StartPoketchFieldMove(PoketchSystem_GetFieldSystem(appData->poketchSys), move);
    }

    return FALSE;
}

static BOOL State_UnloadApp(PoketchFieldMoves *appData)
{
    switch (appData->subState) {
    case 0:
        PoketchFieldMovesGraphics_StartTask(appData->graphics, FIELD_MOVES_GRAPHICS_FREE);
        appData->subState++;
        break;
    case 1:
        if (PoketchFieldMovesGraphics_NoActiveTasks(appData->graphics)) {
            return TRUE;
        }
        break;
    }

    return FALSE;
}
