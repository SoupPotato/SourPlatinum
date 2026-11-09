#include "battle/ability_banner.h"

#include <nitro.h>
#include <string.h>

#include "constants/graphics.h"
#include "constants/heap.h"
#include "constants/pokemon.h"
#include "generated/battle_message_tags.h"

#include "battle/battle_system.h"

#include "bg_window.h"
#include "font.h"
#include "heap.h"
#include "message.h"
#include "narc.h"
#include "palette.h"
#include "pltt_transfer.h"
#include "pokemon.h"
#include "sound.h"
#include "sound_playback.h"
#include "sound_system.h"
#include "sprite.h"
#include "sprite_system.h"
#include "string_gf.h"
#include "string_template.h"
#include "system.h"
#include "sys_task.h"
#include "sys_task_manager.h"
#include "text.h"

#include "res/graphics/battle/ability_banner/banner.4bpp.h"
#include "res/graphics/battle/sprites.naix"
#include "res/text/bank/battle_strings.h"

#define ABILITY_BANNER_RESID_CHAR(side) (21100 + (side) * 10)
#define ABILITY_BANNER_RESID_PLTT(side) (21101 + (side) * 10)
#define ABILITY_BANNER_RESID_CELL(side) (21102 + (side) * 10)
#define ABILITY_BANNER_RESID_ANIM(side) (21103 + (side) * 10)

#define ABILITY_BANNER_WIDTH_TILES  16
#define ABILITY_BANNER_HEIGHT_TILES 4
#define ABILITY_BANNER_WIDTH        (ABILITY_BANNER_WIDTH_TILES * 8)
#define ABILITY_BANNER_HEIGHT       (ABILITY_BANNER_HEIGHT_TILES * 8)
#define ABILITY_BANNER_TILE_SIZE    32
#define ABILITY_BANNER_BYTES        (ABILITY_BANNER_WIDTH_TILES * ABILITY_BANNER_HEIGHT_TILES * ABILITY_BANNER_TILE_SIZE)

#define ABILITY_BANNER_ART_PLAYER 0
#define ABILITY_BANNER_ART_ENEMY  1

#define ABILITY_BANNER_PLAYER_X        64
#define ABILITY_BANNER_PLAYER_Y        123
#define ABILITY_BANNER_ENEMY_X         192
#define ABILITY_BANNER_ENEMY_Y         59
#define ABILITY_BANNER_OFFSCREEN_DX    144
#define ABILITY_BANNER_SLIDE_SPEED     18
#define ABILITY_BANNER_WIPE_FRAMES     18
#define ABILITY_BANNER_FLASH_DELAY     4
#define ABILITY_BANNER_FLASH_FRAMES    8
#define ABILITY_BANNER_HOLD_FRAMES     (ABILITY_BANNER_FLASH_DELAY + ABILITY_BANNER_FLASH_FRAMES + 1)
#define ABILITY_BANNER_SPRITE_PRIORITY 10

#define ABILITY_BANNER_WAIT_FOR_MESSAGE_FRAMES 1200
#define ABILITY_BANNER_LINGER_FRAMES           60

#define ABILITY_BANNER_COLOR_TEXT        1
#define ABILITY_BANNER_COLOR_SHADOW      2
#define ABILITY_BANNER_FIRST_FLASH_COLOR 3
#define ABILITY_BANNER_COLOR_KEY         15

#define ABILITY_BANNER_PLAYER_TEXT_CENTER 53
#define ABILITY_BANNER_TEXT_STAGGER       16
#define ABILITY_BANNER_ENEMY_TEXT_CENTER  74
#define ABILITY_BANNER_LINE_1_Y    8
#define ABILITY_BANNER_LINE_2_Y    19

#define ABILITY_BANNER_MOSAIC_MAX        15
#define ABILITY_BANNER_MOSAIC_STEP_TIME  2

enum AbilityBannerState {
    ABILITY_BANNER_STATE_SLIDE_IN = 0,
    ABILITY_BANNER_STATE_WIPE,
    ABILITY_BANNER_STATE_HOLD,
    ABILITY_BANNER_STATE_CHANGE,
};

enum AbilityBannerChangePhase {
    ABILITY_BANNER_CHANGE_PIXELATE = 0,
    ABILITY_BANNER_CHANGE_REDRAW,
    ABILITY_BANNER_CHANGE_UNPIXELATE,
    ABILITY_BANNER_CHANGE_WAIT_SOUND,
};

typedef struct AbilityBanner {
    BattleSystem *battleSys;
    SysTask *task;
    ManagedSprite *sprite;
    u8 state;
    u8 timer;
    u8 msgIdx;
    u8 paletteSlot;
    u16 timeout;
    u16 lingerFrames;
    u8 messageGone;
    u8 printed;
    u8 side;
    u8 wipeColumn;
    u8 wipeFrames;
    u8 flashStarted;
    u8 changePending;
    u8 changePhase;
    u8 changeTimer;
    u8 mosaic;
    u16 changeAbility;
    u8 *tiles;
    int owner;
    u16 ability;
    u16 order;
    s16 restX;
    s16 x;
    s16 direction;
    u16 colors[PALETTE_SIZE];
} AbilityBanner;

