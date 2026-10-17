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
#include "sys_task.h"
#include "sys_task_manager.h"
#include "text.h"

#include "res/graphics/battle/ability_banner/banner.4bpp.h"
#include "res/graphics/battle/sprites.naix"
#include "res/text/bank/battle_strings.h"

// Resource IDs of the sprite resources while the banner is showing
#define ABILITY_BANNER_RESID_CHAR 21100
#define ABILITY_BANNER_RESID_PLTT 21101
#define ABILITY_BANNER_RESID_CELL 21102
#define ABILITY_BANNER_RESID_ANIM 21103

#define ABILITY_BANNER_WIDTH_TILES  16
#define ABILITY_BANNER_HEIGHT_TILES 4
#define ABILITY_BANNER_WIDTH        (ABILITY_BANNER_WIDTH_TILES * 8)
#define ABILITY_BANNER_HEIGHT       (ABILITY_BANNER_HEIGHT_TILES * 8)
#define ABILITY_BANNER_TILE_SIZE    32
#define ABILITY_BANNER_BYTES        (ABILITY_BANNER_WIDTH_TILES * ABILITY_BANNER_HEIGHT_TILES * ABILITY_BANNER_TILE_SIZE)

// banner.png has the art of the player side on top and that of the enemy side below it. The banner of the player is open
// on its left side and rests against the left edge of the screen; the banner of the enemy is open on its right side and
// rests against the right edge, like in Black and White.
#define ABILITY_BANNER_ART_PLAYER 0
#define ABILITY_BANNER_ART_ENEMY  1

// Position of the center of the banner on the top screen
#define ABILITY_BANNER_PLAYER_X        64
#define ABILITY_BANNER_PLAYER_Y        124
#define ABILITY_BANNER_ENEMY_X         192
#define ABILITY_BANNER_ENEMY_Y         60
#define ABILITY_BANNER_OFFSCREEN_DX    128 // how far from its resting position the banner starts
#define ABILITY_BANNER_SLIDE_SPEED     16
#define ABILITY_BANNER_HOLD_FRAMES     45 // the banner stays at least this long
#define ABILITY_BANNER_FLASH_DELAY     2 // frames between the end of the slide and the flash
#define ABILITY_BANNER_FLASH_FRAMES    15 // the flash goes from white back to the colors of the banner in 0.5 seconds
#define ABILITY_BANNER_SPRITE_PRIORITY 10

// A banner that is shown before the effect of an ability (see BattleStrings_Text_AbilityBanner) waits for the message
// of the ability, however long the effect takes. If none comes at all, it goes away after this long.
#define ABILITY_BANNER_WAIT_FOR_MESSAGE_FRAMES 600

// Palette indexes of banner.png
#define ABILITY_BANNER_COLOR_TEXT        1
#define ABILITY_BANNER_COLOR_SHADOW      2
#define ABILITY_BANNER_FIRST_FLASH_COLOR 3 // the colors of the text don't flash
#define ABILITY_BANNER_COLOR_KEY         15 // not used by the art; marks the pixels around the text, which let the art through

// The name starts at the left of the text and the ability ends at its right (under the end of a longer name), and
// together they are centered on the bar of the art: x 0-106 on the player banner, 20-127 on the enemy banner
#define ABILITY_BANNER_PLAYER_TEXT_CENTER 53
#define ABILITY_BANNER_TEXT_STAGGER       16 // the ability starts at least this far right of the name
#define ABILITY_BANNER_ENEMY_TEXT_CENTER  74
#define ABILITY_BANNER_LINE_1_Y    6
#define ABILITY_BANNER_LINE_2_Y    18

enum AbilityBannerState {
    ABILITY_BANNER_STATE_SLIDE_IN = 0,
    ABILITY_BANNER_STATE_HOLD,
};

typedef struct AbilityBanner {
    BattleSystem *battleSys;
    SysTask *task;
    ManagedSprite *sprite;
    u8 state;
    u8 timer;
    u8 msgIdx; // the banner stays until this text printer is done, or ABILITY_BANNER_NO_MESSAGE
    u8 paletteSlot;
    u16 timeout; // frames until the banner goes away when it has no message
    int owner; // battler and party slot of the Pokemon, as in the message tags; -1 for other banners
    s16 restX;
    s16 x;
    s16 direction; // 1 when the banner slides in from the left, -1 when it slides in from the right
    u16 colors[PALETTE_SIZE]; // the colors of the banner, to fade back to after the flash
} AbilityBanner;

