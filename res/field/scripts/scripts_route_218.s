#include "macros/scrcmd.inc"
#include "res/text/bank/route_218.h"


    ScriptEntry Route218_ArrowSignpostCanalaveCity
    ScriptEntry Route218_ArrowSignpostJubilifeCity
    ScriptEntry Route218_Guitarist
    ScriptEntry Route218_Fisherman
    ScriptEntry Route218_ClefairySouth
    ScriptEntry Route218_ClefairyNorth
    ScriptEntry Route218_Pikachu
    ScriptEntry Route218_HoneyTree
    ScriptEntryEnd

Route218_ArrowSignpostCanalaveCity:
    ShowArrowSign Route218_Text_SignCanalaveCity
    End

Route218_ArrowSignpostJubilifeCity:
    ShowArrowSign Route218_Text_SignJubilifeCity
    End

Route218_Guitarist:
    EventMessage Route218_Text_ClefairyCuterNow
    End

Route218_Fisherman:
    EventMessage Route218_Text_PikachuDazzle
    End

Route218_ClefairySouth:
    PlaySE SE_CONFIRM_sseq_3
    LockAll
    WaitSE SE_CONFIRM_sseq_3
    PlayCry SPECIES_CLEFAIRY
    Message Route218_Text_ClefairyCryPippiih
    WaitCry
    WaitButton
    CloseMessage
    ReleaseAll
    End

Route218_ClefairyNorth:
    PlaySE SE_CONFIRM_sseq_3
    LockAll
    WaitSE SE_CONFIRM_sseq_3
    PlayCry SPECIES_CLEFAIRY
    Message Route218_Text_ClefairyCryPippippiih
    WaitCry
    WaitButton
    CloseMessage
    ReleaseAll
    End

Route218_Pikachu:
    PlaySE SE_CONFIRM_sseq_3
    LockAll
    WaitSE SE_CONFIRM_sseq_3
    PlayCry SPECIES_PIKACHU
    Message Route218_Text_PikachuCry
    WaitCry
    WaitButton
    CloseMessage
    ReleaseAll
    End

Route218_HoneyTree:
    PlaySE SE_CONFIRM_sseq_3
    LockAll
    CheckItem ITEM_HONEY, 1, VAR_RESULT
    GoToIfEq VAR_RESULT, FALSE, Route218_HoneyTreeNoHoney
    Message Route218_Text_HoneyTreeSlatherBark
    ShowYesNoMenu VAR_RESULT
    GoToIfEq VAR_RESULT, MENU_NO, Route218_HoneyTreeDeclined
    RemoveItem ITEM_HONEY, 1, VAR_RESULT
    Message Route218_Text_HoneyTreeBarkSlathered
    WaitButton
    CloseMessage
    WaitTime 30, VAR_RESULT
    Call Route218_HoneyTreePickSpecies
    PlayCry VAR_0x8004
    WaitCry
    StartLegendaryBattle VAR_0x8004, 12
    ClearFlag FLAG_MAP_LOCAL_REMOVE_OBJECT
    CheckWonBattle VAR_RESULT
    GoToIfEq VAR_RESULT, FALSE, Route218_HoneyTreeBlackOut
    ReleaseAll
    End

Route218_HoneyTreeNoHoney:
    Message Route218_Text_HoneyTreeSweetScent
    WaitButton
    CloseMessage
    ReleaseAll
    End

Route218_HoneyTreeDeclined:
    CloseMessage
    ReleaseAll
    End

Route218_HoneyTreePickSpecies:
    GetRandom VAR_RESULT, 13
    SetVar VAR_0x8004, SPECIES_COMBEE
    GoToIfEq VAR_RESULT, 0, Route218_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_COMBEE
    GoToIfEq VAR_RESULT, 1, Route218_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_COMBEE
    GoToIfEq VAR_RESULT, 2, Route218_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_WURMPLE
    GoToIfEq VAR_RESULT, 3, Route218_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_WURMPLE
    GoToIfEq VAR_RESULT, 4, Route218_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_BURMY
    GoToIfEq VAR_RESULT, 5, Route218_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_BURMY
    GoToIfEq VAR_RESULT, 6, Route218_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_CHERUBI
    GoToIfEq VAR_RESULT, 7, Route218_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_CHERUBI
    GoToIfEq VAR_RESULT, 8, Route218_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_AIPOM
    GoToIfEq VAR_RESULT, 9, Route218_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_AIPOM
    GoToIfEq VAR_RESULT, 10, Route218_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_HERACROSS
    GoToIfEq VAR_RESULT, 11, Route218_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_MUNCHLAX
    Return

Route218_HoneyTreeBlackOut:
    BlackOutFromBattle
    ReleaseAll
    End

Route218_HoneyTreePickSpeciesEnd:
    Return

    .balign 4, 0