static AbilityBanner *sAbilityBanners[2] = { NULL, NULL };
static AbilityBanner *sLastBanner = NULL;
static u16 sBannerOrder = 0;

enum AbilityBannerSounds {
    ABILITY_BANNER_SOUNDS_INTRO = 0,
    ABILITY_BANNER_SOUNDS_CHANGE,
};

static BOOL sSoundsLoaded = FALSE;
static u8 sSoundSet;
static int sSoundHeapState;
static u32 sSoundHeapFreeSize;

static BOOL AbilityBanner_AreSoundsLoaded(void);
static void AbilityBanner_FreeSounds(void);

static void AbilityBanner_LoadSounds(enum AbilityBannerSounds set)
{
    if (AbilityBanner_AreSoundsLoaded()) {
        if (sSoundSet == set) {
            return;
        }

        AbilityBanner_FreeSounds();
    }

    NNSSndHeapHandle heap = SoundSystem_Get()->heap;
    u32 flags = NNS_SND_ARC_LOAD_SEQ | NNS_SND_ARC_LOAD_BANK | NNS_SND_ARC_LOAD_WAVE;

    sSoundHeapState = NNS_SndHeapSaveState(heap);

    if (sSoundHeapState == SOUND_HEAP_STATE_INVALID) {
        return;
    }

    BOOL loaded;

    if (set == ABILITY_BANNER_SOUNDS_INTRO) {
        loaded = SoundSystem_LoadSequenceEx(SEQ_SE_WB_SHOOTER_sseq, flags) && SoundSystem_LoadSequenceEx(SEQ_SE_WB_DECIDE2_sseq, flags);
    } else {
        loaded = SoundSystem_LoadSequenceEx(SEQ_SE_WB_DECIDE3_sseq, flags);
    }

    if (loaded == FALSE) {
        SoundSystem_LoadHeapState(sSoundHeapState - 1);
        return;
    }

    sSoundHeapFreeSize = NNS_SndHeapGetFreeSize(heap);
    sSoundSet = set;
    sSoundsLoaded = TRUE;
}

static BOOL AbilityBanner_AreSoundsLoaded(void)
{
    if (sSoundsLoaded && NNS_SndHeapGetCurrentLevel(SoundSystem_Get()->heap) < sSoundHeapState) {
        sSoundsLoaded = FALSE;
    }

    return sSoundsLoaded;
}

static BOOL AbilityBanner_AreSoundsLoadedFor(enum AbilityBannerSounds set)
{
    return AbilityBanner_AreSoundsLoaded() && sSoundSet == set;
}

static void AbilityBanner_FreeSounds(void)
{
    if (!AbilityBanner_AreSoundsLoaded()) {
        return;
    }

    NNSSndHeapHandle heap = SoundSystem_Get()->heap;

    if (sSoundSet == ABILITY_BANNER_SOUNDS_INTRO) {
        Sound_StopEffect(SEQ_SE_WB_SHOOTER_sseq, 0);
        Sound_StopEffect(SEQ_SE_WB_DECIDE2_sseq, 0);
    } else {
        Sound_StopEffect(SEQ_SE_WB_DECIDE3_sseq, 0);
    }

    if (NNS_SndHeapGetCurrentLevel(heap) == sSoundHeapState && NNS_SndHeapGetFreeSize(heap) == sSoundHeapFreeSize) {
        SoundSystem_LoadHeapState(sSoundHeapState - 1);
    }

    sSoundsLoaded = FALSE;
}

static void AbilityBanner_Task(SysTask *task, void *data);
static void AbilityBanner_Free(AbilityBanner *banner);
static BOOL AbilityBanner_GetOwnerAndAbility(const BattleMessage *battleMsg, int *owner, int *ability);
static AbilityBanner *AbilityBanner_New(BattleSystem *battleSys, const String *line1, const String *line2, BOOL isPlayerSide);
static void AbilityBanner_Draw(BattleSystem *battleSys, AbilityBanner *banner, const String *line1, const String *line2, BOOL isPlayerSide);
static void AbilityBanner_CopyColumn(ManagedSprite *sprite, const u8 *src, int column);
static void AbilityBanner_SetFlash(AbilityBanner *banner, int fraction);
static BOOL AbilityBanner_MakeLines(BattleSystem *battleSys, int owner, int ability, String **line1, String **line2);
static void AbilityBanner_Compose(BattleSystem *battleSys, u8 *out, const String *line1, const String *line2, BOOL isPlayerSide);

static BOOL AbilityBanner_GetOwnerAndAbility(const BattleMessage *battleMsg, int *owner, int *ability)
{
    switch (battleMsg->tags) {
    case TAG_NICKNAME_ABILITY:
    case TAG_NICKNAME_ABILITY_NICKNAME:
    case TAG_NICKNAME_ABILITY_MOVE:
    case TAG_NICKNAME_ABILITY_ITEM:
    case TAG_NICKNAME_ABILITY_STAT:
    case TAG_NICKNAME_ABILITY_TYPE:
    case TAG_NICKNAME_ABILITY_STATUS:
    case TAG_NICKNAME_ABILITY_NUMBER:
    case TAG_NICKNAME_ABILITY_NICKNAME_MOVE:
    case TAG_NICKNAME_ABILITY_NICKNAME_ABILITY:
    case TAG_NICKNAME_ABILITY_NICKNAME_STAT:
        *owner = battleMsg->params[0];
        *ability = battleMsg->params[1];
        return TRUE;
    case TAG_ABILITY_NICKNAME:
        *ability = battleMsg->params[0];
        *owner = battleMsg->params[1];
        return TRUE;
    }

    return FALSE;
}

