#include "savedata.h"

#include <nitro.h>
#include <string.h>

#include "constants/heap.h"

#include "savedata/save_table.h"

#include "heap.h"
#include "inlines.h"
#include "math_util.h"
#include "play_time_manager.h"
#include "savedata_misc.h"
#include "system.h"
#include "unk_0209A74C.h"
#include "unk_0209AA74.h"

static void SaveTable_Clear(SaveDataBody *body, const SavePageInfo *pageInfo);
static void SavePageInfo_Init(SavePageInfo *pageInfo);
static void SaveBlockInfo_Init(SaveBlockInfo *blockInfo, const SavePageInfo *pageInfo);
static BOOL SaveDataState_Save(SaveData *saveData);
static BOOL SaveDataState_Load(SaveData *saveData);
static int SaveData_LoadCheck(SaveData *saveData);
static void SaveDataExtra_LoadCheck(SaveData *saveData, int *frontierResult, int *videoResult);
static void SaveDataState_Init(SaveData *saveData, SaveDataState *state, int blockID);
static int SaveDataState_Main(SaveData *saveData, SaveDataState *state);
static void SaveDataState_End(SaveData *saveData, SaveDataState *state, int saveResult);
static void SaveDataState_Cancel(SaveData *saveData, SaveDataState *state);
static BOOL SaveBlockFooter_Erase(const SaveData *saveData, int blockID, int sectorID);
static s32 SaveData_CardSave_Init(u32 address, void *data, u32 size);
static BOOL SaveData_CardSave_Main(s32 lockID, BOOL lockFlag, BOOL *result);
static void SaveData_CardSave_Error(s32 lockID, int errorID);
static void SaveDataExtra_SaveKey(SaveData *saveData, int extraSaveID, u32 *returnKey, u32 *oldKey, u8 *keyFlag);
static void SaveDataExtra_SetSaveKey(SaveData *saveData, int extraSaveID, u32 newKey, u32 oldKey, u8 keyFlag);

static SaveData *sSaveDataPtr = NULL;
static BOOL sSaveComplete;

#define SAVE_COMPARE_PAGE_SIZE 256
#define SAVE_COMPARE_BUDGET    0x1000
#define SAVE_WRITE_RUN_MAX     0x8000
#define SAVE_DIRTY_PAGES_MAX   (SAVE_SECTOR_SIZE * SAVE_PAGE_MAX / SAVE_COMPARE_PAGE_SIZE + SAVE_BLOCK_ID_MAX)

enum SaveSequence {
    SAVE_SEQ_BLOCK_START = 0,
    SAVE_SEQ_COMPARE,
    SAVE_SEQ_WRITE_WAIT,
    SAVE_SEQ_FOOTER_CHECK,
    SAVE_SEQ_FOOTER,
    SAVE_SEQ_BLOCK_DONE,
};

static u32 sComparePage[SAVE_COMPARE_PAGE_SIZE / sizeof(u32)];
static u8 sDirtyPages[(SAVE_DIRTY_PAGES_MAX + 7) / 8];
static BOOL sSlotsInSync[SAVE_BLOCK_ID_MAX];

SaveData *SaveData_Init(void)
{
    SaveData *saveData = Heap_Alloc(HEAP_ID_SAVE, sizeof(SaveData));
    ;

    MI_CpuClearFast(saveData, sizeof(SaveData));

    sSaveDataPtr = saveData;

    saveData->backupExists = SaveData_CardBackupType();
    saveData->dataExists = FALSE;
    saveData->isNewGameData = TRUE;
    saveData->fullSaveRequired = TRUE;

    SavePageInfo_Init(saveData->pageInfo);
    SaveBlockInfo_Init(saveData->blockInfo, saveData->pageInfo);

    MI_CpuClearFast(saveData->blockCounters, sizeof(saveData->blockCounters));

    int loadResult = SaveData_LoadCheck(saveData);

    saveData->loadCheckStatus = 0;

    switch (loadResult) {
    case LOAD_RESULT_OK:
        saveData->fullSaveRequired = FALSE;
    case LOAD_RESULT_CORRUPT:
        SaveDataState_Load(saveData);

        saveData->dataExists = TRUE;
        saveData->isNewGameData = FALSE;

        if (loadResult == LOAD_RESULT_CORRUPT) {
            saveData->loadCheckStatus |= NORMAL_LOAD_CORRUPT;
        }

        int frontierResult, videoResult;

        SaveDataExtra_LoadCheck(saveData, &frontierResult, &videoResult);

        if (frontierResult == LOAD_RESULT_ERROR) {
            saveData->loadCheckStatus |= FRONTIER_LOAD_ERROR;
        } else if (frontierResult == LOAD_RESULT_CORRUPT) {
            saveData->loadCheckStatus |= FRONTIER_LOAD_CORRUPT;
        }

        if (videoResult == LOAD_RESULT_ERROR) {
            saveData->loadCheckStatus |= VIDEO_LOAD_ERROR;
        } else if (videoResult == LOAD_RESULT_CORRUPT) {
            saveData->loadCheckStatus |= VIDEO_LOAD_CORRUPT;
        }
        break;
    case LOAD_RESULT_ERROR:
        saveData->loadCheckStatus |= NORMAL_LOAD_ERROR;
    case LOAD_RESULT_EMPTY:
        SaveData_Clear(saveData);
        break;
    }

    return saveData;
}

SaveData *SaveData_Ptr(void)
{
    GF_ASSERT(sSaveDataPtr != NULL);
    return sSaveDataPtr;
}

void *SaveData_SaveTable(SaveData *saveData, int saveTableID)
{
    GF_ASSERT(saveTableID < SAVE_TABLE_ENTRY_MAX);
    return &(saveData->body.data[saveData->pageInfo[saveTableID].location]);
}

const void *SaveData_SaveTableConst(const SaveData *saveData, int saveTableID)
{
    return SaveData_SaveTable(saveData, saveTableID);
}

BOOL SaveData_Erase(SaveData *saveData)
{
    u8 *saveBuffer = Heap_AllocAtEnd(HEAP_ID_APPLICATION, SAVE_SECTOR_SIZE);

    SleepLock(SLEEP_TYPE_SAVE_DATA);

    SaveBlockFooter_Erase(saveData, SAVE_BLOCK_ID_NORMAL, !saveData->blockOffsets[SAVE_BLOCK_ID_NORMAL]);
    SaveBlockFooter_Erase(saveData, SAVE_BLOCK_ID_BOXES, !saveData->blockOffsets[SAVE_BLOCK_ID_BOXES]);
    SaveBlockFooter_Erase(saveData, SAVE_BLOCK_ID_NORMAL, saveData->blockOffsets[SAVE_BLOCK_ID_NORMAL]);
    SaveBlockFooter_Erase(saveData, SAVE_BLOCK_ID_BOXES, saveData->blockOffsets[SAVE_BLOCK_ID_BOXES]);

    MI_CpuFillFast(saveBuffer, 0xffffffff, SAVE_SECTOR_SIZE);

    for (int i = 0; i < SAVE_PAGE_MAX * SECTOR_ID_MAX; i++) {
        SaveData_CardSave(SAVE_SECTOR_SIZE * (i + PRIMARY_SECTOR_START), saveBuffer, SAVE_SECTOR_SIZE);
        SaveData_CardSave(SAVE_SECTOR_SIZE * (i + BACKUP_SECTOR_START), saveBuffer, SAVE_SECTOR_SIZE);
    }

    Heap_Free(saveBuffer);
    SaveData_Clear(saveData);

    for (int i = 0; i < SAVE_BLOCK_ID_MAX; i++) {
        sSlotsInSync[i] = TRUE;
    }

    saveData->dataExists = FALSE;
    SleepUnlock(SLEEP_TYPE_SAVE_DATA);

    return TRUE;
}

