#include "macros/scrcmd.inc"
#include "res/text/bank/route_206.h"


    ScriptEntry Route206_OnTransition
    ScriptEntry Route206_OnResume
    ScriptEntry Route206_Hiker
    ScriptEntry Route206_ArrowSignpostEternaCity
    ScriptEntry Route206_ArrowSignpostOreburghCity
    ScriptEntry Route206_HoneyTree
    ScriptEntryEnd

Route206_OnTransition:
    SetFlag FLAG_FIRST_ARRIVAL_CYCLING_ROAD_UNUSED
    End

Route206_OnResume:
    CallIfSet FLAG_ON_CYCLING_ROAD, Route206_ForceBicycling
    GetPreviousMapID VAR_MAP_LOCAL_0x00
    GoToIfEq VAR_MAP_LOCAL_0x00, MAP_HEADER_ROUTE_206_CYCLING_ROAD_NORTH_GATE, Route206_TrySetFlagsCyclingRoad
    GoToIfEq VAR_MAP_LOCAL_0x00, MAP_HEADER_ROUTE_206_CYCLING_ROAD_SOUTH_GATE, Route206_TrySetFlagsCyclingRoad
    End

Route206_TrySetFlagsCyclingRoad:
    GoToIfSet FLAG_MAP_LOCAL_0x03, Route206_OnResumeEnd
    GetPlayerMapPos VAR_MAP_LOCAL_0x00, VAR_MAP_LOCAL_0x01
    GoToIfLt VAR_MAP_LOCAL_0x00, 299, Route206_OnResumeEnd
    GoToIfGt VAR_MAP_LOCAL_0x00, 306, Route206_OnResumeEnd
    GoToIfEq VAR_MAP_LOCAL_0x01, 576, Route206_SetFlagsCyclingRoad
    GoToIfEq VAR_MAP_LOCAL_0x01, 681, Route206_SetFlagsCyclingRoad
    End

Route206_SetFlagsCyclingRoad:
    SetFlag FLAG_MAP_LOCAL_0x03
    SetFlag FLAG_ON_CYCLING_ROAD
    SetCyclingBGM
    ForceBicycling TRUE
    End

Route206_OnResumeEnd:
    End

Route206_ForceBicycling:
    ForceBicycling TRUE
    Return

Route206_Hiker:
    NPCMessage Route206_Text_TwoCavesOnRoute206
    End

Route206_ArrowSignpostEternaCity:
    ShowArrowSign Route206_Text_SignEternaCity
    End

Route206_ArrowSignpostOreburghCity:
    ShowArrowSign Route206_Text_SignOreburghCity
    End

Route206_HoneyTree:
    PlaySE SE_CONFIRM_sseq_3
    LockAll
    CheckItem ITEM_HONEY, 1, VAR_RESULT
    GoToIfEq VAR_RESULT, FALSE, Route206_HoneyTreeNoHoney
    Message Route206_Text_HoneyTreeSlatherBark
    ShowYesNoMenu VAR_RESULT
    GoToIfEq VAR_RESULT, MENU_NO, Route206_HoneyTreeDeclined
    RemoveItem ITEM_HONEY, 1, VAR_RESULT
    Message Route206_Text_HoneyTreeBarkSlathered
    WaitButton
    CloseMessage
    WaitTime 30, VAR_RESULT
    Call Route206_HoneyTreePickSpecies
    PlayCry VAR_0x8004
    WaitCry
    StartLegendaryBattle VAR_0x8004, 12
    ClearFlag FLAG_MAP_LOCAL_REMOVE_OBJECT
    CheckWonBattle VAR_RESULT
    GoToIfEq VAR_RESULT, FALSE, Route206_HoneyTreeBlackOut
    ReleaseAll
    End

Route206_HoneyTreeNoHoney:
    Message Route206_Text_HoneyTreeSweetScent
    WaitButton
    CloseMessage
    ReleaseAll
    End

Route206_HoneyTreeDeclined:
    CloseMessage
    ReleaseAll
    End

Route206_HoneyTreePickSpecies:
    GetRandom VAR_RESULT, 13
    SetVar VAR_0x8004, SPECIES_COMBEE
    GoToIfEq VAR_RESULT, 0, Route206_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_COMBEE
    GoToIfEq VAR_RESULT, 1, Route206_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_COMBEE
    GoToIfEq VAR_RESULT, 2, Route206_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_WURMPLE
    GoToIfEq VAR_RESULT, 3, Route206_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_WURMPLE
    GoToIfEq VAR_RESULT, 4, Route206_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_BURMY
    GoToIfEq VAR_RESULT, 5, Route206_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_BURMY
    GoToIfEq VAR_RESULT, 6, Route206_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_CHERUBI
    GoToIfEq VAR_RESULT, 7, Route206_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_CHERUBI
    GoToIfEq VAR_RESULT, 8, Route206_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_AIPOM
    GoToIfEq VAR_RESULT, 9, Route206_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_AIPOM
    GoToIfEq VAR_RESULT, 10, Route206_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_HERACROSS
    GoToIfEq VAR_RESULT, 11, Route206_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_MUNCHLAX
    Return

Route206_HoneyTreeBlackOut:
    BlackOutFromBattle
    ReleaseAll
    End

Route206_HoneyTreePickSpeciesEnd:
    Return

    .balign 4, 0