BOOL AbilityBanner_MessageNamesAbility(const BattleMessage *battleMsg)
{
    int owner, ability;
    return AbilityBanner_GetOwnerAndAbility(battleMsg, &owner, &ability) && ability > 0;
}

BOOL AbilityBanner_IsBannerOnlyMessage(const BattleMessage *battleMsg)
{
    return (battleMsg->id == BattleStrings_Text_AbilityBanner || battleMsg->id == BattleStrings_Text_AbilityBannerReshow)
        && AbilityBanner_MessageNamesAbility(battleMsg);
}

void AbilityBanner_TryShow(BattleSystem *battleSys, const BattleMessage *battleMsg, u8 msgIdx)
{
    int owner, ability;

    if (AbilityBanner_GetOwnerAndAbility(battleMsg, &owner, &ability) == FALSE || ability <= 0) {
        return;
    }

    BOOL bannerOnly = (msgIdx == ABILITY_BANNER_NO_MESSAGE);

    int battler = owner & 0xFF;
    AbilityBanner *shown = sAbilityBanners[BattleSystem_GetBattlerSide(battleSys, battler) == 0 ? 0 : 1];

    BOOL reshow = battleMsg->id == BattleStrings_Text_AbilityBannerReshow;

    if (shown != NULL && shown->owner == (owner & 0xFFFF) && shown->ability == ability && reshow == FALSE) {
        if (bannerOnly) {
            shown->timeout = ABILITY_BANNER_WAIT_FOR_MESSAGE_FRAMES;

            if (shown->msgIdx != ABILITY_BANNER_NO_MESSAGE) {
                shown->msgIdx = ABILITY_BANNER_NO_MESSAGE;
                shown->printed = FALSE;
                shown->messageGone = FALSE;
                shown->lingerFrames = 0;
                shown->order = ++sBannerOrder;
                sLastBanner = shown;
            }
        } else {
            shown->msgIdx = msgIdx;
            shown->printed = FALSE;
            shown->messageGone = FALSE;
            sLastBanner = shown;
        }

        return;
    }

    String *ownerString, *abilityString;

    if (AbilityBanner_MakeLines(battleSys, owner, ability, &ownerString, &abilityString) == FALSE) {
        return;
    }

    AbilityBanner *banner = AbilityBanner_New(battleSys, ownerString, abilityString, BattleSystem_GetBattlerSide(battleSys, battler) == 0);

    if (banner != NULL) {
        banner->owner = owner & 0xFFFF;
        banner->ability = ability;

        if (bannerOnly) {
            banner->msgIdx = ABILITY_BANNER_NO_MESSAGE;
            banner->timeout = ABILITY_BANNER_WAIT_FOR_MESSAGE_FRAMES;
        } else {
            banner->msgIdx = msgIdx;
        }
    }

    String_Free(ownerString);
    String_Free(abilityString);
}

static BOOL AbilityBanner_MakeLines(BattleSystem *battleSys, int owner, int ability, String **line1, String **line2)
{
    Pokemon *mon = BattleSystem_GetPartyPokemon(battleSys, owner & 0xFF, (owner >> 8) & 0xFF);

    if (mon == NULL) {
        return FALSE;
    }

    MessageLoader *msgLoader = BattleSystem_GetMessageLoader(battleSys);
    StringTemplate *strFormatter = BattleSystem_GetStringTemplate(battleSys);

    StringTemplate_SetNickname(strFormatter, 0, Pokemon_GetBoxPokemon(mon));
    StringTemplate_SetAbilityName(strFormatter, 1, ability);

    *line1 = String_Init(MON_NAME_LEN + 12, HEAP_ID_BATTLE);
    *line2 = String_Init(MON_NAME_LEN + 12, HEAP_ID_BATTLE);
    String *ownerTemplate = MessageLoader_GetNewString(msgLoader, BattleStrings_Text_AbilityBannerOwner);
    String *abilityTemplate = MessageLoader_GetNewString(msgLoader, BattleStrings_Text_AbilityBannerAbility);

    StringTemplate_Format(strFormatter, *line1, ownerTemplate);
    StringTemplate_Format(strFormatter, *line2, abilityTemplate);

    String_Free(ownerTemplate);
    String_Free(abilityTemplate);
    return TRUE;
}

BOOL AbilityBanner_IsChangeMessage(const BattleMessage *battleMsg)
{
    return battleMsg->id == BattleStrings_Text_AbilityBannerChange;
}

void AbilityBanner_StartChange(BattleSystem *battleSys, const BattleMessage *battleMsg)
{
    int owner, ability;

    if (AbilityBanner_GetOwnerAndAbility(battleMsg, &owner, &ability) == FALSE || ability <= 0) {
        return;
    }

    AbilityBanner *banner = sAbilityBanners[BattleSystem_GetBattlerSide(battleSys, owner & 0xFF) == 0 ? 0 : 1];

    if (banner == NULL || banner->owner != (owner & 0xFFFF)) {
        return;
    }

    banner->changePending = TRUE;
    banner->changeAbility = ability;

    AbilityBanner_LoadSounds(ABILITY_BANNER_SOUNDS_CHANGE);
}

