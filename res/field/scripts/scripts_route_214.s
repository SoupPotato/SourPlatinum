#include "macros/scrcmd.inc"
#include "res/text/bank/route_214.h"


    ScriptEntry Route214_ArrowSignpostVeilstoneCity
    ScriptEntry Route214_ArrowSignpostLakeValor
    ScriptEntry Route214_OnTransition
    ScriptEntry Route214_OnLoad
    ScriptEntry Route214_HoneyTree
    ScriptEntryEnd

Route214_OnLoad:
    GetUnownFormsSeenCount VAR_MAP_LOCAL_0x00
    GoToIfGe VAR_MAP_LOCAL_0x00, 26, Route214_RemoveWarpsManiacCaveShortAndLong
    GoToIfGe VAR_MAP_LOCAL_0x00, 10, Route214_RemoveWarpsManiacCaveShortAndTunnel
    GoToIfLt VAR_MAP_LOCAL_0x00, 10, Route214_RemoveWarpsManiacCaveLongAndTunnel
    End

Route214_RemoveWarpsManiacCaveShortAndLong:
    SetWarpEventPos 2, 710, 670
    SetWarpEventPos 3, 710, 670
    End

Route214_RemoveWarpsManiacCaveShortAndTunnel:
    SetWarpEventPos 2, 710, 670
    SetWarpEventPos 4, 710, 670
    End

Route214_RemoveWarpsManiacCaveLongAndTunnel:
    SetWarpEventPos 3, 710, 670
    SetWarpEventPos 4, 710, 670
    End

Route214_OnTransition:
    GetUnownFormsSeenCount VAR_MAP_LOCAL_0x00
    GoToIfGe VAR_MAP_LOCAL_0x00, 26, Route214_RemoveWarpsManiacCaveShortAndLong
    GoToIfGe VAR_MAP_LOCAL_0x00, 10, Route214_RemoveWarpsManiacCaveShortAndTunnel
    GoToIfLt VAR_MAP_LOCAL_0x00, 10, Route214_RemoveWarpsManiacCaveLongAndTunnel
    End

Route214_ArrowSignpostVeilstoneCity:
    ShowArrowSign Route214_Text_SignVeilstoneCity
    End

Route214_ArrowSignpostLakeValor:
    ShowArrowSign Route214_Text_SignLakeValor
    End

Route214_HoneyTree:
    PlaySE SE_CONFIRM_sseq_3
    LockAll
    CheckItem ITEM_HONEY, 1, VAR_RESULT
    GoToIfEq VAR_RESULT, FALSE, Route214_HoneyTreeNoHoney
    Message Route214_Text_HoneyTreeSlatherBark
    ShowYesNoMenu VAR_RESULT
    GoToIfEq VAR_RESULT, MENU_NO, Route214_HoneyTreeDeclined
    RemoveItem ITEM_HONEY, 1, VAR_RESULT
    Message Route214_Text_HoneyTreeBarkSlathered
    WaitButton
    CloseMessage
    WaitTime 30, VAR_RESULT
    Call Route214_HoneyTreePickSpecies
    PlayCry VAR_0x8004
    WaitCry
    StartLegendaryBattle VAR_0x8004, 12
    ClearFlag FLAG_MAP_LOCAL_REMOVE_OBJECT
    CheckWonBattle VAR_RESULT
    GoToIfEq VAR_RESULT, FALSE, Route214_HoneyTreeBlackOut
    ReleaseAll
    End

Route214_HoneyTreeNoHoney:
    Message Route214_Text_HoneyTreeSweetScent
    WaitButton
    CloseMessage
    ReleaseAll
    End

Route214_HoneyTreeDeclined:
    CloseMessage
    ReleaseAll
    End

Route214_HoneyTreePickSpecies:
    GetRandom VAR_RESULT, 13
    SetVar VAR_0x8004, SPECIES_COMBEE
    GoToIfEq VAR_RESULT, 0, Route214_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_COMBEE
    GoToIfEq VAR_RESULT, 1, Route214_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_COMBEE
    GoToIfEq VAR_RESULT, 2, Route214_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_WURMPLE
    GoToIfEq VAR_RESULT, 3, Route214_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_WURMPLE
    GoToIfEq VAR_RESULT, 4, Route214_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_BURMY
    GoToIfEq VAR_RESULT, 5, Route214_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_BURMY
    GoToIfEq VAR_RESULT, 6, Route214_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_CHERUBI
    GoToIfEq VAR_RESULT, 7, Route214_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_CHERUBI
    GoToIfEq VAR_RESULT, 8, Route214_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_AIPOM
    GoToIfEq VAR_RESULT, 9, Route214_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_AIPOM
    GoToIfEq VAR_RESULT, 10, Route214_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_HERACROSS
    GoToIfEq VAR_RESULT, 11, Route214_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_MUNCHLAX
    Return

Route214_HoneyTreeBlackOut:
    BlackOutFromBattle
    ReleaseAll
    End

Route214_HoneyTreePickSpeciesEnd:
    Return