BOOL SaveData_Load(SaveData *saveData)
{
    if (!saveData->backupExists) {
        return FALSE;
    }

    BOOL loadSucceeded = SaveDataState_Load(saveData);

    if (loadSucceeded) {
        saveData->dataExists = TRUE;
        saveData->isNewGameData = FALSE;

        int frontierResult, videoResult;
        SaveDataExtra_LoadCheck(saveData, &frontierResult, &videoResult);
        return TRUE;
    }

    return FALSE;
}

static void SaveData_EraseForNewGame(SaveData *saveData)
{
    if (saveData->isNewGameData) {
        SleepLock(SLEEP_TYPE_SAVE_DATA);

        SaveBlockFooter_Erase(saveData, SAVE_BLOCK_ID_NORMAL, !saveData->blockOffsets[SAVE_BLOCK_ID_NORMAL]);
        SaveBlockFooter_Erase(saveData, SAVE_BLOCK_ID_BOXES, !saveData->blockOffsets[SAVE_BLOCK_ID_BOXES]);
        SaveBlockFooter_Erase(saveData, SAVE_BLOCK_ID_NORMAL, saveData->blockOffsets[SAVE_BLOCK_ID_NORMAL]);
        SaveBlockFooter_Erase(saveData, SAVE_BLOCK_ID_BOXES, saveData->blockOffsets[SAVE_BLOCK_ID_BOXES]);

        for (int i = 0; i < SAVE_BLOCK_ID_MAX; i++) {
            sSlotsInSync[i] = FALSE;
        }

        SleepUnlock(SLEEP_TYPE_SAVE_DATA);
    }
}

int SaveData_Save(SaveData *saveData)
{
    if (!saveData->backupExists) {
        return SAVE_RESULT_CORRUPT;
    }

    SaveData_EraseForNewGame(saveData);

    int saveResult = SaveDataState_Save(saveData);

    if (saveResult == SAVE_RESULT_OK) {
        saveData->dataExists = TRUE;
        saveData->isNewGameData = FALSE;
    }

    return saveResult;
}

int SaveData_SaveBlock(SaveData *saveData, int saveBlockID)
{
    GF_ASSERT(saveBlockID < SAVE_BLOCK_ID_MAX);
    GF_ASSERT(saveData->isNewGameData == FALSE);
    GF_ASSERT(saveData->dataExists == TRUE);

    SaveData_SaveStateInit(saveData, saveBlockID);

    int saveResult;
    do {
        saveResult = SaveData_SaveStateMain(saveData);
    } while (saveResult == SAVE_RESULT_PROCEED || saveResult == SAVE_RESULT_PROCEED_FINAL);

    return saveResult;
}

void SaveData_Clear(SaveData *saveData)
{
    saveData->isNewGameData = TRUE;
    saveData->fullSaveRequired = TRUE;

    SaveTable_Clear(&saveData->body, saveData->pageInfo);
}

BOOL SaveData_BackupExists(const SaveData *saveData)
{
    return saveData->backupExists;
}

u32 SaveData_LoadCheckStatus(const SaveData *saveData)
{
    return saveData->loadCheckStatus;
}

BOOL SaveData_DataExists(const SaveData *saveData)
{
    return saveData->dataExists;
}

BOOL SaveData_IsNewGameData(const SaveData *saveData)
{
    return saveData->isNewGameData;
}

BOOL SaveData_MiscSaveBlock_InitFlag(SaveData *saveData)
{
    return MiscSaveBlock_InitFlag(SaveData_MiscSaveBlock(saveData));
}

static void SaveData_MiscSaveBlock_SetInitFlag(SaveData *saveData)
{
    MiscSaveBlock_SetInitFlag(SaveData_MiscSaveBlock(saveData));
}

BOOL SaveData_OverwriteCheck(const SaveData *saveData)
{
    return SaveData_IsNewGameData(saveData) && SaveData_DataExists(saveData);
}

BOOL SaveData_FullSaveRequired(const SaveData *saveData)
{
    return saveData->fullSaveRequired;
}

void SaveData_SetFullSaveRequired(void)
{
    sSaveDataPtr->fullSaveRequired = TRUE;
}

void SaveData_SaveStateInit(SaveData *saveData, int blockID)
{
    SaveDataState_Init(saveData, &saveData->state, blockID);
}

int SaveData_SaveStateMain(SaveData *saveData)
{
    int saveResult = SaveDataState_Main(saveData, &saveData->state);

    if (saveResult != SAVE_RESULT_PROCEED && saveResult != SAVE_RESULT_PROCEED_FINAL) {
        SaveDataState_End(saveData, &saveData->state, saveResult);
    }

    return saveResult;
}

void SaveData_SaveStateCancel(SaveData *saveData)
{
    SaveDataState_Cancel(saveData, &saveData->state);
}

BOOL SaveData_SaveAsync_Start(SaveData *saveData)
{
    if (!saveData->backupExists) {
        return FALSE;
    }

    SaveData_EraseForNewGame(saveData);
    SaveData_SaveStateInit(saveData, SAVE_BLOCK_ID_MAX);

    return TRUE;
}

static void SaveData_CheckInfoInit(SaveCheckInfo *checkInfo)
{
    checkInfo->valid = FALSE;
    checkInfo->globalCounter = 0;
    checkInfo->blockCounter = 0;
}

u16 SaveData_CalculateChecksum(const SaveData *saveData, const void *startAddress, u32 size)
{
    return CalcCRC16Checksum(startAddress, size);
}

static u16 SaveData_CalculateFooterChecksum(const SaveData *saveData, void *startAddress, u32 size)
{
    return CalcCRC16Checksum(startAddress, size - sizeof(SaveBlockFooter));
}

static u32 SaveData_SaveOffset(int sectorID, const SaveBlockInfo *blockInfo)
{
    u32 offset;

    if (sectorID == SECTOR_ID_PRIMARY) {
        offset = PRIMARY_SECTOR_START * SAVE_SECTOR_SIZE;
    } else {
        offset = BACKUP_SECTOR_START * SAVE_SECTOR_SIZE;
    }

    offset += blockInfo->offset;
    return offset;
}

static SaveBlockFooter *SaveBlockFooter_Ptr(SaveData *saveData, u32 bodyAddress, int blockID)
{
    u32 footerAddress;
    const SaveBlockInfo *blockInfo = &saveData->blockInfo[blockID];

    footerAddress = bodyAddress + blockInfo->offset;
    GF_ASSERT(blockInfo->size);

    footerAddress += blockInfo->size;
    footerAddress -= sizeof(SaveBlockFooter);

    return (SaveBlockFooter *)footerAddress;
}

static BOOL SaveBlockFooter_Validate(SaveData *saveData, u32 bodyAddress, int blockID)
{
    const SaveBlockInfo *blockInfo = &saveData->blockInfo[blockID];
    SaveBlockFooter *footer = SaveBlockFooter_Ptr(saveData, bodyAddress, blockID);
    u32 startAddress = bodyAddress + blockInfo->offset;

    if (footer->size != blockInfo->size) {
        return FALSE;
    }

    if (footer->signature != SECTOR_SIGNATURE) {
        return FALSE;
    }

    if (footer->saveBlockID != blockID) {
        return FALSE;
    }

    if (footer->checksum != SaveData_CalculateFooterChecksum(saveData, startAddress, blockInfo->size)) {
        return FALSE;
    }

    return TRUE;
}

static void SaveBlockFooter_CheckInfo(SaveCheckInfo *checkInfo, SaveData *saveData, u32 bodyAddress, int blockID)
{
    SaveBlockFooter *footer = SaveBlockFooter_Ptr(saveData, bodyAddress, blockID);

    checkInfo->valid = SaveBlockFooter_Validate(saveData, bodyAddress, blockID);
    checkInfo->globalCounter = footer->saveCounter;
    checkInfo->blockCounter = footer->blockCounter;
}