static AbilityBanner *AbilityBanner_New(BattleSystem *battleSys, const String *line1, const String *line2, BOOL isPlayerSide)
{
    int side = isPlayerSide ? 0 : 1;

    if (sAbilityBanners[side] != NULL) {
        AbilityBanner *banner = sAbilityBanners[side];

        Heap_Free(banner->tiles);
        banner->state = ABILITY_BANNER_STATE_SLIDE_IN;
        banner->timer = 0;
        banner->msgIdx = ABILITY_BANNER_NO_MESSAGE;
        banner->timeout = 0;
        banner->lingerFrames = 0;
        banner->messageGone = FALSE;
        banner->printed = FALSE;
        banner->wipeColumn = 0;
        banner->wipeFrames = 0;
        banner->flashStarted = FALSE;
        banner->changePending = FALSE;
        banner->changePhase = 0;
        banner->changeTimer = 0;
        banner->mosaic = 0;
        banner->owner = -1;
        banner->ability = 0;
        banner->order = ++sBannerOrder;
        banner->x = banner->restX - banner->direction * ABILITY_BANNER_OFFSCREEN_DX;

        s16 x, y;
        ManagedSprite_GetPositionXY(banner->sprite, &x, &y);
        ManagedSprite_SetPositionXY(banner->sprite, banner->x, y);
        AbilityBanner_SetFlash(banner, 0);
        AbilityBanner_Draw(battleSys, banner, line1, line2, isPlayerSide);

        sLastBanner = banner;
        AbilityBanner_LoadSounds(ABILITY_BANNER_SOUNDS_INTRO);
        return banner;
    }

    if (PlttTransfer_HasFreeSpace(1, NNS_G2D_VRAM_TYPE_2DMAIN) == FALSE) {
        return NULL;
    }

    SpriteSystem *spriteSys = BattleSystem_GetSpriteSystem(battleSys);
    SpriteManager *spriteMan = BattleSystem_GetSpriteManager(battleSys);
    PaletteData *paletteData = BattleSystem_GetPaletteData(battleSys);
    NARC *narc = NARC_ctor(NARC_INDEX_BATTLE__GRAPHIC__PL_BATT_OBJ, HEAP_ID_BATTLE);

    SpriteSystem_LoadCharResObjFromOpenNarc(spriteSys, spriteMan, narc, ability_banner_banner_NCGR_lz, TRUE, NNS_G2D_VRAM_TYPE_2DMAIN, ABILITY_BANNER_RESID_CHAR(side));
    u8 paletteSlot = SpriteSystem_LoadPaletteBufferFromOpenNarc(paletteData, PLTTBUF_MAIN_OBJ, spriteSys, spriteMan, narc, ability_banner_banner_NCLR, FALSE, 1, NNS_G2D_VRAM_TYPE_2DMAIN, ABILITY_BANNER_RESID_PLTT(side));
    SpriteSystem_LoadCellResObjFromOpenNarc(spriteSys, spriteMan, narc, ability_banner_banner_cell_NCER_lz, TRUE, ABILITY_BANNER_RESID_CELL(side));
    SpriteSystem_LoadAnimResObjFromOpenNarc(spriteSys, spriteMan, narc, misc_single_frame_anim_NANR_lz_5, TRUE, ABILITY_BANNER_RESID_ANIM(side));
    NARC_dtor(narc);

    AbilityBanner *banner = Heap_Alloc(HEAP_ID_BATTLE, sizeof(AbilityBanner));
    memset(banner, 0, sizeof(AbilityBanner));

    banner->battleSys = battleSys;
    banner->state = ABILITY_BANNER_STATE_SLIDE_IN;
    banner->msgIdx = ABILITY_BANNER_NO_MESSAGE;
    banner->owner = -1;
    banner->order = ++sBannerOrder;
    banner->side = side;
    banner->paletteSlot = paletteSlot;
    MI_CpuCopy16(PaletteData_GetUnfadedBuffer(paletteData, PLTTBUF_MAIN_OBJ) + PLTT_DEST(paletteSlot), banner->colors, sizeof(banner->colors));

    s16 restY;
    if (isPlayerSide) {
        banner->restX = ABILITY_BANNER_PLAYER_X;
        banner->direction = 1;
        restY = ABILITY_BANNER_PLAYER_Y;
    } else {
        banner->restX = ABILITY_BANNER_ENEMY_X;
        banner->direction = -1;
        restY = ABILITY_BANNER_ENEMY_Y;
    }

    banner->x = banner->restX - banner->direction * ABILITY_BANNER_OFFSCREEN_DX;

    SpriteTemplate template = {
        .x = banner->x,
        .y = restY,
        .z = 0,
        .animIdx = 0,
        .priority = ABILITY_BANNER_SPRITE_PRIORITY,
        .plttIdx = 0,
        .vramType = NNS_G2D_VRAM_TYPE_2DMAIN,
        .resources = {
            ABILITY_BANNER_RESID_CHAR(side),
            ABILITY_BANNER_RESID_PLTT(side),
            ABILITY_BANNER_RESID_CELL(side),
            ABILITY_BANNER_RESID_ANIM(side),
            SPRITE_RESOURCE_NONE,
            SPRITE_RESOURCE_NONE,
        },
        .bgPriority = 0,
        .vramTransfer = FALSE,
    };

    banner->sprite = SpriteSystem_NewSprite(spriteSys, spriteMan, &template);
    AbilityBanner_Draw(battleSys, banner, line1, line2, isPlayerSide);

    banner->task = SysTask_Start(AbilityBanner_Task, banner, 0);
    SysTask_SetTickDiv(banner->task, 1);
    sAbilityBanners[side] = banner;
    sLastBanner = banner;

    AbilityBanner_LoadSounds(ABILITY_BANNER_SOUNDS_INTRO);

    return banner;
}

