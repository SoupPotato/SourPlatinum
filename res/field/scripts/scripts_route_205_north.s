#include "macros/scrcmd.inc"
#include "res/text/bank/route_205_north.h"


    ScriptEntry Route205North_Fisherman
    ScriptEntry Route205North_ArrowSignpostEternaForest
    ScriptEntry Route205North_ArrowSignpostEternaCity
    ScriptEntry Route205North_HoneyTree
    ScriptEntryEnd

Route205North_Fisherman:
    NPCMessage Route205North_Text_FishCasually
    End

Route205North_ArrowSignpostEternaForest:
    ShowArrowSign Route205North_Text_SignEternaForest
    End

Route205North_ArrowSignpostEternaCity:
    ShowArrowSign Route205North_Text_SignEternaCity
    End

Route205North_HoneyTree:
    PlaySE SE_CONFIRM_sseq_3
    LockAll
    CheckItem ITEM_HONEY, 1, VAR_RESULT
    GoToIfEq VAR_RESULT, FALSE, Route205North_HoneyTreeNoHoney
    Message Route205North_Text_HoneyTreeSlatherBark
    ShowYesNoMenu VAR_RESULT
    GoToIfEq VAR_RESULT, MENU_NO, Route205North_HoneyTreeDeclined
    RemoveItem ITEM_HONEY, 1, VAR_RESULT
    Message Route205North_Text_HoneyTreeBarkSlathered
    WaitButton
    CloseMessage
    WaitTime 30, VAR_RESULT
    Call Route205North_HoneyTreePickSpecies
    PlayCry VAR_0x8004
    WaitCry
    StartLegendaryBattle VAR_0x8004, 12
    ClearFlag FLAG_MAP_LOCAL_REMOVE_OBJECT
    CheckWonBattle VAR_RESULT
    GoToIfEq VAR_RESULT, FALSE, Route205North_HoneyTreeBlackOut
    ReleaseAll
    End

Route205North_HoneyTreeNoHoney:
    Message Route205North_Text_HoneyTreeSweetScent
    WaitButton
    CloseMessage
    ReleaseAll
    End

Route205North_HoneyTreeDeclined:
    CloseMessage
    ReleaseAll
    End

Route205North_HoneyTreePickSpecies:
    GetRandom VAR_RESULT, 13
    SetVar VAR_0x8004, SPECIES_COMBEE
    GoToIfEq VAR_RESULT, 0, Route205North_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_COMBEE
    GoToIfEq VAR_RESULT, 1, Route205North_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_COMBEE
    GoToIfEq VAR_RESULT, 2, Route205North_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_WURMPLE
    GoToIfEq VAR_RESULT, 3, Route205North_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_WURMPLE
    GoToIfEq VAR_RESULT, 4, Route205North_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_BURMY
    GoToIfEq VAR_RESULT, 5, Route205North_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_BURMY
    GoToIfEq VAR_RESULT, 6, Route205North_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_CHERUBI
    GoToIfEq VAR_RESULT, 7, Route205North_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_CHERUBI
    GoToIfEq VAR_RESULT, 8, Route205North_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_AIPOM
    GoToIfEq VAR_RESULT, 9, Route205North_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_AIPOM
    GoToIfEq VAR_RESULT, 10, Route205North_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_HERACROSS
    GoToIfEq VAR_RESULT, 11, Route205North_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_MUNCHLAX
    Return

Route205North_HoneyTreeBlackOut:
    BlackOutFromBattle
    ReleaseAll
    End

Route205North_HoneyTreePickSpeciesEnd:
    Return

    .balign 4, 0
