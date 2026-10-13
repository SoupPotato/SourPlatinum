#include "macros/scrcmd.inc"
#include "res/text/bank/route_208.h"


    ScriptEntry Route208_ArrowSignpostMtCoronet
    ScriptEntry Route208_ArrowSignpostHearthomeCity
    ScriptEntry Route208_SignboardBerryMastersHouse
    ScriptEntry Route208_BlackBelt
    ScriptEntry Route208_TrainerTipsSignpost
    ScriptEntry Route208_HoneyTree
    ScriptEntryEnd

Route208_ArrowSignpostMtCoronet:
    ShowArrowSign Route208_Text_SignMtCoronet
    End

Route208_ArrowSignpostHearthomeCity:
    ShowArrowSign Route208_Text_SignHearthomeCity
    End

Route208_SignboardBerryMastersHouse:
    ShowLandmarkSign Route208_Text_SignBerryMastersHouse
    End

Route208_TrainerTipsSignpost:
    ShowScrollingSign Route208_Text_TrainerTipsWatchBerrySoilColor
    End

Route208_BlackBelt:
    PlaySE SE_CONFIRM_sseq_3
    LockAll
    FacePlayer
    GoToIfSet FLAG_RECEIVED_ROUTE_208_ODD_KEYSTONE, Route208_GoToRoute209
    Message Route208_Text_JustTakeIt
    SetVar VAR_0x8004, ITEM_ODD_KEYSTONE
    SetVar VAR_0x8005, 1
    GoToIfCannotFitItem VAR_0x8004, VAR_0x8005, VAR_RESULT, Route208_BagIsFull
    SetFlag FLAG_RECEIVED_ROUTE_208_ODD_KEYSTONE
    Common_GiveItemQuantityNoLineFeed
    CloseMessage
    ReleaseAll
    End

Route208_GoToRoute209:
    Message Route208_Text_GoToRoute209
    WaitButton
    CloseMessage
    ReleaseAll
    End

Route208_BagIsFull:
    Common_MessageBagIsFull
    CloseMessage
    ReleaseAll
    End

Route208_HoneyTree:
    PlaySE SE_CONFIRM_sseq_3
    LockAll
    CheckItem ITEM_HONEY, 1, VAR_RESULT
    GoToIfEq VAR_RESULT, FALSE, Route208_HoneyTreeNoHoney
    Message Route208_Text_HoneyTreeSlatherBark
    ShowYesNoMenu VAR_RESULT
    GoToIfEq VAR_RESULT, MENU_NO, Route208_HoneyTreeDeclined
    RemoveItem ITEM_HONEY, 1, VAR_RESULT
    Message Route208_Text_HoneyTreeBarkSlathered
    WaitButton
    CloseMessage
    WaitTime 30, VAR_RESULT
    Call Route208_HoneyTreePickSpecies
    PlayCry VAR_0x8004
    WaitCry
    StartLegendaryBattle VAR_0x8004, 12
    ClearFlag FLAG_MAP_LOCAL_REMOVE_OBJECT
    CheckWonBattle VAR_RESULT
    GoToIfEq VAR_RESULT, FALSE, Route208_HoneyTreeBlackOut
    ReleaseAll
    End

Route208_HoneyTreeNoHoney:
    Message Route208_Text_HoneyTreeSweetScent
    WaitButton
    CloseMessage
    ReleaseAll
    End

Route208_HoneyTreeDeclined:
    CloseMessage
    ReleaseAll
    End

Route208_HoneyTreePickSpecies:
    GetRandom VAR_RESULT, 13
    SetVar VAR_0x8004, SPECIES_COMBEE
    GoToIfEq VAR_RESULT, 0, Route208_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_COMBEE
    GoToIfEq VAR_RESULT, 1, Route208_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_COMBEE
    GoToIfEq VAR_RESULT, 2, Route208_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_WURMPLE
    GoToIfEq VAR_RESULT, 3, Route208_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_WURMPLE
    GoToIfEq VAR_RESULT, 4, Route208_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_BURMY
    GoToIfEq VAR_RESULT, 5, Route208_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_BURMY
    GoToIfEq VAR_RESULT, 6, Route208_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_CHERUBI
    GoToIfEq VAR_RESULT, 7, Route208_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_CHERUBI
    GoToIfEq VAR_RESULT, 8, Route208_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_AIPOM
    GoToIfEq VAR_RESULT, 9, Route208_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_AIPOM
    GoToIfEq VAR_RESULT, 10, Route208_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_HERACROSS
    GoToIfEq VAR_RESULT, 11, Route208_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_MUNCHLAX
    Return

Route208_HoneyTreeBlackOut:
    BlackOutFromBattle
    ReleaseAll
    End

Route208_HoneyTreePickSpeciesEnd:
    Return

    .balign 4, 0