static AbilityBanner *sAbilityBanner = NULL;

// The sounds of the banner are loaded into the sound heap while it is showing and freed after it, so that they don't
// take room from the battle music (the trainer music does not fit next to them)
static BOOL sSoundsLoaded = FALSE;
static int sSoundHeapState;
static u32 sSoundHeapFreeSize;

static BOOL AbilityBanner_AreSoundsLoaded(void);

static void AbilityBanner_LoadSounds(void)
{
    if (AbilityBanner_AreSoundsLoaded()) {
        return;
    }

    NNSSndHeapHandle heap = SoundSystem_Get()->heap;
    u32 flags = NNS_SND_ARC_LOAD_SEQ | NNS_SND_ARC_LOAD_BANK | NNS_SND_ARC_LOAD_WAVE;

    sSoundHeapState = NNS_SndHeapSaveState(heap);

    if (sSoundHeapState == SOUND_HEAP_STATE_INVALID) {
        return;
    }

    // Without room the banner is silent
    if (SoundSystem_LoadSequenceEx(SEQ_SE_WB_SHOOTER_sseq, flags) == FALSE || SoundSystem_LoadSequenceEx(SEQ_SE_WB_DECIDE2_sseq, flags) == FALSE) {
        SoundSystem_LoadHeapState(sSoundHeapState - 1);
        return;
    }

    sSoundHeapFreeSize = NNS_SndHeapGetFreeSize(heap);
    sSoundsLoaded = TRUE;
}

// FALSE if something reset the sound heap below the sounds of the banner (the music of a new scene), which frees them
static BOOL AbilityBanner_AreSoundsLoaded(void)
{
    if (sSoundsLoaded && NNS_SndHeapGetCurrentLevel(SoundSystem_Get()->heap) < sSoundHeapState) {
        sSoundsLoaded = FALSE;
    }

    return sSoundsLoaded;
}

static void AbilityBanner_FreeSounds(void)
{
    if (!AbilityBanner_AreSoundsLoaded()) {
        return;
    }

    NNSSndHeapHandle heap = SoundSystem_Get()->heap;

    Sound_StopEffect(SEQ_SE_WB_SHOOTER_sseq, 0);
    Sound_StopEffect(SEQ_SE_WB_DECIDE2_sseq, 0);

    // Only when nothing was loaded after them; otherwise they stay until the heap is reset at the end of the battle
    if (NNS_SndHeapGetCurrentLevel(heap) == sSoundHeapState && NNS_SndHeapGetFreeSize(heap) == sSoundHeapFreeSize) {
        SoundSystem_LoadHeapState(sSoundHeapState - 1);
    }

    sSoundsLoaded = FALSE;
}

static void AbilityBanner_Task(SysTask *task, void *data);
static void AbilityBanner_Free(AbilityBanner *banner);
static BOOL AbilityBanner_GetOwnerAndAbility(const BattleMessage *battleMsg, int *owner, int *ability);
static AbilityBanner *AbilityBanner_New(BattleSystem *battleSys, const String *line1, const String *line2, BOOL isPlayerSide);
static void AbilityBanner_Draw(BattleSystem *battleSys, ManagedSprite *sprite, const String *line1, const String *line2, BOOL isPlayerSide);

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
    case TAG_NICKNAME_NICKNAME_ABILITY:
        *owner = battleMsg->params[1];
        *ability = battleMsg->params[2];
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
    return battleMsg->id == BattleStrings_Text_AbilityBanner && AbilityBanner_MessageNamesAbility(battleMsg);
}

