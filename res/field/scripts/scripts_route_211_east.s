#include "macros/scrcmd.inc"
#include "res/text/bank/route_211_east.h"


    ScriptEntry Route211East_AceTrainerM
    ScriptEntry Route211East_ArrowSignpostMtCoronet
    ScriptEntry Route211East_TrainerTipsSignpost
    ScriptEntry Route211East_ArrowSignpostCelesticTown
    ScriptEntry Route211East_HoneyTree
    ScriptEntryEnd

Route211East_AceTrainerM:
    PlaySE SE_CONFIRM_sseq_3
    LockAll
    GoToIfSet FLAG_RECEIVED_ROUTE_211_EAST_TM77, Route211East_ExplainPsychUp
    Message Route211East_Text_ImStrong
    CloseMessage
    FacePlayer
    ApplyMovement VAR_LAST_TALKED, Route211East_Movement_ExclamationMark
    WaitMovement
    Message Route211East_Text_YouStartledMe
    SetVar VAR_0x8004, ITEM_TM77
    SetVar VAR_0x8005, 1
    GoToIfCannotFitItem VAR_0x8004, VAR_0x8005, VAR_RESULT, Route211East_BagIsFull
    Common_GiveItemQuantity
    SetFlag FLAG_RECEIVED_ROUTE_211_EAST_TM77
    GoTo Route211East_ExplainPsychUp

Route211East_ExplainPsychUp:
    FacePlayer
    Message Route211East_Text_ExplainPsychUp
    WaitButton
    CloseMessage
    ReleaseAll
    End

Route211East_BagIsFull:
    Common_MessageBagIsFull
    CloseMessage
    ReleaseAll
    End

    .balign 4, 0
Route211East_Movement_ExclamationMark:
    EmoteExclamationMark
    EndMovement

Route211East_ArrowSignpostMtCoronet:
    ShowArrowSign Route211East_Text_SignMtCoronet
    End

Route211East_TrainerTipsSignpost:
    ShowScrollingSign Route211East_Text_TrainerTipsCheckSupply
    End

Route211East_ArrowSignpostCelesticTown:
    ShowArrowSign Route211East_Text_SignCelesticTown
    End

Route211East_HoneyTree:
    PlaySE SE_CONFIRM_sseq_3
    LockAll
    CheckItem ITEM_HONEY, 1, VAR_RESULT
    GoToIfEq VAR_RESULT, FALSE, Route211East_HoneyTreeNoHoney
    Message Route211East_Text_HoneyTreeSlatherBark
    ShowYesNoMenu VAR_RESULT
    GoToIfEq VAR_RESULT, MENU_NO, Route211East_HoneyTreeDeclined
    RemoveItem ITEM_HONEY, 1, VAR_RESULT
    Message Route211East_Text_HoneyTreeBarkSlathered
    WaitButton
    CloseMessage
    WaitTime 30, VAR_RESULT
    Call Route211East_HoneyTreePickSpecies
    PlayCry VAR_0x8004
    WaitCry
    StartLegendaryBattle VAR_0x8004, 12
    ClearFlag FLAG_MAP_LOCAL_REMOVE_OBJECT
    CheckWonBattle VAR_RESULT
    GoToIfEq VAR_RESULT, FALSE, Route211East_HoneyTreeBlackOut
    ReleaseAll
    End

Route211East_HoneyTreeNoHoney:
    Message Route211East_Text_HoneyTreeSweetScent
    WaitButton
    CloseMessage
    ReleaseAll
    End

Route211East_HoneyTreeDeclined:
    CloseMessage
    ReleaseAll
    End

Route211East_HoneyTreePickSpecies:
    GetRandom VAR_RESULT, 13
    SetVar VAR_0x8004, SPECIES_COMBEE
    GoToIfEq VAR_RESULT, 0, Route211East_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_COMBEE
    GoToIfEq VAR_RESULT, 1, Route211East_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_COMBEE
    GoToIfEq VAR_RESULT, 2, Route211East_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_WURMPLE
    GoToIfEq VAR_RESULT, 3, Route211East_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_WURMPLE
    GoToIfEq VAR_RESULT, 4, Route211East_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_BURMY
    GoToIfEq VAR_RESULT, 5, Route211East_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_BURMY
    GoToIfEq VAR_RESULT, 6, Route211East_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_CHERUBI
    GoToIfEq VAR_RESULT, 7, Route211East_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_CHERUBI
    GoToIfEq VAR_RESULT, 8, Route211East_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_AIPOM
    GoToIfEq VAR_RESULT, 9, Route211East_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_AIPOM
    GoToIfEq VAR_RESULT, 10, Route211East_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_HERACROSS
    GoToIfEq VAR_RESULT, 11, Route211East_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_MUNCHLAX
    Return

Route211East_HoneyTreeBlackOut:
    BlackOutFromBattle
    ReleaseAll
    End

Route211East_HoneyTreePickSpeciesEnd:
    Return

    .balign 4, 0