static void SaveBlockFooter_Set(SaveData *saveData, u32 bodyAddress, int blockID)
{
    const SaveBlockInfo *blockInfo = &saveData->blockInfo[blockID];
    SaveBlockFooter *footer = SaveBlockFooter_Ptr(saveData, bodyAddress, blockID);
    u32 startAddress = bodyAddress + blockInfo->offset;

    footer->saveCounter = saveData->globalCounter;
    footer->blockCounter = saveData->blockCounters[blockID];
    footer->size = blockInfo->size;
    footer->signature = SECTOR_SIGNATURE;
    footer->saveBlockID = blockID;
    footer->checksum = SaveData_CalculateFooterChecksum(saveData, startAddress, blockInfo->size);
}

static int SaveCheckInfo_CompareCounters(u32 counter1, u32 counter2)
{
    if (counter1 == 0xffffffff && counter2 == 0) {
        return -1;
    } else if (counter1 == 0 && counter2 == 0xffffffff) {
        return 1;
    } else if (counter1 > counter2) {
        return 1;
    } else if (counter1 < counter2) {
        return -1;
    }

    return 0;
}

static int SaveCheckInfo_CompareSectors(const SaveCheckInfo *checkInfo1, const SaveCheckInfo *checkInfo2, int *currentSector, int *staleSector)
{
    int globalDiff = SaveCheckInfo_CompareCounters(checkInfo1->globalCounter, checkInfo2->globalCounter);
    int blockDiff = SaveCheckInfo_CompareCounters(checkInfo1->blockCounter, checkInfo2->blockCounter);

    if (checkInfo1->valid && checkInfo2->valid) {
        if (globalDiff > 0) {
            GF_ASSERT(blockDiff > 0);
            *currentSector = SECTOR_ID_PRIMARY;
            *staleSector = SECTOR_ID_BACKUP;
        } else if (globalDiff < 0) {
            GF_ASSERT(blockDiff < 0);
            *currentSector = SECTOR_ID_BACKUP;
            *staleSector = SECTOR_ID_PRIMARY;
        } else if (blockDiff > 0) {
            *currentSector = SECTOR_ID_PRIMARY;
            *staleSector = SECTOR_ID_BACKUP;
        } else if (blockDiff < 0) {
            *currentSector = SECTOR_ID_BACKUP;
            *staleSector = SECTOR_ID_PRIMARY;
        } else {
            *currentSector = SECTOR_ID_PRIMARY;
            *staleSector = SECTOR_ID_BACKUP;
        }

        return SECTOR_RESULT_VALID;

    } else if (checkInfo1->valid && !checkInfo2->valid) {
        *currentSector = SECTOR_ID_PRIMARY;
        *staleSector = SECTOR_ID_ERROR;
        return SECTOR_RESULT_PARTIAL_VALID;
    } else if (!checkInfo1->valid && checkInfo2->valid) {
        *currentSector = SECTOR_ID_BACKUP;
        *staleSector = SECTOR_ID_ERROR;
        return SECTOR_RESULT_PARTIAL_VALID;
    } else {
        *currentSector = SECTOR_ID_ERROR;
        *staleSector = SECTOR_ID_ERROR;
        return SECTOR_RESULT_INVALID;
    }
}

static void SaveData_SetBlockCheckInfo(SaveData *saveData, const SaveCheckInfo *normalCheck, const SaveCheckInfo *boxCheck, int normalOffset, int boxOffset)
{
    saveData->globalCounter = normalCheck[normalOffset].globalCounter;
    saveData->blockCounters[SAVE_BLOCK_ID_NORMAL] = normalCheck[normalOffset].blockCounter;
    saveData->blockCounters[SAVE_BLOCK_ID_BOXES] = boxCheck[boxOffset].blockCounter;
    saveData->blockOffsets[SAVE_BLOCK_ID_NORMAL] = normalOffset;
    saveData->blockOffsets[SAVE_BLOCK_ID_BOXES] = boxOffset;
}

static int SaveData_LoadCheck(SaveData *saveData)
{
    u8 *primaryBuffer = Heap_AllocAtEnd(HEAP_ID_APPLICATION, SAVE_SECTOR_SIZE * SAVE_PAGE_MAX);
    u8 *backupBuffer = Heap_AllocAtEnd(HEAP_ID_APPLICATION, SAVE_SECTOR_SIZE * SAVE_PAGE_MAX);

    SaveCheckInfo normalInfo[SECTOR_ID_MAX];
    SaveCheckInfo boxInfo[SECTOR_ID_MAX];

    if (SaveData_CardLoad(PRIMARY_SECTOR_START * SAVE_SECTOR_SIZE, primaryBuffer, SAVE_SECTOR_SIZE * SAVE_PAGE_MAX)) {
        SaveBlockFooter_CheckInfo(&normalInfo[SECTOR_ID_PRIMARY], saveData, (u32)primaryBuffer, SAVE_BLOCK_ID_NORMAL);
        SaveBlockFooter_CheckInfo(&boxInfo[SECTOR_ID_PRIMARY], saveData, (u32)primaryBuffer, SAVE_BLOCK_ID_BOXES);
    } else {
        SaveData_CheckInfoInit(&normalInfo[SECTOR_ID_PRIMARY]);
        SaveData_CheckInfoInit(&boxInfo[SECTOR_ID_PRIMARY]);
    }

    if (SaveData_CardLoad(BACKUP_SECTOR_START * SAVE_SECTOR_SIZE, backupBuffer, SAVE_SECTOR_SIZE * SAVE_PAGE_MAX)) {
        SaveBlockFooter_CheckInfo(&normalInfo[SECTOR_ID_BACKUP], saveData, (u32)backupBuffer, SAVE_BLOCK_ID_NORMAL);
        SaveBlockFooter_CheckInfo(&boxInfo[SECTOR_ID_BACKUP], saveData, (u32)backupBuffer, SAVE_BLOCK_ID_BOXES);
    } else {
        SaveData_CheckInfoInit(&normalInfo[SECTOR_ID_BACKUP]);
        SaveData_CheckInfoInit(&boxInfo[SECTOR_ID_BACKUP]);
    }

    for (int i = 0; i < SAVE_BLOCK_ID_MAX; i++) {
        const SaveBlockInfo *blockInfo = &saveData->blockInfo[i];
        sSlotsInSync[i] = memcmp(primaryBuffer + blockInfo->offset, backupBuffer + blockInfo->offset, blockInfo->size) == 0;
    }

    Heap_Free(primaryBuffer);
    Heap_Free(backupBuffer);

    int currNormalSector, currBoxSector, staleNormalSector, staleBoxSector;
    int normalResult = SaveCheckInfo_CompareSectors(&normalInfo[SECTOR_ID_PRIMARY], &normalInfo[SECTOR_ID_BACKUP], &currNormalSector, &staleNormalSector);
    int boxResult = SaveCheckInfo_CompareSectors(&boxInfo[SECTOR_ID_PRIMARY], &boxInfo[SECTOR_ID_BACKUP], &currBoxSector, &staleBoxSector);

    if (normalResult == SECTOR_RESULT_INVALID && boxResult == SECTOR_RESULT_INVALID) {
        return LOAD_RESULT_EMPTY;
    }

    if (normalResult == SECTOR_RESULT_INVALID || boxResult == SECTOR_RESULT_INVALID) {
        return LOAD_RESULT_ERROR;
    }

    if (normalResult == SECTOR_RESULT_VALID && boxResult == SECTOR_RESULT_VALID) {
        if (normalInfo[currNormalSector].globalCounter == boxInfo[currBoxSector].globalCounter) {
            SaveData_SetBlockCheckInfo(saveData, normalInfo, boxInfo, currNormalSector, currBoxSector);
            return LOAD_RESULT_OK;
        } else {
            SaveData_SetBlockCheckInfo(saveData, normalInfo, boxInfo, staleNormalSector, currBoxSector);
            return LOAD_RESULT_CORRUPT;
        }
    }

    if (normalResult == SECTOR_RESULT_PARTIAL_VALID && boxResult == SECTOR_RESULT_VALID) {
        if (normalInfo[currNormalSector].globalCounter == boxInfo[currBoxSector].globalCounter) {
            SaveData_SetBlockCheckInfo(saveData, normalInfo, boxInfo, currNormalSector, currBoxSector);
            return LOAD_RESULT_CORRUPT;
        } else if (normalInfo[currNormalSector].globalCounter == boxInfo[staleBoxSector].globalCounter) {
            SaveData_SetBlockCheckInfo(saveData, normalInfo, boxInfo, currNormalSector, staleBoxSector);
            return LOAD_RESULT_CORRUPT;
        }

        return LOAD_RESULT_ERROR;
    }

    if (normalResult == SECTOR_RESULT_VALID && boxResult == SECTOR_RESULT_PARTIAL_VALID) {
        if (normalInfo[currNormalSector].globalCounter == boxInfo[currBoxSector].globalCounter) {
            SaveData_SetBlockCheckInfo(saveData, normalInfo, boxInfo, currNormalSector, currBoxSector);
            return LOAD_RESULT_OK;
        } else {
            SaveData_SetBlockCheckInfo(saveData, normalInfo, boxInfo, staleNormalSector, currBoxSector);
            return LOAD_RESULT_CORRUPT;
        }
    }

    if (normalResult == SECTOR_RESULT_PARTIAL_VALID
        && boxResult == SECTOR_RESULT_PARTIAL_VALID
        && currNormalSector == currBoxSector) {
        GF_ASSERT(normalInfo[currNormalSector].globalCounter == boxInfo[currBoxSector].globalCounter);
        SaveData_SetBlockCheckInfo(saveData, normalInfo, boxInfo, currNormalSector, currBoxSector);
        return LOAD_RESULT_OK;
    } else {
        GF_ASSERT(normalInfo[currNormalSector].globalCounter == boxInfo[currBoxSector].globalCounter);
        SaveData_SetBlockCheckInfo(saveData, normalInfo, boxInfo, currNormalSector, currBoxSector);
        return LOAD_RESULT_CORRUPT;
    }
}