void AbilityBanner_TryShow(BattleSystem *battleSys, const BattleMessage *battleMsg, u8 msgIdx)
{
    int owner, ability;

    if (AbilityBanner_GetOwnerAndAbility(battleMsg, &owner, &ability) == FALSE || ability <= 0) {
        return;
    }

    BOOL bannerOnly = (msgIdx == ABILITY_BANNER_NO_MESSAGE);

    // The banner was already shown before the effect of the ability: it stays until this message is done
    if (sAbilityBanner != NULL && sAbilityBanner->owner == (owner & 0xFFFF)) {
        if (bannerOnly) {
            sAbilityBanner->timeout = ABILITY_BANNER_WAIT_FOR_MESSAGE_FRAMES;
        } else {
            sAbilityBanner->msgIdx = msgIdx;
        }

        return;
    }

    int battler = owner & 0xFF;
    int partySlot = (owner >> 8) & 0xFF;
    Pokemon *mon = BattleSystem_GetPartyPokemon(battleSys, battler, partySlot);

    if (mon == NULL) {
        return;
    }

    MessageLoader *msgLoader = BattleSystem_GetMessageLoader(battleSys);
    StringTemplate *strFormatter = BattleSystem_GetStringTemplate(battleSys);

    StringTemplate_SetNickname(strFormatter, 0, Pokemon_GetBoxPokemon(mon));
    StringTemplate_SetAbilityName(strFormatter, 1, ability);

    String *ownerString = String_Init(MON_NAME_LEN + 12, HEAP_ID_BATTLE);
    String *abilityString = String_Init(MON_NAME_LEN + 12, HEAP_ID_BATTLE);
    String *ownerTemplate = MessageLoader_GetNewString(msgLoader, BattleStrings_Text_AbilityBannerOwner);
    String *abilityTemplate = MessageLoader_GetNewString(msgLoader, BattleStrings_Text_AbilityBannerAbility);

    StringTemplate_Format(strFormatter, ownerString, ownerTemplate);
    StringTemplate_Format(strFormatter, abilityString, abilityTemplate);

    AbilityBanner *banner = AbilityBanner_New(battleSys, ownerString, abilityString, BattleSystem_GetBattlerSide(battleSys, battler) == 0);

    if (banner != NULL) {
        banner->owner = owner & 0xFFFF;

        if (bannerOnly) {
            banner->msgIdx = ABILITY_BANNER_NO_MESSAGE;
            banner->timeout = ABILITY_BANNER_WAIT_FOR_MESSAGE_FRAMES;
        } else {
            banner->msgIdx = msgIdx;
        }
    }

    String_Free(ownerTemplate);
    String_Free(abilityTemplate);
    String_Free(ownerString);
    String_Free(abilityString);
}

static AbilityBanner *AbilityBanner_New(BattleSystem *battleSys, const String *line1, const String *line2, BOOL isPlayerSide)
{
    if (sAbilityBanner != NULL) {
        AbilityBanner_Free(sAbilityBanner);
    }

    // Without room for the palette there is no banner, the message is enough
    if (PlttTransfer_HasFreeSpace(1, NNS_G2D_VRAM_TYPE_2DMAIN) == FALSE) {
        return NULL;
    }

    SpriteSystem *spriteSys = BattleSystem_GetSpriteSystem(battleSys);
    SpriteManager *spriteMan = BattleSystem_GetSpriteManager(battleSys);
    PaletteData *paletteData = BattleSystem_GetPaletteData(battleSys);
    NARC *narc = NARC_ctor(NARC_INDEX_BATTLE__GRAPHIC__PL_BATT_OBJ, HEAP_ID_BATTLE);

    // The palette goes into the palette buffer too, because the battle copies the buffer to the screen every frame
    SpriteSystem_LoadCharResObjFromOpenNarc(spriteSys, spriteMan, narc, ability_banner_banner_NCGR_lz, TRUE, NNS_G2D_VRAM_TYPE_2DMAIN, ABILITY_BANNER_RESID_CHAR);
    u8 paletteSlot = SpriteSystem_LoadPaletteBufferFromOpenNarc(paletteData, PLTTBUF_MAIN_OBJ, spriteSys, spriteMan, narc, ability_banner_banner_NCLR, FALSE, 1, NNS_G2D_VRAM_TYPE_2DMAIN, ABILITY_BANNER_RESID_PLTT);
    SpriteSystem_LoadCellResObjFromOpenNarc(spriteSys, spriteMan, narc, ability_banner_banner_cell_NCER_lz, TRUE, ABILITY_BANNER_RESID_CELL);
    SpriteSystem_LoadAnimResObjFromOpenNarc(spriteSys, spriteMan, narc, misc_single_frame_anim_NANR_lz_5, TRUE, ABILITY_BANNER_RESID_ANIM);
    NARC_dtor(narc);

    AbilityBanner *banner = Heap_Alloc(HEAP_ID_BATTLE, sizeof(AbilityBanner));
    memset(banner, 0, sizeof(AbilityBanner));

    banner->battleSys = battleSys;
    banner->state = ABILITY_BANNER_STATE_SLIDE_IN;
    banner->msgIdx = ABILITY_BANNER_NO_MESSAGE;
    banner->owner = -1;
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
            ABILITY_BANNER_RESID_CHAR,
            ABILITY_BANNER_RESID_PLTT,
            ABILITY_BANNER_RESID_CELL,
            ABILITY_BANNER_RESID_ANIM,
            SPRITE_RESOURCE_NONE,
            SPRITE_RESOURCE_NONE,
        },
        .bgPriority = 0,
        .vramTransfer = FALSE,
    };

    banner->sprite = SpriteSystem_NewSprite(spriteSys, spriteMan, &template);
    AbilityBanner_Draw(battleSys, banner->sprite, line1, line2, isPlayerSide);

    banner->task = SysTask_Start(AbilityBanner_Task, banner, 0);
    sAbilityBanner = banner;

    // The sounds of the ability window of Black and White: one as it slides in, one as it flashes
    AbilityBanner_LoadSounds();

    if (sSoundsLoaded) {
        Sound_PlayEffect(SEQ_SE_WB_SHOOTER_sseq);
    }

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

