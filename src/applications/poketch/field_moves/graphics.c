#include "applications/poketch/field_moves/graphics.h"

#include <nitro.h>

#include "constants/heap.h"
#include "generated/items.h"
#include "generated/moves.h"
#include "generated/poketch_apps.h"
#include "generated/text_banks.h"

#include "applications/poketch/poketch_graphics.h"
#include "applications/poketch/poketch_system.h"
#include "applications/poketch/poketch_task.h"

#include "bg_window.h"
#include "field_move_tasks.h"
#include "font.h"
#include "graphics.h"
#include "heap.h"
#include "message.h"
#include "string_gf.h"
#include "sys_task_manager.h"
#include "text.h"

#include "res/graphics/poketch/poketch.naix"

// The app screen is a 24x20 tile window that starts at tile (2, 2) of the Poketch screen.
#define WINDOW_TILE_X      2
#define WINDOW_TILE_Y      2
#define WINDOW_WIDTH_TILES 24
#define WINDOW_HEIGHT_TILES 20

// Layout (in pixels, relative to the window): a title with a dotted line below it, then the available moves in two
// columns of plain text. The hit areas are a bit larger than the text.
#define TITLE_Y           12
#define TITLE_LINE_Y      29
#define TITLE_LINE_LEFT   39
#define TITLE_LINE_RIGHT  154
#define LIST_TOP          40
#define ROW_HEIGHT        24
#define FRAME_WIDTH       88
#define FRAME_HEIGHT      22
#define FRAME_COLUMN_0_X  6
#define FRAME_COLUMN_1_X  98
#define FRAME_TOP_OFFSET  3 // the frame starts this many pixels above the row
#define FRAME_BORDER      2

// Palette indexes of the Poketch screen
#define COLOR_DARKEST 1
#define COLOR_DARK    8
#define COLOR_MEDIUM  15
#define COLOR_LIGHT   4

// The order is row by row, left column first
static const struct {
    u16 fieldMove;
    u16 moveID;
    u16 hmItem;
} sButtons[FIELD_MOVES_BUTTON_COUNT] = {
    { FIELD_MOVE_ROCK_SMASH, MOVE_ROCK_SMASH, ITEM_HM06 },
    { FIELD_MOVE_CUT, MOVE_CUT, ITEM_HM01 },
    { FIELD_MOVE_STRENGTH, MOVE_STRENGTH, ITEM_HM04 },
    { FIELD_MOVE_FLY, MOVE_FLY, ITEM_HM02 },
    { FIELD_MOVE_DEFOG, MOVE_DEFOG, ITEM_HM05 },
    { FIELD_MOVE_SURF, MOVE_SURF, ITEM_HM03 },
    { FIELD_MOVE_ROCK_CLIMB, MOVE_ROCK_CLIMB, ITEM_HM08 },
    { FIELD_MOVE_WATERFALL, MOVE_WATERFALL, ITEM_HM07 },
};

static void EndTask(PoketchTaskManager *taskMan);
static void Task_DrawBackground(SysTask *task, void *taskMan);
static void Task_FreeBackground(SysTask *task, void *taskMan);
static void Task_Redraw(SysTask *task, void *taskMan);
static void DrawButtons(FieldMovesGraphics *graphics);
static void DrawButton(FieldMovesGraphics *graphics, int button);

static int FrameX(int button)
{
    return (button % 2) == 0 ? FRAME_COLUMN_0_X : FRAME_COLUMN_1_X;
}

static int FrameY(int button)
{
    return LIST_TOP - FRAME_TOP_OFFSET + (button / 2) * ROW_HEIGHT;
}