static void SaveDataExtra_LoadCheck(SaveData *saveData, int *frontierResult, int *videoResult)
{
    int loadResult;
    MiscSaveBlock *miscSave = SaveData_MiscSaveBlock(saveData);

    *frontierResult = LOAD_RESULT_OK;
    *videoResult = LOAD_RESULT_OK;

    if (SaveData_MiscSaveBlock_InitFlag(saveData) == FALSE) {
        return;
    }

    BOOL isOld;
    u32 currKey, oldKey;
    u8 loadFlag;

    MiscSaveBlock_ExtraSaveKey(miscSave, EXTRA_SAVE_TABLE_ENTRY_FRONTIER, &currKey, &oldKey, &loadFlag);

    void *saveBuffer;
    if (currKey != EXTRA_SAVE_TABLE_ENTRY_NONE || oldKey != EXTRA_SAVE_TABLE_ENTRY_NONE) {
        saveBuffer = SaveDataExtra_Mirror(saveData, HEAP_ID_APPLICATION, EXTRA_SAVE_TABLE_ENTRY_FRONTIER, &loadResult, &isOld);
        Heap_Free(saveBuffer);

        if (loadResult == LOAD_RESULT_CORRUPT) {
            *frontierResult = LOAD_RESULT_ERROR;
        } else if (loadResult == LOAD_RESULT_OK && isOld == TRUE) {
            *frontierResult = LOAD_RESULT_CORRUPT;
        }
    }

    for (int i = EXTRA_SAVE_TABLE_ENTRY_MY_RECORDINGS; i <= EXTRA_SAVE_TABLE_ENTRY_DL_RECORDINGS_2; i++) {
        MiscSaveBlock_ExtraSaveKey(miscSave, i, &currKey, &oldKey, &loadFlag);

        if (currKey != EXTRA_SAVE_TABLE_ENTRY_NONE || oldKey != EXTRA_SAVE_TABLE_ENTRY_NONE) {
            saveBuffer = SaveDataExtra_Mirror(saveData, HEAP_ID_APPLICATION, i, &loadResult, &isOld);
            Heap_Free(saveBuffer);

            if (loadResult == LOAD_RESULT_CORRUPT) {
                *videoResult = LOAD_RESULT_ERROR;
            } else if (loadResult == LOAD_RESULT_OK && isOld == TRUE) {
                if (*videoResult != LOAD_RESULT_ERROR) {
                    *videoResult = LOAD_RESULT_CORRUPT;
                }
            }
        }
    }
}

static BOOL SaveBlock_Load(int sectorID, const SaveBlockInfo *blockInfo, u8 *blockOffset)
{
    u32 saveOffset = SaveData_SaveOffset(sectorID, blockInfo);
    blockOffset += blockInfo->offset;

    return SaveData_CardLoad(saveOffset, blockOffset, blockInfo->size);
}

static BOOL SaveDataState_Load(SaveData *saveData)
{
    int i;

    for (i = 0; i < SAVE_BLOCK_ID_MAX; i++) {
        if (SaveBlock_Load(saveData->blockOffsets[i], &saveData->blockInfo[i], saveData->body.data) == FALSE) {
            return FALSE;
        }

        if (SaveBlockFooter_Validate(saveData, (u32)saveData->body.data, i) == FALSE) {
            return FALSE;
        }
    }

    for (i = 0; i < SAVE_TABLE_ENTRY_MAX; i++) {
        saveData->pageInfo[i].checksum = CalcCRC16Checksum(SaveData_SaveTable(saveData, i), saveData->pageInfo[i].size);
    }

    return TRUE;
}

static BOOL SaveData_CardRead(u32 address, void *data, u32 size)
{
    s32 lockID = OS_GetLockID();
    GF_ASSERT(lockID != OS_LOCK_ID_ERROR);

    CARD_LockBackup(lockID);
    BOOL result = CARD_ReadFlash(address, data, size);
    CARD_UnlockBackup(lockID);
    OS_ReleaseLockID(lockID);

    return result;
}

static int SaveDataState_Slot(const SaveData *saveData, const SaveDataState *state, int blockID)
{
    return state->pass == 0 ? !saveData->blockOffsets[blockID] : saveData->blockOffsets[blockID];
}

static u32 SaveBlock_PageBase(const SaveData *saveData, int blockID)
{
    u32 base = 0;

    for (int i = 0; i < blockID; i++) {
        base += (saveData->blockInfo[i].size + SAVE_COMPARE_PAGE_SIZE - 1) / SAVE_COMPARE_PAGE_SIZE;
    }

    return base;
}

static void SaveBlock_ClearDirtyPages(const SaveData *saveData, int blockID)
{
    u32 base = SaveBlock_PageBase(saveData, blockID);
    u32 count = (saveData->blockInfo[blockID].size + SAVE_COMPARE_PAGE_SIZE - 1) / SAVE_COMPARE_PAGE_SIZE;

    for (u32 i = base; i < base + count; i++) {
        sDirtyPages[i / 8] &= ~(1 << (i % 8));
    }
}

static void SaveDataState_StartWrite(SaveDataState *state, u32 address, void *data, u32 size, int nextSequence)
{
    state->lockID = SaveData_CardSave_Init(address, data, size);
    state->locked = TRUE;
    state->nextSequence = nextSequence;
    state->mainSequence = SAVE_SEQ_WRITE_WAIT;
}