static u8 GetPixel(const u8 *tiles, int x, int y)
{
    u8 byte = tiles[((y / 8) * ABILITY_BANNER_WIDTH_TILES + x / 8) * ABILITY_BANNER_TILE_SIZE + (y % 8) * 4 + (x % 8) / 2];
    return (x & 1) ? (byte >> 4) : (byte & 0x0F);
}

static void SetPixel(u8 *tiles, int x, int y, u8 color)
{
    u8 *byte = &tiles[((y / 8) * ABILITY_BANNER_WIDTH_TILES + x / 8) * ABILITY_BANNER_TILE_SIZE + (y % 8) * 4 + (x % 8) / 2];
    *byte = (x & 1) ? ((*byte & 0x0F) | (color << 4)) : ((*byte & 0xF0) | color);
}

static void AbilityBanner_CopyColumn(ManagedSprite *sprite, const u8 *src, int column)
{
    NNSG2dImageProxy *imgProxy = Sprite_GetImageProxy(sprite->sprite);
    u8 *dst = (u8 *)G2_GetOBJCharPtr() + imgProxy->vramLocation.baseAddrOfVram[NNS_G2D_VRAM_TYPE_2DMAIN];
    int partTiles = ABILITY_BANNER_WIDTH_TILES / 2;
    int part = column / partTiles;

    for (int row = 0; row < ABILITY_BANNER_HEIGHT_TILES; row++) {
        MI_CpuCopy16(
            &src[(row * ABILITY_BANNER_WIDTH_TILES + column) * ABILITY_BANNER_TILE_SIZE],
            &dst[(part * partTiles * ABILITY_BANNER_HEIGHT_TILES + row * partTiles + column % partTiles) * ABILITY_BANNER_TILE_SIZE],
            ABILITY_BANNER_TILE_SIZE);
    }
}

static void AbilityBanner_Draw(BattleSystem *battleSys, AbilityBanner *banner, const String *line1, const String *line2, BOOL isPlayerSide)
{
    banner->tiles = Heap_Alloc(HEAP_ID_BATTLE, ABILITY_BANNER_BYTES);
    AbilityBanner_Compose(battleSys, banner->tiles, line1, line2, isPlayerSide);

    const u8 *art = &sAbilityBannerBitmap[(isPlayerSide ? ABILITY_BANNER_ART_PLAYER : ABILITY_BANNER_ART_ENEMY) * ABILITY_BANNER_BYTES];

    for (int column = 0; column < ABILITY_BANNER_WIDTH_TILES; column++) {
        AbilityBanner_CopyColumn(banner->sprite, art, column);
    }
}

static void AbilityBanner_Compose(BattleSystem *battleSys, u8 *out, const String *line1, const String *line2, BOOL isPlayerSide)
{
    BgConfig *bgConfig = BattleSystem_GetBgConfig(battleSys);
    Window window, textWindow;

    Window_AddToTopLeftCorner(bgConfig, &window, ABILITY_BANNER_WIDTH_TILES, ABILITY_BANNER_HEIGHT_TILES, 0, 0);
    Window_AddToTopLeftCorner(bgConfig, &textWindow, ABILITY_BANNER_WIDTH_TILES, ABILITY_BANNER_HEIGHT_TILES, 0, ABILITY_BANNER_COLOR_KEY);

    const u8 *art = &sAbilityBannerBitmap[(isPlayerSide ? ABILITY_BANNER_ART_PLAYER : ABILITY_BANNER_ART_ENEMY) * ABILITY_BANNER_BYTES];

    MI_CpuCopy16(art, window.pixels, ABILITY_BANNER_BYTES);

    Font_InitManager(FONT_BANNER, HEAP_ID_BATTLE);

    TextColor textColor = TEXT_COLOR(ABILITY_BANNER_COLOR_TEXT, ABILITY_BANNER_COLOR_SHADOW, ABILITY_BANNER_COLOR_KEY);
    int line1Width = Font_CalcStringWidth(FONT_BANNER, line1, 0);
    int line2Width = Font_CalcStringWidth(FONT_BANNER, line2, 0);
    int blockWidth = line1Width > line2Width + ABILITY_BANNER_TEXT_STAGGER ? line1Width : line2Width + ABILITY_BANNER_TEXT_STAGGER;
    int center = isPlayerSide ? ABILITY_BANNER_PLAYER_TEXT_CENTER : ABILITY_BANNER_ENEMY_TEXT_CENTER;
    int blockStart = center - blockWidth / 2;

    if (blockStart + blockWidth > ABILITY_BANNER_WIDTH) {
        blockStart = ABILITY_BANNER_WIDTH - blockWidth;
    }

    if (blockStart < 0) {
        blockStart = 0;
    }

    int line1X = blockStart;
    int line2X = blockStart + blockWidth - line2Width;

    for (int line = 0; line < 2; line++) {
        Window_FillTilemap(&textWindow, ABILITY_BANNER_COLOR_KEY);

        if (line == 0) {
            Text_AddPrinterWithParamsColorAndSpacing(&textWindow, FONT_BANNER, line1, line1X, ABILITY_BANNER_LINE_1_Y, TEXT_SPEED_NO_TRANSFER, textColor, 0, 0, NULL);
        } else {
            Text_AddPrinterWithParamsColorAndSpacing(&textWindow, FONT_BANNER, line2, line2X, ABILITY_BANNER_LINE_2_Y, TEXT_SPEED_NO_TRANSFER, textColor, 0, 0, NULL);
        }

        for (int y = 0; y < ABILITY_BANNER_HEIGHT; y++) {
            for (int x = 0; x < ABILITY_BANNER_WIDTH; x++) {
                u8 color = GetPixel(textWindow.pixels, x, y);

                if (color != ABILITY_BANNER_COLOR_KEY) {
                    SetPixel(window.pixels, x, y, color);
                }
            }
        }
    }

    Font_Free(FONT_BANNER);

    MI_CpuCopy16(window.pixels, out, ABILITY_BANNER_BYTES);

    Window_Remove(&textWindow);
    Window_Remove(&window);
}

