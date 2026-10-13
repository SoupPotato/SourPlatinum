#include "macros/scrcmd.inc"
#include "res/text/bank/eterna_forest_outside.h"


    ScriptEntry EternaForestOutside_OnTransition
    ScriptEntry EternaForestOutside_Dummy2
    ScriptEntry EternaForestOutside_Dummy3
    ScriptEntry EternaForestOutside_PokemonBreederF
    ScriptEntry EternaForestOutside_HoneyTree
    ScriptEntryEnd

EternaForestOutside_OnTransition:
    SetFlag FLAG_FIRST_ARRIVAL_ETERNA_FOREST
    End

EternaForestOutside_PokemonBreederF:
    PlaySE SE_CONFIRM_sseq_3
    LockAll
    FacePlayer
    GoToIfSet FLAG_RECEIVED_ETERNA_FOREST_OUTSIDE_ACCESSORY_BIG_TREE, EternaForestOutside_ITradeBerriesForAccessories
    SetVar VAR_0x8004, ACCESSORY_BIG_TREE
    BufferAccessoryName 0, VAR_0x8004
    Message EternaForestOutside_Text_AreYouCollectingAccessories
    SetVar VAR_0x8005, 1
    Common_GiveAccessoryWaitForConfirm
    SetFlag FLAG_RECEIVED_ETERNA_FOREST_OUTSIDE_ACCESSORY_BIG_TREE
    CloseMessage
    ReleaseAll
    End

EternaForestOutside_ITradeBerriesForAccessories:
    Message EternaForestOutside_Text_ITradeBerriesForAccessories
    WaitButton
    CloseMessage
    ReleaseAll
    End

EternaForestOutside_Dummy2:
    ShowLandmarkSign EternaForestOutside_Text_HoneyTreeSlatherBark
    End

EternaForestOutside_Dummy3:
    ShowScrollingSign EternaForestOutside_Text_HoneyTreeBarkSlathered
    End

EternaForestOutside_HoneyTree:
    PlaySE SE_CONFIRM_sseq_3
    LockAll
    CheckItem ITEM_HONEY, 1, VAR_RESULT
    GoToIfEq VAR_RESULT, FALSE, EternaForestOutside_HoneyTreeNoHoney
    Message EternaForestOutside_Text_HoneyTreeSlatherBark
    ShowYesNoMenu VAR_RESULT
    GoToIfEq VAR_RESULT, MENU_NO, EternaForestOutside_HoneyTreeDeclined
    RemoveItem ITEM_HONEY, 1, VAR_RESULT
    Message EternaForestOutside_Text_HoneyTreeBarkSlathered
    WaitButton
    CloseMessage
    WaitTime 30, VAR_RESULT
    Call EternaForestOutside_HoneyTreePickSpecies
    PlayCry VAR_0x8004
    WaitCry
    StartLegendaryBattle VAR_0x8004, 12
    ClearFlag FLAG_MAP_LOCAL_REMOVE_OBJECT
    CheckWonBattle VAR_RESULT
    GoToIfEq VAR_RESULT, FALSE, EternaForestOutside_HoneyTreeBlackOut
    ReleaseAll
    End

EternaForestOutside_HoneyTreeNoHoney:
    Message EternaForestOutside_Text_HoneyTreeSweetScent
    WaitButton
    CloseMessage
    ReleaseAll
    End

EternaForestOutside_HoneyTreeDeclined:
    CloseMessage
    ReleaseAll
    End

EternaForestOutside_HoneyTreePickSpecies:
    GetRandom VAR_RESULT, 13
    SetVar VAR_0x8004, SPECIES_COMBEE
    GoToIfEq VAR_RESULT, 0, EternaForestOutside_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_COMBEE
    GoToIfEq VAR_RESULT, 1, EternaForestOutside_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_COMBEE
    GoToIfEq VAR_RESULT, 2, EternaForestOutside_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_WURMPLE
    GoToIfEq VAR_RESULT, 3, EternaForestOutside_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_WURMPLE
    GoToIfEq VAR_RESULT, 4, EternaForestOutside_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_BURMY
    GoToIfEq VAR_RESULT, 5, EternaForestOutside_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_BURMY
    GoToIfEq VAR_RESULT, 6, EternaForestOutside_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_CHERUBI
    GoToIfEq VAR_RESULT, 7, EternaForestOutside_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_CHERUBI
    GoToIfEq VAR_RESULT, 8, EternaForestOutside_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_AIPOM
    GoToIfEq VAR_RESULT, 9, EternaForestOutside_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_AIPOM
    GoToIfEq VAR_RESULT, 10, EternaForestOutside_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_HERACROSS
    GoToIfEq VAR_RESULT, 11, EternaForestOutside_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_MUNCHLAX
    Return

EternaForestOutside_HoneyTreeBlackOut:
    BlackOutFromBattle
    ReleaseAll
    End

EternaForestOutside_HoneyTreePickSpeciesEnd:
    Return