static void SaveDataState_Init(SaveData *saveData, SaveDataState *state, int blockID)
{
    for (int i = 0; i < SAVE_BLOCK_ID_MAX; i++) {
        state->blockCounterBackup[i] = saveData->blockCounters[i];
        saveData->blockCounters[i]++;
    }

    state->mainSequence = SAVE_SEQ_BLOCK_START;
    state->fullSaveMode = FALSE;
    state->locked = FALSE;
    state->pass = 0;
    state->pos = 0;
    state->runStart = 0;
    state->runEnd = 0;
    state->finalSent = FALSE;
    state->restarted = 0;
    state->unsynced = 0;
    state->writeAll = saveData->isNewGameData;

    if (blockID == SAVE_BLOCK_ID_MAX) {
        if (saveData->fullSaveRequired) {
            state->fullSaveMode = TRUE;
            state->globalCounterBackup = saveData->globalCounter;
            saveData->globalCounter++;

            state->startBlock = SAVE_BLOCK_ID_NORMAL;
            state->currentBlock = SAVE_BLOCK_ID_NORMAL;
            state->endBlock = SAVE_BLOCK_ID_MAX;
        } else {
            state->startBlock = SAVE_BLOCK_ID_NORMAL;
            state->currentBlock = SAVE_BLOCK_ID_NORMAL;
            state->endBlock = SAVE_BLOCK_ID_NORMAL + 1;
        }
    } else {
        state->startBlock = blockID;
        state->currentBlock = blockID;
        state->endBlock = blockID + 1;
    }

    SleepLock(SLEEP_TYPE_SAVE_DATA);
    PlayTime_SetPaused(TRUE);
}

static int SaveDataState_Main(SaveData *saveData, SaveDataState *state)
{
    u32 budget = SAVE_COMPARE_BUDGET;
    BOOL saveResult;

    while (TRUE) {
        int block = state->currentBlock;
        const SaveBlockInfo *blockInfo = &saveData->blockInfo[block];
        u32 bodySize = blockInfo->size - sizeof(SaveBlockFooter);
        u32 slotAddress = SaveData_SaveOffset(SaveDataState_Slot(saveData, state, block), blockInfo);
        u8 *body = saveData->body.data + blockInfo->offset;

        switch (state->mainSequence) {
        case SAVE_SEQ_BLOCK_START:
            if (state->pass == 0) {
                SaveBlockFooter_Set(saveData, (u32)saveData->body.data, block);
                SaveBlock_ClearDirtyPages(saveData, block);
            }

            state->pos = 0;
            state->runStart = 0;
            state->runEnd = 0;
            state->mainSequence = SAVE_SEQ_COMPARE;
            break;

        case SAVE_SEQ_COMPARE: {
            BOOL reuse = state->pass == 1 && sSlotsInSync[block] && !(state->restarted & (1 << block));
            u32 pageBase = SaveBlock_PageBase(saveData, block);

            while (state->pos < bodySize) {
                u32 size = bodySize - state->pos;
                u32 page = pageBase + state->pos / SAVE_COMPARE_PAGE_SIZE;
                BOOL differs;

                if (size > SAVE_COMPARE_PAGE_SIZE) {
                    size = SAVE_COMPARE_PAGE_SIZE;
                }

                if (state->writeAll) {
                    differs = TRUE;
                } else if (reuse) {
                    differs = (sDirtyPages[page / 8] >> (page % 8)) & 1;
                } else {
                    if (budget < size) {
                        return SAVE_RESULT_PROCEED;
                    }

                    budget -= size;
                    differs = !SaveData_CardRead(slotAddress + state->pos, sComparePage, size)
                        || memcmp(sComparePage, body + state->pos, size) != 0;

                    if (differs && state->pass == 0) {
                        sDirtyPages[page / 8] |= 1 << (page % 8);
                    }
                }

                if (differs) {
                    if (state->runEnd == state->runStart) {
                        state->runStart = state->pos;
                    }

                    state->pos += size;
                    state->runEnd = state->pos;

                    if (state->runEnd - state->runStart >= SAVE_WRITE_RUN_MAX) {
                        SaveDataState_StartWrite(state, slotAddress + state->runStart, body + state->runStart, state->runEnd - state->runStart, SAVE_SEQ_COMPARE);
                        return SAVE_RESULT_PROCEED;
                    }
                } else {
                    state->pos += size;

                    if (state->runEnd != state->runStart) {
                        SaveDataState_StartWrite(state, slotAddress + state->runStart, body + state->runStart, state->runEnd - state->runStart, SAVE_SEQ_COMPARE);
                        return SAVE_RESULT_PROCEED;
                    }
                }
            }

            if (state->runEnd != state->runStart) {
                SaveDataState_StartWrite(state, slotAddress + state->runStart, body + state->runStart, state->runEnd - state->runStart, SAVE_SEQ_COMPARE);
                return SAVE_RESULT_PROCEED;
            }

            state->mainSequence = SAVE_SEQ_FOOTER_CHECK;
            break;
        }

        case SAVE_SEQ_WRITE_WAIT:
            if (SaveData_CardSave_Main(state->lockID, state->locked, &saveResult) == FALSE) {
                return SAVE_RESULT_PROCEED;
            }

            state->locked = FALSE;

            if (!saveResult) {
                return SAVE_RESULT_CORRUPT;
            }

            state->runStart = 0;
            state->runEnd = 0;
            state->mainSequence = state->nextSequence;
            break;

        case SAVE_SEQ_FOOTER_CHECK:
            if (SaveBlockFooter_Ptr(saveData, (u32)saveData->body.data, block)->checksum != SaveData_CalculateFooterChecksum(saveData, body, blockInfo->size)) {
                SaveBlockFooter_Set(saveData, (u32)saveData->body.data, block);
                state->restarted |= 1 << block;

                if (state->pass == 1) {
                    state->unsynced |= 1 << block;
                }

                state->pos = 0;
                state->mainSequence = SAVE_SEQ_COMPARE;
                break;
            }

            state->mainSequence = SAVE_SEQ_FOOTER;

            if (state->pass == 0 && block + 1 == state->endBlock && !state->finalSent) {
                state->finalSent = TRUE;
                return SAVE_RESULT_PROCEED_FINAL;
            }
            break;

        case SAVE_SEQ_FOOTER:
            SaveDataState_StartWrite(state, slotAddress + bodySize, body + bodySize, sizeof(SaveBlockFooter), SAVE_SEQ_BLOCK_DONE);
            return SAVE_RESULT_PROCEED;

        case SAVE_SEQ_BLOCK_DONE:
            state->currentBlock++;

            if (state->currentBlock == state->endBlock) {
                if (state->pass == 1) {
                    return SAVE_RESULT_OK;
                }

                state->pass = 1;
                state->currentBlock = state->startBlock;
            }

            state->mainSequence = SAVE_SEQ_BLOCK_START;
            break;
        }
    }
}

static void SaveDataState_End(SaveData *saveData, SaveDataState *state, int saveResult)
{
    int i;

    if (saveResult == SAVE_RESULT_CORRUPT) {
        if (state->fullSaveMode) {
            saveData->globalCounter = state->globalCounterBackup;
        }

        for (i = 0; i < SAVE_BLOCK_ID_MAX; i++) {
            saveData->blockCounters[i] = state->blockCounterBackup[i];
        }

        for (i = state->startBlock; i < state->endBlock; i++) {
            sSlotsInSync[i] = FALSE;
        }
    } else {
        for (i = state->startBlock; i < state->endBlock; i++) {
            saveData->blockOffsets[i] = !saveData->blockOffsets[i];
            sSlotsInSync[i] = !(state->unsynced & (1 << i));
        }

        saveData->dataExists = TRUE;
        saveData->isNewGameData = FALSE;
        saveData->fullSaveRequired = FALSE;
    }

    SleepUnlock(SLEEP_TYPE_SAVE_DATA);
    PlayTime_SetPaused(FALSE);
}

static void SaveDataState_Cancel(SaveData *saveData, SaveDataState *state)
{
    int i;

    if (state->fullSaveMode) {
        saveData->globalCounter = state->globalCounterBackup;
    }

    for (i = 0; i < SAVE_BLOCK_ID_MAX; i++) {
        saveData->blockCounters[i] = state->blockCounterBackup[i];
    }

    for (i = state->startBlock; i < state->endBlock; i++) {
        sSlotsInSync[i] = FALSE;
    }

    if (!CARD_TryWaitBackupAsync()) {
        CARD_CancelBackupAsync();
    }

    if (state->locked) {
        CARD_UnlockBackup(state->lockID);
        OS_ReleaseLockID(state->lockID);
        state->locked = FALSE;
    }

    SleepUnlock(SLEEP_TYPE_SAVE_DATA);
    PlayTime_SetPaused(FALSE);
}