static void AbilityBanner_SetFlash(AbilityBanner *banner, int fraction)
{
    u16 colors[PALETTE_SIZE];

    for (int i = 0; i < PALETTE_SIZE; i++) {
        u16 color = banner->colors[i];

        if (i >= ABILITY_BANNER_FIRST_FLASH_COLOR && fraction > 0) {
            int r = BlendColor(color & 0x1F, 0x1F, fraction);
            int g = BlendColor((color >> 5) & 0x1F, 0x1F, fraction);
            int b = BlendColor((color >> 10) & 0x1F, 0x1F, fraction);
            color = r | (g << 5) | (b << 10);
        }

        colors[i] = color;
    }

    PaletteData_LoadBuffer(BattleSystem_GetPaletteData(banner->battleSys), colors, PLTTBUF_MAIN_OBJ, PLTT_DEST(banner->paletteSlot), sizeof(colors));
}

static void AbilityBanner_DrawMosaic(AbilityBanner *banner)
{
    int block = banner->mosaic + 1;
    u8 *pixelated = Heap_Alloc(HEAP_ID_BATTLE, ABILITY_BANNER_BYTES);

    for (int y = 0; y < ABILITY_BANNER_HEIGHT; y++) {
        for (int x = 0; x < ABILITY_BANNER_WIDTH; x++) {
            SetPixel(pixelated, x, y, GetPixel(banner->tiles, x - x % block, y - y % block));
        }
    }

    for (int column = 0; column < ABILITY_BANNER_WIDTH_TILES; column++) {
        AbilityBanner_CopyColumn(banner->sprite, pixelated, column);
    }

    Heap_Free(pixelated);
}

static BOOL AbilityBanner_IsChanging(void)
{
    for (int i = 0; i < 2; i++) {
        if (sAbilityBanners[i] != NULL && (sAbilityBanners[i]->changePending || sAbilityBanners[i]->state == ABILITY_BANNER_STATE_CHANGE)) {
            return TRUE;
        }
    }

    return FALSE;
}

static BOOL AbilityBanner_UpdateChange(AbilityBanner *banner, int step)
{
    switch (banner->changePhase) {
    case ABILITY_BANNER_CHANGE_PIXELATE: {
        int mosaic = banner->mosaic;
        banner->changeTimer += step;

        while (banner->changeTimer >= ABILITY_BANNER_MOSAIC_STEP_TIME && banner->mosaic < ABILITY_BANNER_MOSAIC_MAX) {
            banner->changeTimer -= ABILITY_BANNER_MOSAIC_STEP_TIME;
            banner->mosaic++;
        }

        if (banner->mosaic != mosaic) {
            AbilityBanner_DrawMosaic(banner);
        }

        if (banner->mosaic >= ABILITY_BANNER_MOSAIC_MAX) {
            banner->changePhase = ABILITY_BANNER_CHANGE_REDRAW;
        }
        break;
    }
    case ABILITY_BANNER_CHANGE_REDRAW: {
        String *line1, *line2;

        if (AbilityBanner_MakeLines(banner->battleSys, banner->owner, banner->changeAbility, &line1, &line2)) {
            AbilityBanner_Compose(banner->battleSys, banner->tiles, line1, line2, banner->side == 0);
            String_Free(line1);
            String_Free(line2);
        }

        AbilityBanner_DrawMosaic(banner);
        banner->changeTimer = 0;
        banner->changePhase = ABILITY_BANNER_CHANGE_UNPIXELATE;
        break;
    }
    case ABILITY_BANNER_CHANGE_UNPIXELATE: {
        int mosaic = banner->mosaic;
        banner->changeTimer += step;

        while (banner->changeTimer >= ABILITY_BANNER_MOSAIC_STEP_TIME && banner->mosaic > 0) {
            banner->changeTimer -= ABILITY_BANNER_MOSAIC_STEP_TIME;
            banner->mosaic--;
        }

        if (banner->mosaic != mosaic) {
            AbilityBanner_DrawMosaic(banner);
        }

        if (banner->mosaic == 0) {
            banner->changePhase = ABILITY_BANNER_CHANGE_WAIT_SOUND;
        }
        break;
    }
    case ABILITY_BANNER_CHANGE_WAIT_SOUND:
        if (AbilityBanner_AreSoundsLoadedFor(ABILITY_BANNER_SOUNDS_CHANGE) == FALSE || Sound_IsEffectPlaying(SEQ_SE_WB_DECIDE3_sseq) == FALSE) {
            return TRUE;
        }
        break;
    }

    return FALSE;
}