BOOL PoketchFieldMovesGraphics_New(FieldMovesGraphics **dest, const FieldMovesData *data, BgConfig *bgConfig)
{
    FieldMovesGraphics *graphics = Heap_Alloc(HEAP_ID_POKETCH_APP, sizeof(FieldMovesGraphics));

    if (graphics != NULL) {
        PoketchTask_InitActiveTaskList(graphics->activeTasks, FIELD_MOVES_TASK_SLOTS);
        graphics->data = data;
        graphics->bgConfig = PoketchGraphics_GetBgConfig();
        graphics->msgLoader = MessageLoader_Init(MSG_LOADER_LOAD_ON_DEMAND, NARC_INDEX_MSGDATA__PL_MSG, TEXT_BANK_MOVE_NAMES, HEAP_ID_POKETCH_APP);
        graphics->appNameLoader = MessageLoader_Init(MSG_LOADER_LOAD_ON_DEMAND, NARC_INDEX_MSGDATA__PL_MSG, TEXT_BANK_POKETCH_APP_NAMES, HEAP_ID_POKETCH_APP);
        graphics->string = String_Init(32, HEAP_ID_POKETCH_APP);
        *dest = graphics;

        return TRUE;
    }

    return FALSE;
}

void PoketchFieldMovesGraphics_Free(FieldMovesGraphics *graphics)
{
    if (graphics != NULL) {
        String_Free(graphics->string);
        MessageLoader_Free(graphics->appNameLoader);
        MessageLoader_Free(graphics->msgLoader);
        Heap_Free(graphics);
    }
}

static const PoketchTask sFieldMovesTasks[] = {
    { FIELD_MOVES_GRAPHICS_INIT, Task_DrawBackground, 0 },
    { FIELD_MOVES_GRAPHICS_FREE, Task_FreeBackground, 0 },
    { FIELD_MOVES_GRAPHICS_REDRAW, Task_Redraw, 0 },
    { 0 }
};

void PoketchFieldMovesGraphics_StartTask(FieldMovesGraphics *graphics, enum FieldMovesGraphicsTask taskID)
{
    PoketchTask_Start(sFieldMovesTasks, taskID, graphics, graphics->data, graphics->activeTasks, 2, HEAP_ID_POKETCH_APP);
}

BOOL PoketchFieldMovesGraphics_TaskIsNotActive(FieldMovesGraphics *graphics, enum FieldMovesGraphicsTask taskID)
{
    return PoketchTask_TaskIsNotActive(graphics->activeTasks, taskID);
}

BOOL PoketchFieldMovesGraphics_NoActiveTasks(FieldMovesGraphics *graphics)
{
    return PoketchTask_NoActiveTasks(graphics->activeTasks);
}

void PoketchFieldMovesGraphics_GetButtonRect(int button, TouchScreenRect *rect)
{
    rect->rect.left = WINDOW_TILE_X * TILE_WIDTH_PIXELS + FrameX(button);
    rect->rect.top = WINDOW_TILE_Y * TILE_HEIGHT_PIXELS + FrameY(button);
    rect->rect.right = rect->rect.left + FRAME_WIDTH;
    rect->rect.bottom = rect->rect.top + FRAME_HEIGHT;
}

int PoketchFieldMovesGraphics_GetButtonMove(int button)
{
    return sButtons[button].fieldMove;
}

int PoketchFieldMovesGraphics_GetButtonItem(int button)
{
    return sButtons[button].hmItem;
}

static void EndTask(PoketchTaskManager *taskMan)
{
    FieldMovesGraphics *graphics = PoketchTask_GetTaskData(taskMan);

    PoketchTask_EndTask(graphics->activeTasks, taskMan);
}

static void Task_DrawBackground(SysTask *task, void *taskMan)
{
    static const BgTemplate bgTemplate = {
        .x = 0,
        .y = 0,
        .bufferSize = 0x800,
        .baseTile = 0,
        .screenSize = BG_SCREEN_SIZE_256x256,
        .colorMode = GX_BG_COLORMODE_16,
        .screenBase = GX_BG_SCRBASE_0x7000,
        .charBase = GX_BG_CHARBASE_0x00000,
        .bgExtPltt = GX_BG_EXTPLTT_01,
        .priority = 2,
        .areaOver = 0,
        .mosaic = FALSE,
    };
    FieldMovesGraphics *graphics = PoketchTask_GetTaskData(taskMan);

    Bg_InitFromTemplate(graphics->bgConfig, BG_LAYER_SUB_2, &bgTemplate, BG_TYPE_STATIC);
    Bg_FillTilemapRect(graphics->bgConfig, BG_LAYER_SUB_2, 0, 0, 0, 32, 32, 0);
    PoketchGraphics_LoadActivePalette(0, 0);

    Window_Add(graphics->bgConfig, &graphics->window, BG_LAYER_SUB_2, WINDOW_TILE_X, WINDOW_TILE_Y, WINDOW_WIDTH_TILES, WINDOW_HEIGHT_TILES, 0, 1);
    Window_PutToTilemap(&graphics->window);

    DrawButtons(graphics);
    Bg_CopyTilemapBufferToVRAM(graphics->bgConfig, BG_LAYER_SUB_2);

    GXSDispCnt dispCnt = GXS_GetDispCnt();
    GXS_SetVisiblePlane(dispCnt.visiblePlane | GX_PLANEMASK_BG2);

    EndTask(taskMan);
}