BOOL SaveDataState_Save(SaveData *saveData)
{
    SaveDataState state;
    SaveDataState_Init(saveData, &state, SAVE_BLOCK_ID_MAX);

    int saveResult;

    do {
        saveResult = SaveDataState_Main(saveData, &state);
    } while (saveResult == SAVE_RESULT_PROCEED || saveResult == SAVE_RESULT_PROCEED_FINAL);

    SaveDataState_End(saveData, &state, saveResult);
    return saveResult;
}

static BOOL SaveBlockFooter_Erase(const SaveData *saveData, int blockID, int sectorID)
{
    SaveBlockFooter footer;
    const SaveBlockInfo *blockInfo = &saveData->blockInfo[blockID];

    MI_CpuFill8(&footer, 0xff, sizeof(SaveBlockFooter));
    u32 saveOffset = SaveData_SaveOffset(sectorID, blockInfo) + blockInfo->size - sizeof(SaveBlockFooter);

    return SaveData_CardSave(saveOffset, &footer, sizeof(SaveBlockFooter));
}

int SaveTableEntry_BodySize(int saveTableID)
{
    const SaveTableEntry *saveTable = gSaveTable;

    GF_ASSERT(saveTableID < gSaveTableSize);
    int size = saveTable[saveTableID].sizeFunc();

    size += 4 - (size % 4);
    size += 4;

    return size;
}

static void SavePageInfo_Init(SavePageInfo *pageInfo)
{
    const SaveTableEntry *saveTable = gSaveTable;
    int i, totalSize = 0;

    GF_ASSERT(gSaveTableSize == SAVE_TABLE_ENTRY_MAX);

    for (i = 0; i < gSaveTableSize; i++) {
        GF_ASSERT(saveTable[i].dataID == i);

        pageInfo[i].pageID = saveTable[i].dataID;
        pageInfo[i].size = SaveTableEntry_BodySize(i);
        pageInfo[i].location = totalSize;
        pageInfo[i].checksum = 0;
        pageInfo[i].blockID = saveTable[i].blockID;

        totalSize += pageInfo[i].size;

        if ((i == gSaveTableSize - 1) || (saveTable[i].blockID != saveTable[i + 1].blockID)) {
            totalSize += sizeof(SaveBlockFooter);
        }
    }

    GF_ASSERT(totalSize <= SAVE_SECTOR_SIZE * SAVE_PAGE_MAX);
}

static void SaveBlockInfo_Init(SaveBlockInfo *blockInfo, const SavePageInfo *pageInfo)
{
    int totalSectors = 0, blockOffset = 0, i, page = 0;

    for (i = 0; i < SAVE_BLOCK_ID_MAX; i++) {
        blockInfo[i].saveBlockID = i;
        blockInfo[i].size = 0;

        while (pageInfo[page].blockID == i && page < gSaveTableSize) {
            blockInfo[i].size += pageInfo[page].size;
            page++;
        }

        blockInfo[i].size += sizeof(SaveBlockFooter);
        blockInfo[i].sectorStartPos = totalSectors;
        blockInfo[i].offset = blockOffset;
        blockInfo[i].sectorsInUse = (blockInfo[i].size + SAVE_SECTOR_SIZE - 1) / SAVE_SECTOR_SIZE;

        totalSectors += blockInfo[i].sectorsInUse;
        blockOffset += blockInfo[i].size;
    }

    GF_ASSERT(totalSectors == blockInfo[SAVE_BLOCK_ID_MAX - 1].sectorStartPos + blockInfo[SAVE_BLOCK_ID_MAX - 1].sectorsInUse);
    GF_ASSERT(totalSectors <= SAVE_PAGE_MAX);
}

static void SaveTable_Clear(SaveDataBody *body, const SavePageInfo *pageInfo)
{
    const SaveTableEntry *saveTable = gSaveTable;
    MI_CpuClearFast(body->data, sizeof(body->data));

    int i, size;
    void *page;
    u32 location;

    for (i = 0; i < gSaveTableSize; i++) {
        location = pageInfo[i].location;
        page = &body->data[location];
        size = pageInfo[i].size;
        MI_CpuClearFast(page, size);
        saveTable[i].initFunc(page);
    }
}

void SaveDataExtra_Init(SaveData *saveData)
{
    const SaveTableEntry *extraTable = gExtraSaveTable;

    if (SaveData_MiscSaveBlock_InitFlag(saveData) == TRUE) {
        return;
    }

    int i, loadResult;
    void *extraData;

    for (i = 0; i < gExtraSaveTableSize; i++) {
        if (extraTable[i].dataID == EXTRA_SAVE_TABLE_ENTRY_HALL_OF_FAME) {
            continue;
        }

        extraData = SaveDataExtra_Get(saveData, HEAP_ID_APPLICATION, extraTable[i].dataID, &loadResult);

        GF_ASSERT(extraData != NULL);
        MI_CpuClear8(extraData, extraTable[i].sizeFunc());

        extraTable[i].initFunc(extraData);

        SaveDataExtra_Save(saveData, extraTable[i].dataID, extraData);
        Heap_Free(extraData);
    }

    SaveData_MiscSaveBlock_SetInitFlag(saveData);
}

static void SaveCheckFooter_Set(const SaveData *saveData, void *saveBody, int extraSaveID, u32 size)
{
    SaveCheckFooter *footer = (SaveCheckFooter *)(saveBody + size);

    footer->signature = SECTOR_SIGNATURE;
    footer->saveCounter = saveData->sectorCounter + 1;
    footer->size = size;
    footer->id = extraSaveID;
    footer->checksum = CalcCRC16Checksum(saveBody, size + sizeof(SaveCheckFooter) - 2);
}

static BOOL SaveCheckFooter_Validate(const SaveData *saveData, void *saveBody, int extraSaveID, u32 size)
{
    SaveCheckFooter *footer = (SaveCheckFooter *)(saveBody + size);

    if (footer->signature != SECTOR_SIGNATURE) {
        return FALSE;
    }

    if (footer->size != size) {
        return FALSE;
    }

    if (footer->id != extraSaveID) {
        return FALSE;
    }

    if (footer->checksum != CalcCRC16Checksum(saveBody, size + sizeof(SaveCheckFooter) - 2)) {
        return FALSE;
    }

    return TRUE;
}

static u32 SaveCheckFooter_SaveCounter(void *saveBody, u32 size)
{
    return ((SaveCheckFooter *)(saveBody + size))->saveCounter;
}

int SaveDataExtra_Save(const SaveData *saveData, int extraSaveID, void *data)
{
    SleepLock(SLEEP_TYPE_SAVE_DATA);
    GF_ASSERT(extraSaveID < gExtraSaveTableSize);

    const SaveTableEntry *saveTable = &gExtraSaveTable[extraSaveID];
    GF_ASSERT(saveTable->dataID == extraSaveID);

    u32 size = saveTable->sizeFunc() + sizeof(SaveCheckFooter);
    BOOL saveResult;

    if (saveData->sectorSwitch == SECTOR_ID_BACKUP) {
        SaveCheckFooter_Set(saveData, data, extraSaveID, saveTable->sizeFunc());
        saveResult = SaveData_CardSave((PRIMARY_SECTOR_START + saveTable->blockID) * SAVE_SECTOR_SIZE, data, size);

        GF_ASSERT(SaveCheckFooter_Validate(saveData, data, extraSaveID, saveTable->sizeFunc()) == TRUE);
        SaveCheckFooter_Set(saveData, data, extraSaveID, saveTable->sizeFunc());

        saveResult |= SaveData_CardSave((BACKUP_SECTOR_START + saveTable->blockID) * SAVE_SECTOR_SIZE, data, size);
        GF_ASSERT(SaveCheckFooter_Validate(saveData, data, extraSaveID, saveTable->sizeFunc()) == TRUE);
    } else {
        SaveCheckFooter_Set(saveData, data, extraSaveID, saveTable->sizeFunc());
        saveResult = SaveData_CardSave((BACKUP_SECTOR_START + saveTable->blockID) * SAVE_SECTOR_SIZE, data, size);

        GF_ASSERT(SaveCheckFooter_Validate(saveData, data, extraSaveID, saveTable->sizeFunc()) == TRUE);
        SaveCheckFooter_Set(saveData, data, extraSaveID, saveTable->sizeFunc());

        saveResult |= SaveData_CardSave((PRIMARY_SECTOR_START + saveTable->blockID) * SAVE_SECTOR_SIZE, data, size);
        GF_ASSERT(SaveCheckFooter_Validate(saveData, data, extraSaveID, saveTable->sizeFunc()) == TRUE);
    }

    if (saveResult == TRUE) {
        SleepUnlock(SLEEP_TYPE_SAVE_DATA);
        return SAVE_RESULT_OK;
    } else {
        SleepUnlock(SLEEP_TYPE_SAVE_DATA);
        return SAVE_RESULT_CORRUPT;
    }
}