static void AbilityBanner_Task(SysTask *task, void *data)
{
    AbilityBanner *banner = data;
    s16 x, y;

    int step = gSystem.fps60 ? 1 : 2;

    ManagedSprite_GetPositionXY(banner->sprite, &x, &y);

    switch (banner->state) {
    case ABILITY_BANNER_STATE_SLIDE_IN:
        banner->x += banner->direction * ABILITY_BANNER_SLIDE_SPEED * step;

        if ((banner->direction > 0 && banner->x >= banner->restX) || (banner->direction < 0 && banner->x <= banner->restX)) {
            banner->x = banner->restX;
            banner->state = ABILITY_BANNER_STATE_WIPE;
            banner->wipeColumn = 0;
            banner->wipeFrames = 0;

            if (AbilityBanner_AreSoundsLoadedFor(ABILITY_BANNER_SOUNDS_INTRO)) {
                Sound_PlayEffect(SEQ_SE_WB_SHOOTER_sseq);
            }
        }
        break;
    case ABILITY_BANNER_STATE_WIPE:
        banner->wipeFrames += step;

        while (banner->wipeColumn < ABILITY_BANNER_WIDTH_TILES && banner->wipeColumn < banner->wipeFrames * ABILITY_BANNER_WIDTH_TILES / ABILITY_BANNER_WIPE_FRAMES) {
            AbilityBanner_CopyColumn(banner->sprite, banner->tiles, banner->wipeColumn);
            banner->wipeColumn++;
        }

        if (banner->wipeFrames >= ABILITY_BANNER_WIPE_FRAMES) {
            banner->state = ABILITY_BANNER_STATE_HOLD;
            banner->timer = 0;
        }
        break;
    case ABILITY_BANNER_STATE_CHANGE:
        if (AbilityBanner_UpdateChange(banner, step)) {
            banner->state = ABILITY_BANNER_STATE_HOLD;
            banner->ability = banner->changeAbility;
            banner->timeout = ABILITY_BANNER_WAIT_FOR_MESSAGE_FRAMES;
            banner->lingerFrames = 0;
        }
        break;
    case ABILITY_BANNER_STATE_HOLD:
        if (banner->changePending && banner->timer >= ABILITY_BANNER_HOLD_FRAMES) {
            banner->changePending = FALSE;
            banner->state = ABILITY_BANNER_STATE_CHANGE;
            banner->changePhase = ABILITY_BANNER_CHANGE_PIXELATE;
            banner->changeTimer = 0;
            banner->mosaic = 0;

            if (AbilityBanner_AreSoundsLoadedFor(ABILITY_BANNER_SOUNDS_CHANGE)) {
                Sound_PlayEffect(SEQ_SE_WB_DECIDE3_sseq);
            }
            break;
        }

        if (banner->flashStarted == FALSE && banner->timer >= ABILITY_BANNER_FLASH_DELAY) {
            banner->flashStarted = TRUE;

            if (AbilityBanner_AreSoundsLoadedFor(ABILITY_BANNER_SOUNDS_INTRO)) {
                Sound_PlayEffect(SEQ_SE_WB_DECIDE2_sseq);
            }
        }

        if (banner->timer >= ABILITY_BANNER_FLASH_DELAY && banner->timer <= ABILITY_BANNER_FLASH_DELAY + ABILITY_BANNER_FLASH_FRAMES) {
            AbilityBanner_SetFlash(banner, 16 - 16 * (banner->timer - ABILITY_BANNER_FLASH_DELAY) / ABILITY_BANNER_FLASH_FRAMES);
        }

        if (banner->timer < ABILITY_BANNER_HOLD_FRAMES) {
            banner->timer += step;
        }

        if (banner->msgIdx == ABILITY_BANNER_NO_MESSAGE) {
            banner->timeout = banner->timeout > step ? banner->timeout - step : 0;

            if (banner->timeout == 0 && banner->timer >= ABILITY_BANNER_HOLD_FRAMES) {
                AbilityBanner_Free(banner);
                return;
            }
        } else if (banner->printed == FALSE && (banner->messageGone || Text_IsPrinterActive(banner->msgIdx) == FALSE)) {
            banner->printed = TRUE;
        }

        if (banner->msgIdx != ABILITY_BANNER_NO_MESSAGE && banner->printed && banner->timer >= ABILITY_BANNER_HOLD_FRAMES) {
            banner->lingerFrames += step;

            if (banner->messageGone || banner->lingerFrames >= ABILITY_BANNER_LINGER_FRAMES) {
                for (int i = 0; i < 2; i++) {
                    if (sAbilityBanners[i] != NULL && sAbilityBanners[i] != banner && sAbilityBanners[i]->msgIdx == ABILITY_BANNER_NO_MESSAGE
                        && sAbilityBanners[i]->order < banner->order) {
                        AbilityBanner_Free(sAbilityBanners[i]);
                    }
                }

                AbilityBanner_Free(banner);
                return;
            }
        }
        break;
    }

    ManagedSprite_SetPositionXY(banner->sprite, banner->x, y);
}