static void AbilityBanner_Draw(BattleSystem *battleSys, ManagedSprite *sprite, const String *line1, const String *line2, BOOL isPlayerSide)
{
    BgConfig *bgConfig = BattleSystem_GetBgConfig(battleSys);
    Window window, textWindow;

    // The art goes into a window, and the text is printed into a second one whose background is a color that the art
    // does not use. Only the pixels of the letters are copied over the art.
    Window_AddToTopLeftCorner(bgConfig, &window, ABILITY_BANNER_WIDTH_TILES, ABILITY_BANNER_HEIGHT_TILES, 0, 0);
    Window_AddToTopLeftCorner(bgConfig, &textWindow, ABILITY_BANNER_WIDTH_TILES, ABILITY_BANNER_HEIGHT_TILES, 0, ABILITY_BANNER_COLOR_KEY);

    const u8 *art = &sAbilityBannerBitmap[(isPlayerSide ? ABILITY_BANNER_ART_PLAYER : ABILITY_BANNER_ART_ENEMY) * ABILITY_BANNER_BYTES];

    MI_CpuCopy16(art, window.pixels, ABILITY_BANNER_BYTES);

    TextColor textColor = TEXT_COLOR(ABILITY_BANNER_COLOR_TEXT, ABILITY_BANNER_COLOR_SHADOW, ABILITY_BANNER_COLOR_KEY);
    int line1Width = Font_CalcStringWidth(FONT_SYSTEM, line1, 0);
    int line2Width = Font_CalcStringWidth(FONT_SYSTEM, line2, 0);
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

    Text_AddPrinterWithParamsColorAndSpacing(&textWindow, FONT_SYSTEM, line1, line1X, ABILITY_BANNER_LINE_1_Y, TEXT_SPEED_NO_TRANSFER, textColor, 0, 0, NULL);
    Text_AddPrinterWithParamsColorAndSpacing(&textWindow, FONT_SYSTEM, line2, line2X, ABILITY_BANNER_LINE_2_Y, TEXT_SPEED_NO_TRANSFER, textColor, 0, 0, NULL);

    for (int y = 0; y < ABILITY_BANNER_HEIGHT; y++) {
        for (int x = 0; x < ABILITY_BANNER_WIDTH; x++) {
            u8 color = GetPixel(textWindow.pixels, x, y);

            if (color != ABILITY_BANNER_COLOR_KEY) {
                SetPixel(window.pixels, x, y, color);
            }
        }
    }

    // The window has its tiles in rows of 16, the sprite is two parts of 8x4 tiles
    NNSG2dImageProxy *imgProxy = Sprite_GetImageProxy(sprite->sprite);
    u8 *dst = (u8 *)G2_GetOBJCharPtr() + imgProxy->vramLocation.baseAddrOfVram[NNS_G2D_VRAM_TYPE_2DMAIN];
    u8 *src = window.pixels;
    int partTiles = ABILITY_BANNER_WIDTH_TILES / 2;

    for (int part = 0; part < 2; part++) {
        for (int row = 0; row < ABILITY_BANNER_HEIGHT_TILES; row++) {
            MI_CpuCopy16(
                &src[(row * ABILITY_BANNER_WIDTH_TILES + part * partTiles) * ABILITY_BANNER_TILE_SIZE],
                &dst[(part * partTiles * ABILITY_BANNER_HEIGHT_TILES + row * partTiles) * ABILITY_BANNER_TILE_SIZE],
                partTiles * ABILITY_BANNER_TILE_SIZE);
        }
    }

    Window_Remove(&textWindow);
    Window_Remove(&window);
}