int SaveDataExtra_SaveMirror(SaveData *saveData, int extraSaveID, void *data)
{
    SleepLock(SLEEP_TYPE_SAVE_DATA);
    GF_ASSERT(extraSaveID < gExtraSaveTableSize);

    const SaveTableEntry *saveTable = &gExtraSaveTable[extraSaveID];
    GF_ASSERT(saveTable->dataID == extraSaveID);

    u32 size = saveTable->sizeFunc() + sizeof(SaveCheckFooter);

    u32 currKey, oldKey, newKey;
    u8 keyFlag;
    SaveDataExtra_SaveKey(saveData, extraSaveID, &currKey, &oldKey, &keyFlag);

    do {
        newKey = ARNG_Next(currKey);
    } while (newKey == EXTRA_SAVE_TABLE_ENTRY_NONE);

    SaveDataExtra_SetSaveKey(saveData, extraSaveID, newKey, currKey, keyFlag ^ 1);

    *((u32 *)data) = newKey;

    BOOL saveResult;

    if (keyFlag == 1) {
        SaveCheckFooter_Set(saveData, data, extraSaveID, saveTable->sizeFunc());
        saveResult = SaveData_CardSave((PRIMARY_SECTOR_START + saveTable->blockID) * SAVE_SECTOR_SIZE, data, size);
        GF_ASSERT(SaveCheckFooter_Validate(saveData, data, extraSaveID, saveTable->sizeFunc()) == TRUE);
    } else {
        SaveCheckFooter_Set(saveData, data, extraSaveID, saveTable->sizeFunc());
        saveResult = SaveData_CardSave((BACKUP_SECTOR_START + saveTable->blockID) * SAVE_SECTOR_SIZE, data, size);
        GF_ASSERT(SaveCheckFooter_Validate(saveData, data, extraSaveID, saveTable->sizeFunc()) == TRUE);
    }

    if (saveResult == TRUE) {
        SleepUnlock(SLEEP_TYPE_SAVE_DATA);
        return SAVE_RESULT_OK;
    } else {
        SleepUnlock(SLEEP_TYPE_SAVE_DATA);
        return SAVE_RESULT_CORRUPT;
    }
}

void *SaveDataExtra_Get(SaveData *saveData, enum HeapID heapID, int extraSaveID, int *loadResult)
{
    GF_ASSERT(extraSaveID < gExtraSaveTableSize);

    const SaveTableEntry *saveTable = &gExtraSaveTable[extraSaveID];
    GF_ASSERT(saveTable->dataID == extraSaveID);

    u32 size = saveTable->sizeFunc() + sizeof(SaveCheckFooter);
    void *ret = Heap_Alloc(heapID, size);

    SaveData_CardLoad((PRIMARY_SECTOR_START + saveTable->blockID) * SAVE_SECTOR_SIZE, ret, size);

    BOOL primaryResult = SaveCheckFooter_Validate(saveData, ret, extraSaveID, saveTable->sizeFunc());
    u32 primaryCounter = SaveCheckFooter_SaveCounter(ret, saveTable->sizeFunc());

    SaveData_CardLoad((BACKUP_SECTOR_START + saveTable->blockID) * SAVE_SECTOR_SIZE, ret, size);

    BOOL backupResult = SaveCheckFooter_Validate(saveData, ret, extraSaveID, saveTable->sizeFunc());
    u32 backupCounter = SaveCheckFooter_SaveCounter(ret, saveTable->sizeFunc());

    *loadResult = LOAD_RESULT_OK;

    if (primaryResult == TRUE && backupResult == FALSE) {
        saveData->sectorSwitch = SECTOR_ID_PRIMARY;
        saveData->sectorCounter = primaryCounter;
        SaveData_CardLoad((PRIMARY_SECTOR_START + saveTable->blockID) * SAVE_SECTOR_SIZE, ret, size);
        return ret;
    }

    if (primaryResult == FALSE && backupResult == TRUE) {
        saveData->sectorSwitch = SECTOR_ID_BACKUP;
        saveData->sectorCounter = backupCounter;
        SaveData_CardLoad((BACKUP_SECTOR_START + saveTable->blockID) * SAVE_SECTOR_SIZE, ret, size);
        return ret;
    }

    if (primaryResult == TRUE && backupResult == TRUE) {
        if (SaveCheckInfo_CompareCounters(primaryCounter, backupCounter) != -1) {
            saveData->sectorSwitch = SECTOR_ID_PRIMARY;
            saveData->sectorCounter = primaryCounter;
            SaveData_CardLoad((PRIMARY_SECTOR_START + saveTable->blockID) * SAVE_SECTOR_SIZE, ret, size);
            return ret;
        } else {
            saveData->sectorSwitch = SECTOR_ID_BACKUP;
            saveData->sectorCounter = backupCounter;
            SaveData_CardLoad((BACKUP_SECTOR_START + saveTable->blockID) * SAVE_SECTOR_SIZE, ret, size);
            return ret;
        }
    }

    *loadResult = LOAD_RESULT_CORRUPT;

    saveData->sectorSwitch = 0;
    saveData->sectorCounter = 0;

    return ret;
}