static void Task_FreeBackground(SysTask *task, void *taskMan)
{
    FieldMovesGraphics *graphics = PoketchTask_GetTaskData(taskMan);

    Window_Remove(&graphics->window);
    Bg_FreeTilemapBuffer(graphics->bgConfig, BG_LAYER_SUB_2);

    EndTask(taskMan);
}

static void Task_Redraw(SysTask *task, void *taskMan)
{
    FieldMovesGraphics *graphics = PoketchTask_GetTaskData(taskMan);

    DrawButtons(graphics);
    EndTask(taskMan);
}

static void DrawButtons(FieldMovesGraphics *graphics)
{
    Window_FillTilemap(&graphics->window, COLOR_LIGHT);

    // Title and the dotted line under it
    MessageLoader_GetString(graphics->appNameLoader, POKETCH_APPID_FIELDMOVES, graphics->string);

    u32 titleX = (WINDOW_WIDTH_TILES * TILE_WIDTH_PIXELS - Font_CalcStringWidth(FONT_SYSTEM, graphics->string, 0)) / 2;
    Text_AddPrinterWithParamsAndColor(&graphics->window, FONT_SYSTEM, graphics->string, titleX, TITLE_Y, TEXT_SPEED_NO_TRANSFER, TEXT_COLOR(COLOR_DARKEST, COLOR_DARK, COLOR_LIGHT), NULL);

    for (int x = TITLE_LINE_LEFT; x < TITLE_LINE_RIGHT; x += 2) {
        Window_FillRectWithColor(&graphics->window, COLOR_MEDIUM, x, TITLE_LINE_Y, 1, 1);
    }

    for (int button = 0; button < FIELD_MOVES_BUTTON_COUNT; button++) {
        if (graphics->data->moveAvailable[button]) {
            DrawButton(graphics, button);
        }
    }

    Window_LoadTiles(&graphics->window);
}

static void DrawButton(FieldMovesGraphics *graphics, int button)
{
    int x = FrameX(button);
    int y = FrameY(button);
    BOOL pressed = (graphics->data->pressedButton == button);

    // The frame; a pressed button is filled with the dark color and its text is inverted and moved a pixel
    Window_FillRectWithColor(&graphics->window, COLOR_DARKEST, x, y, FRAME_WIDTH, FRAME_HEIGHT);
    Window_FillRectWithColor(&graphics->window, pressed ? COLOR_DARK : COLOR_MEDIUM, x + FRAME_BORDER, y + FRAME_BORDER, FRAME_WIDTH - 2 * FRAME_BORDER, FRAME_HEIGHT - 2 * FRAME_BORDER);

    MessageLoader_GetString(graphics->msgLoader, sButtons[button].moveID, graphics->string);

    u32 textX = x + (FRAME_WIDTH - Font_CalcStringWidth(FONT_SYSTEM, graphics->string, 0)) / 2;
    u32 textY = y + (FRAME_HEIGHT - 16) / 2;

    if (pressed) {
        Text_AddPrinterWithParamsAndColor(&graphics->window, FONT_SYSTEM, graphics->string, textX + 1, textY + 1, TEXT_SPEED_NO_TRANSFER, TEXT_COLOR(COLOR_LIGHT, COLOR_DARKEST, COLOR_DARK), NULL);
    } else {
        Text_AddPrinterWithParamsAndColor(&graphics->window, FONT_SYSTEM, graphics->string, textX, textY, TEXT_SPEED_NO_TRANSFER, TEXT_COLOR(COLOR_DARKEST, COLOR_DARK, COLOR_MEDIUM), NULL);
    }
}