// fraction: 16 is white, 0 is the colors of the art
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

static void AbilityBanner_Task(SysTask *task, void *data)
{
    AbilityBanner *banner = data;
    s16 x, y;

    ManagedSprite_GetPositionXY(banner->sprite, &x, &y);

    switch (banner->state) {
    case ABILITY_BANNER_STATE_SLIDE_IN:
        banner->x += banner->direction * ABILITY_BANNER_SLIDE_SPEED;

        if ((banner->direction > 0 && banner->x >= banner->restX) || (banner->direction < 0 && banner->x <= banner->restX)) {
            banner->x = banner->restX;
            banner->state = ABILITY_BANNER_STATE_HOLD;
            banner->timer = 0;
        }
        break;
    case ABILITY_BANNER_STATE_HOLD:
        if (banner->timer == ABILITY_BANNER_FLASH_DELAY && AbilityBanner_AreSoundsLoaded()) {
            Sound_PlayEffect(SEQ_SE_WB_DECIDE2_sseq);
        }

        if (banner->timer >= ABILITY_BANNER_FLASH_DELAY && banner->timer <= ABILITY_BANNER_FLASH_DELAY + ABILITY_BANNER_FLASH_FRAMES) {
            AbilityBanner_SetFlash(banner, 16 - 16 * (banner->timer - ABILITY_BANNER_FLASH_DELAY) / ABILITY_BANNER_FLASH_FRAMES);
        }

        if (banner->timer < ABILITY_BANNER_HOLD_FRAMES) {
            banner->timer++;
        }

        // Once its message is done the banner disappears. A banner without a message waits for one for a while.
        if (banner->msgIdx == ABILITY_BANNER_NO_MESSAGE) {
            if (banner->timeout > 0) {
                banner->timeout--;
            }

            if (banner->timeout == 0 && banner->timer >= ABILITY_BANNER_HOLD_FRAMES) {
                AbilityBanner_Free(banner);
                return;
            }
        } else if (banner->timer >= ABILITY_BANNER_HOLD_FRAMES && Text_IsPrinterActive(banner->msgIdx) == FALSE) {
            AbilityBanner_Free(banner);
            return;
        }
        break;
    }

    ManagedSprite_SetPositionXY(banner->sprite, banner->x, y);
}

BOOL AbilityBanner_IsIntroPlaying(void)
{
    AbilityBanner *banner = sAbilityBanner;

    if (banner == NULL) {
        return FALSE;
    }

    if (banner->state == ABILITY_BANNER_STATE_SLIDE_IN || banner->timer <= ABILITY_BANNER_FLASH_DELAY + ABILITY_BANNER_FLASH_FRAMES) {
        return TRUE;
    }

    return AbilityBanner_AreSoundsLoaded() && (Sound_IsEffectPlaying(SEQ_SE_WB_SHOOTER_sseq) || Sound_IsEffectPlaying(SEQ_SE_WB_DECIDE2_sseq));
}

static void AbilityBanner_Free(AbilityBanner *banner)
{
    SpriteManager *spriteMan = BattleSystem_GetSpriteManager(banner->battleSys);

    Sprite_DeleteAndFreeResources(banner->sprite);
    SpriteManager_UnloadCharObjById(spriteMan, ABILITY_BANNER_RESID_CHAR);
    SpriteManager_UnloadPlttObjById(spriteMan, ABILITY_BANNER_RESID_PLTT);
    SpriteManager_UnloadCellObjById(spriteMan, ABILITY_BANNER_RESID_CELL);
    SpriteManager_UnloadAnimObjById(spriteMan, ABILITY_BANNER_RESID_ANIM);
    SysTask_Done(banner->task);
    AbilityBanner_FreeSounds();

    if (sAbilityBanner == banner) {
        sAbilityBanner = NULL;
    }

    Heap_Free(banner);
}
