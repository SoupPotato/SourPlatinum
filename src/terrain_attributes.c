#include "terrain_attributes.h"

#include <nitro.h>
#include <string.h>

#include "constants/field/map.h"

#include "field/field_system.h"

#include "heap.h"
#include "map_matrix.h"
#include "narc.h"

static void TerrainAttributes_Load(MapMatrix *mapMatrix, TerrainAttributes *terrainAttributes, const u8 blockCount);
static const u8 TerrainAttributes_GetOrPushLandDataID(const u16 landDataID, u16 *blockIndexToLandDataID, u8 *blockCount);

void TerrainAttributes_New(FieldSystem *fieldSystem, const u8 blockCount)
{
    if (fieldSystem->terrainAttributes == NULL) {
        fieldSystem->terrainAttributes = Heap_Alloc(HEAP_ID_FIELD2, sizeof(TerrainAttributes));

        TerrainAttributes_Load(fieldSystem->mapMatrix, fieldSystem->terrainAttributes, blockCount);
    }
}

void TerrainAttributes_Free(FieldSystem *fieldSystem)
{
    if (fieldSystem->terrainAttributes != NULL) {
        Heap_Free(fieldSystem->terrainAttributes);
        fieldSystem->terrainAttributes = NULL;
    }
}

u16 TerrainAttributes_GetTile(const u32 mapMatrixIndex, const u32 tileIndex, const TerrainAttributes *terrainAttributes)
{
    u8 blockIndex = terrainAttributes->mapMatrixIndexToBlockIndex[mapMatrixIndex];
    u8 index = (terrainAttributes->packed[blockIndex][tileIndex / 4] >> ((tileIndex % 4) * 2)) & 3;

    return terrainAttributes->palette[blockIndex][index];
}

static void TerrainAttributes_Pack(TerrainAttributes *terrainAttributes, int blockIndex, const u16 *attributes)
{
    u16 *palette = terrainAttributes->palette[blockIndex];
    u8 *packed = terrainAttributes->packed[blockIndex];
    int used = 0;

    MI_CpuClear8(packed, TERRAIN_ATTRIBUTES_COUNT / 4);

    for (int i = 0; i < TERRAIN_ATTRIBUTES_PALETTE_SIZE; i++) {
        palette[i] = 0x8000;
    }

    for (int tile = 0; tile < TERRAIN_ATTRIBUTES_COUNT; tile++) {
        u16 value = attributes[tile];
        int index = 0;

        while (index < used && palette[index] != value) {
            index++;
        }

        if (index == used) {
            if (used < TERRAIN_ATTRIBUTES_PALETTE_SIZE) {
                palette[used++] = value;
            } else {
                for (index = 0; index < used; index++) {
                    if ((palette[index] & 0x8000) == (value & 0x8000)) {
                        break;
                    }
                }

                if (index == used) {
                    index = 0;
                }
            }
        }

        packed[tile / 4] |= index << ((tile % 4) * 2);
    }
}

static void TerrainAttributes_Load(MapMatrix *mapMatrix, TerrainAttributes *terrainAttributes, const u8 blockCount)
{
    u16 mapMatrixIndex;
    u16 landDataID;
    int i, j;
    u16 blockIndexToLandDataID[TERRAIN_ATTRIBUTES_MAX_BLOCK_COUNT];

    u8 realBlockCount = 0;
    int mapMatrixWidth = MapMatrix_GetWidth(mapMatrix);
    int mapMatrixHeight = MapMatrix_GetHeight(mapMatrix);

    for (j = 0; j < mapMatrixHeight; j++) {
        for (i = 0; i < mapMatrixWidth; i++) {
            mapMatrixIndex = j * mapMatrixWidth + i;
            landDataID = MapMatrix_GetLandDataIDByIndex2(mapMatrixIndex, mapMatrix);

            u8 blockIndex = TerrainAttributes_GetOrPushLandDataID(landDataID, blockIndexToLandDataID, &realBlockCount);
            terrainAttributes->mapMatrixIndexToBlockIndex[mapMatrixIndex] = blockIndex;
        }
    }

    NARC *landDataNARC = NARC_ctor(NARC_INDEX_FIELDDATA__LAND_DATA__LAND_DATA, HEAP_ID_FIELD2);
    u16 *buffer = Heap_AllocAtEnd(HEAP_ID_FIELD2, TERRAIN_ATTRIBUTES_SIZE);
    int count = realBlockCount < blockCount ? realBlockCount : blockCount;

    for (i = 0; i < count; i++) {
        landDataID = blockIndexToLandDataID[i];
        NARC_ReadFromMember(landDataNARC, landDataID, TERRAIN_ATTRIBUTES_OFFSET, TERRAIN_ATTRIBUTES_SIZE, buffer);
        TerrainAttributes_Pack(terrainAttributes, i, buffer);
    }

    Heap_Free(buffer);
    NARC_dtor(landDataNARC);
}

static const u8 TerrainAttributes_GetOrPushLandDataID(const u16 landDataID, u16 *blockIndexToLandDataID, u8 *blockCount)
{
    u8 i;

    for (i = 0; i < *blockCount; i++) {
        if (blockIndexToLandDataID[i] == landDataID) {
            return i;
        }
    }

    GF_ASSERT(i < TERRAIN_ATTRIBUTES_MAX_BLOCK_COUNT);

    blockIndexToLandDataID[i] = landDataID;
    (*blockCount)++;

    return i;
}