void *SaveDataExtra_Mirror(SaveData *saveData, enum HeapID heapID, int extraSaveID, int *loadResult, BOOL *isOld)
{
    const SaveTableEntry *saveTable;
    void *ret;
    u32 size;
    BOOL primaryResult, backupResult;
    MiscSaveBlock *miscSave = SaveData_MiscSaveBlock(saveData);

    GF_ASSERT(extraSaveID < gExtraSaveTableSize);
    GF_ASSERT(extraSaveID != EXTRA_SAVE_TABLE_ENTRY_HALL_OF_FAME);

    saveTable = &gExtraSaveTable[extraSaveID];
    GF_ASSERT(saveTable->dataID == extraSaveID);

    size = saveTable->sizeFunc() + sizeof(SaveCheckFooter);
    ret = Heap_Alloc(heapID, size);

    u32 primaryKey, backupKey, currKey, oldKey;
    u8 keyFlag;

    SaveDataExtra_SaveKey(saveData, extraSaveID, &currKey, &oldKey, &keyFlag);

    SaveData_CardLoad((PRIMARY_SECTOR_START + saveTable->blockID) * SAVE_SECTOR_SIZE, ret, size);
    primaryResult = SaveCheckFooter_Validate(saveData, ret, extraSaveID, saveTable->sizeFunc());

    MI_CpuCopy8(ret, &primaryKey, sizeof(u32));

    SaveData_CardLoad((BACKUP_SECTOR_START + saveTable->blockID) * SAVE_SECTOR_SIZE, ret, size);
    backupResult = SaveCheckFooter_Validate(saveData, ret, extraSaveID, saveTable->sizeFunc());

    MI_CpuCopy8(ret, &backupKey, sizeof(u32));

    *loadResult = LOAD_RESULT_OK;
    *isOld = FALSE;

    if (primaryResult == TRUE
        && backupResult == FALSE
        && currKey == primaryKey) {

        if (keyFlag == 1) {
            SaveDataExtra_SetSaveKey(saveData, extraSaveID, oldKey, oldKey, 0);
            *isOld = TRUE;
        }

        SaveData_CardLoad((PRIMARY_SECTOR_START + saveTable->blockID) * SAVE_SECTOR_SIZE, ret, size);
        return ret;
    }

    if (primaryResult == FALSE
        && backupResult == TRUE
        && currKey == backupKey) {

        if (keyFlag == 0) {
            SaveDataExtra_SetSaveKey(saveData, extraSaveID, oldKey, oldKey, 1);
            *isOld = TRUE;
        }

        SaveData_CardLoad((BACKUP_SECTOR_START + saveTable->blockID) * SAVE_SECTOR_SIZE, ret, size);
        return ret;
    }

    if (primaryResult == TRUE && backupResult == TRUE) {
        if (keyFlag == 0) {
            if (currKey == primaryKey) {
                SaveData_CardLoad((PRIMARY_SECTOR_START + saveTable->blockID) * SAVE_SECTOR_SIZE, ret, size);
                return ret;
            } else if (oldKey == backupKey) {
                SaveDataExtra_SetSaveKey(saveData, extraSaveID, oldKey, oldKey, keyFlag ^ 1);
                *isOld = TRUE;
                SaveData_CardLoad((BACKUP_SECTOR_START + saveTable->blockID) * SAVE_SECTOR_SIZE, ret, size);
                return ret;
            }
        } else {
            if (currKey == backupKey) {
                SaveData_CardLoad((BACKUP_SECTOR_START + saveTable->blockID) * SAVE_SECTOR_SIZE, ret, size);
                return ret;
            } else if (oldKey == primaryKey) {
                SaveDataExtra_SetSaveKey(saveData, extraSaveID, oldKey, oldKey, keyFlag ^ 1);
                *isOld = TRUE;
                SaveData_CardLoad((PRIMARY_SECTOR_START + saveTable->blockID) * SAVE_SECTOR_SIZE, ret, size);
                return ret;
            }
        }
    }

    *loadResult = LOAD_RESULT_CORRUPT;
    MiscSaveBlock_SetExtraSaveKey(miscSave, saveTable->dataID, EXTRA_SAVE_TABLE_ENTRY_NONE, EXTRA_SAVE_TABLE_ENTRY_NONE, 0);

    return ret;
}

static void SaveDataExtra_SaveKey(SaveData *saveData, int extraSaveID, u32 *returnKey, u32 *oldKey, u8 *keyFlag)
{
    MiscSaveBlock_ExtraSaveKey(SaveData_MiscSaveBlock(saveData), extraSaveID, returnKey, oldKey, keyFlag);
}

static void SaveDataExtra_SetSaveKey(SaveData *saveData, int extraSaveID, u32 newKey, u32 oldKey, u8 keyFlag)
{
    MiscSaveBlock_SetExtraSaveKey(SaveData_MiscSaveBlock(saveData), extraSaveID, newKey, oldKey, keyFlag);
}

BOOL SaveData_CardBackupType(void)
{
    s32 lockID = OS_GetLockID();
    GF_ASSERT(lockID != OS_LOCK_ID_ERROR);

    CARD_LockBackup(lockID);

    BOOL result;

    if (CARD_IdentifyBackup(CARD_BACKUP_TYPE_FLASH_4MBITS)) {
        result = CARD_BACKUP_TYPE_FLASH_4MBITS;
    } else if (CARD_IdentifyBackup(CARD_BACKUP_TYPE_FLASH_2MBITS)) {
        result = CARD_BACKUP_TYPE_FLASH_2MBITS;
    } else {
        result = CARD_BACKUP_TYPE_NOT_USE;
    }

    CARD_UnlockBackup(lockID);
    OS_ReleaseLockID(lockID);

    return result != CARD_BACKUP_TYPE_NOT_USE;
}

BOOL SaveData_CardSave(u32 address, void *data, u32 size)
{
    s32 lockID = SaveData_CardSave_Init(address, data, size);
    BOOL result;

    while (SaveData_CardSave_Main(lockID, TRUE, &result) == FALSE) {
        (void)0;
    }

    return result;
}

BOOL SaveData_CardLoad(u32 address, void *data, u32 size)
{
    s32 lockID = OS_GetLockID();
    GF_ASSERT(lockID != OS_LOCK_ID_ERROR);

    CARD_LockBackup(lockID);
    CARD_ReadFlashAsync(address, data, size, NULL, NULL);

    BOOL result = CARD_WaitBackupAsync();

    CARD_UnlockBackup(lockID);
    OS_ReleaseLockID(lockID);

    if (!result) {
        Heap_Free(sSaveDataPtr);
        sub_0209A74C(HEAP_ID_SAVE);
    }

    return result;
}

static void CB_SaveComplete(void *unused)
{
    sSaveComplete = TRUE;
}

static s32 SaveData_CardSave_Init(u32 address, void *data, u32 size)
{
    s32 lockID = OS_GetLockID();
    GF_ASSERT(lockID != OS_LOCK_ID_ERROR);

    CARD_LockBackup(lockID);

    u32 buffer;
    BOOL readResult = CARD_ReadFlash(0, &buffer, sizeof(buffer));

    if (!readResult) {
        SaveData_CardSave_Error(lockID, SAVE_ERROR_DISABLE_READ);
    }

    sSaveComplete = FALSE;
    CARD_WriteAndVerifyFlashAsync(address, data, size, CB_SaveComplete, NULL);

    return lockID;
}

static BOOL SaveData_CardSave_Main(s32 lockID, BOOL lockFlag, BOOL *result)
{
    if (sSaveComplete == TRUE) {
        if (!lockFlag) {
            return TRUE;
        }

        CARD_UnlockBackup(lockID);
        OS_ReleaseLockID(lockID);

        switch (CARD_GetResultCode()) {
        case CARD_RESULT_SUCCESS:
            *result = TRUE;
            break;
        default:
            GF_ASSERT(FALSE);
        case CARD_RESULT_TIMEOUT:
            *result = FALSE;
            SaveData_CardSave_Error(lockID, SAVE_ERROR_DISABLE_WRITE);
        case CARD_RESULT_NO_RESPONSE:
            *result = FALSE;
            SaveData_CardSave_Error(lockID, SAVE_ERROR_DISABLE_READ);
            break;
        }

        return TRUE;
    }

    return FALSE;
}

static void SaveData_CardSave_Error(s32 lockID, int errorID)
{
    CARD_UnlockBackup(lockID);
    OS_ReleaseLockID(lockID);

    Heap_Free(sSaveDataPtr);
    sub_0209AA74(HEAP_ID_SAVE, errorID);
}

BOOL SaveData_Checksum(int saveTableID)
{
    SaveData *saveData = SaveData_Ptr();
    void *table = SaveData_SaveTable(saveData, saveTableID);
    int size = SaveTableEntry_BodySize(saveTableID) - 4;

    u16 checkResult = CalcCRC16Checksum(table, size);

    int halfSize = size / 2;
    u16 *halfTable = table;

    if (halfTable[halfSize] == checkResult) {
        return TRUE;
    }

    u32 address = (u32)&halfTable[halfSize];
    GF_ASSERT(FALSE);

    return FALSE;
}

void SaveData_SetChecksum(int saveTableID)
{
    SaveData *saveData = SaveData_Ptr();
    void *table = SaveData_SaveTable(saveData, saveTableID);

    int size = SaveTableEntry_BodySize(saveTableID) - 4;
    int halfSize = size / 2;
    u16 *halfTable = table;

    u16 checksum = CalcCRC16Checksum(table, size);

    halfTable[halfSize] = checksum;

    u32 address = (u32)&halfTable[halfSize];
}