void AbilityBanner_OnMessage(const BattleMessage *battleMsg)
{
    int owner, ability;

    for (int i = 0; i < 2; i++) {
        AbilityBanner *banner = sAbilityBanners[i];

        if (banner == NULL || banner->msgIdx == ABILITY_BANNER_NO_MESSAGE) {
            continue;
        }

        if (AbilityBanner_GetOwnerAndAbility(battleMsg, &owner, &ability) && banner->owner == (owner & 0xFFFF)) {
            banner->lingerFrames = 0;
            continue;
        }

        banner->messageGone = TRUE;
    }
}

void AbilityBanner_OnMessageBoxCleared(void)
{
    for (int i = 0; i < 2; i++) {
        if (sAbilityBanners[i] != NULL && sAbilityBanners[i]->msgIdx != ABILITY_BANNER_NO_MESSAGE) {
            sAbilityBanners[i]->messageGone = TRUE;
        }
    }
}

void AbilityBanner_AttachMessage(u8 msgIdx)
{
    if (sLastBanner != NULL && sLastBanner->msgIdx == ABILITY_BANNER_NO_MESSAGE) {
        sLastBanner->msgIdx = msgIdx;
        sLastBanner->printed = FALSE;
    }
}

BOOL AbilityBanner_IsHideMessage(const BattleMessage *battleMsg)
{
    return battleMsg->id == BattleStrings_Text_AbilityBannerHide;
}

void AbilityBanner_Hide(void)
{
    for (int i = 0; i < 2; i++) {
        if (sAbilityBanners[i] == NULL) {
            continue;
        }

        if (sAbilityBanners[i]->msgIdx == ABILITY_BANNER_NO_MESSAGE) {
            sAbilityBanners[i]->timeout = 0;
        } else {
            sAbilityBanners[i]->messageGone = TRUE;
        }
    }
}

void AbilityBanner_FreeAll(void)
{
    for (int i = 0; i < 2; i++) {
        if (sAbilityBanners[i] != NULL) {
            AbilityBanner_Free(sAbilityBanners[i]);
        }
    }
}

BOOL AbilityBanner_CanShow(void)
{
    return sAbilityBanners[0] != NULL || sAbilityBanners[1] != NULL || PlttTransfer_HasFreeSpace(1, NNS_G2D_VRAM_TYPE_2DMAIN);
}

BOOL AbilityBanner_IsIntroPlaying(void)
{
    BOOL banners = FALSE;

    if (AbilityBanner_IsChanging()) {
        return TRUE;
    }

    for (int i = 0; i < 2; i++) {
        AbilityBanner *banner = sAbilityBanners[i];

        if (banner == NULL) {
            continue;
        }

        if (banner->state != ABILITY_BANNER_STATE_HOLD || banner->timer <= ABILITY_BANNER_FLASH_DELAY + ABILITY_BANNER_FLASH_FRAMES) {
            return TRUE;
        }

        banners = TRUE;
    }

    if (banners == FALSE) {
        return FALSE;
    }

    return AbilityBanner_AreSoundsLoadedFor(ABILITY_BANNER_SOUNDS_INTRO) && (Sound_IsEffectPlaying(SEQ_SE_WB_SHOOTER_sseq) || Sound_IsEffectPlaying(SEQ_SE_WB_DECIDE2_sseq));
}

static void AbilityBanner_Free(AbilityBanner *banner)
{
    SpriteManager *spriteMan = BattleSystem_GetSpriteManager(banner->battleSys);

    Sprite_DeleteAndFreeResources(banner->sprite);
    Heap_Free(banner->tiles);
    SpriteManager_UnloadCharObjById(spriteMan, ABILITY_BANNER_RESID_CHAR(banner->side));
    SpriteManager_UnloadPlttObjById(spriteMan, ABILITY_BANNER_RESID_PLTT(banner->side));
    SpriteManager_UnloadCellObjById(spriteMan, ABILITY_BANNER_RESID_CELL(banner->side));
    SpriteManager_UnloadAnimObjById(spriteMan, ABILITY_BANNER_RESID_ANIM(banner->side));
    SysTask_Done(banner->task);

    if (sAbilityBanners[banner->side] == banner) {
        sAbilityBanners[banner->side] = NULL;
    }

    if (sLastBanner == banner) {
        sLastBanner = NULL;
    }

    if (sAbilityBanners[0] == NULL && sAbilityBanners[1] == NULL) {
        AbilityBanner_FreeSounds();
    }

    Heap_Free(banner);
}
