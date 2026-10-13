#include "macros/scrcmd.inc"
#include "res/text/bank/fuego_ironworks_outside.h"


    ScriptEntry FuegoIronworksOutside_Signboard
    ScriptEntry FuegoIronworksOutside_HoneyTree
    ScriptEntryEnd

FuegoIronworksOutside_Signboard:
    ShowLandmarkSign FuegoIronworksOutside_Text_SignFuegoIronworks
    End

FuegoIronworksOutside_HoneyTree:
    PlaySE SE_CONFIRM_sseq_3
    LockAll
    CheckItem ITEM_HONEY, 1, VAR_RESULT
    GoToIfEq VAR_RESULT, FALSE, FuegoIronworksOutside_HoneyTreeNoHoney
    Message FuegoIronworksOutside_Text_HoneyTreeSlatherBark
    ShowYesNoMenu VAR_RESULT
    GoToIfEq VAR_RESULT, MENU_NO, FuegoIronworksOutside_HoneyTreeDeclined
    RemoveItem ITEM_HONEY, 1, VAR_RESULT
    Message FuegoIronworksOutside_Text_HoneyTreeBarkSlathered
    WaitButton
    CloseMessage
    WaitTime 30, VAR_RESULT
    Call FuegoIronworksOutside_HoneyTreePickSpecies
    PlayCry VAR_0x8004
    WaitCry
    StartLegendaryBattle VAR_0x8004, 12
    ClearFlag FLAG_MAP_LOCAL_REMOVE_OBJECT
    CheckWonBattle VAR_RESULT
    GoToIfEq VAR_RESULT, FALSE, FuegoIronworksOutside_HoneyTreeBlackOut
    ReleaseAll
    End

FuegoIronworksOutside_HoneyTreeNoHoney:
    Message FuegoIronworksOutside_Text_HoneyTreeSweetScent
    WaitButton
    CloseMessage
    ReleaseAll
    End

FuegoIronworksOutside_HoneyTreeDeclined:
    CloseMessage
    ReleaseAll
    End

FuegoIronworksOutside_HoneyTreePickSpecies:
    GetRandom VAR_RESULT, 13
    SetVar VAR_0x8004, SPECIES_COMBEE
    GoToIfEq VAR_RESULT, 0, FuegoIronworksOutside_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_COMBEE
    GoToIfEq VAR_RESULT, 1, FuegoIronworksOutside_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_COMBEE
    GoToIfEq VAR_RESULT, 2, FuegoIronworksOutside_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_WURMPLE
    GoToIfEq VAR_RESULT, 3, FuegoIronworksOutside_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_WURMPLE
    GoToIfEq VAR_RESULT, 4, FuegoIronworksOutside_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_BURMY
    GoToIfEq VAR_RESULT, 5, FuegoIronworksOutside_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_BURMY
    GoToIfEq VAR_RESULT, 6, FuegoIronworksOutside_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_CHERUBI
    GoToIfEq VAR_RESULT, 7, FuegoIronworksOutside_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_CHERUBI
    GoToIfEq VAR_RESULT, 8, FuegoIronworksOutside_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_AIPOM
    GoToIfEq VAR_RESULT, 9, FuegoIronworksOutside_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_AIPOM
    GoToIfEq VAR_RESULT, 10, FuegoIronworksOutside_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_HERACROSS
    GoToIfEq VAR_RESULT, 11, FuegoIronworksOutside_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_MUNCHLAX
    Return

FuegoIronworksOutside_HoneyTreeBlackOut:
    BlackOutFromBattle
    ReleaseAll
    End

FuegoIronworksOutside_HoneyTreePickSpeciesEnd:
    Return

    .balign 4, 0
