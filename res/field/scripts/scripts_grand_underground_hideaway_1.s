#include "macros/scrcmd.inc"
#include "res/text/bank/grand_underground_hideaway_1.h"
#include "res/field/events/events_grand_underground_hideaway_1.h"


    ScriptEntry GrandUndergroundHideaway1_Machop
    ScriptEntry GrandUndergroundHideaway1_Psyduck
    ScriptEntry GrandUndergroundHideaway1_Clefairy
    ScriptEntry GrandUndergroundHideaway1_Skitty
    ScriptEntry GrandUndergroundHideaway1_Buneary
    ScriptEntry GrandUndergroundHideaway1_Exit
    ScriptEntryEnd

GrandUndergroundHideaway1_Machop:
    LockAll
    PlayCry SPECIES_MACHOP
    WaitCry
    StartWildBattle SPECIES_MACHOP, 20
    CheckWonBattle VAR_RESULT
    GoToIfEq VAR_RESULT, FALSE, GrandUndergroundHideaway1_BlackOut
    RemoveObject LOCALID_MACHOP
    ReleaseAll
    End

GrandUndergroundHideaway1_Psyduck:
    LockAll
    PlayCry SPECIES_PSYDUCK
    WaitCry
    StartWildBattle SPECIES_PSYDUCK, 20
    CheckWonBattle VAR_RESULT
    GoToIfEq VAR_RESULT, FALSE, GrandUndergroundHideaway1_BlackOut
    RemoveObject LOCALID_PSYDUCK
    ReleaseAll
    End

GrandUndergroundHideaway1_Clefairy:
    LockAll
    PlayCry SPECIES_CLEFAIRY
    WaitCry
    StartWildBattle SPECIES_CLEFAIRY, 20
    CheckWonBattle VAR_RESULT
    GoToIfEq VAR_RESULT, FALSE, GrandUndergroundHideaway1_BlackOut
    RemoveObject LOCALID_CLEFAIRY
    ReleaseAll
    End

GrandUndergroundHideaway1_Skitty:
    LockAll
    PlayCry SPECIES_SKITTY
    WaitCry
    StartWildBattle SPECIES_SKITTY, 20
    CheckWonBattle VAR_RESULT
    GoToIfEq VAR_RESULT, FALSE, GrandUndergroundHideaway1_BlackOut
    RemoveObject LOCALID_SKITTY
    ReleaseAll
    End

GrandUndergroundHideaway1_Buneary:
    LockAll
    PlayCry SPECIES_BUNEARY
    WaitCry
    StartWildBattle SPECIES_BUNEARY, 20
    CheckWonBattle VAR_RESULT
    GoToIfEq VAR_RESULT, FALSE, GrandUndergroundHideaway1_BlackOut
    RemoveObject LOCALID_BUNEARY
    ReleaseAll
    End

GrandUndergroundHideaway1_Exit:
    LockAll
    Message GrandUndergroundHideaway1_Text_ReturnToTheUnderground
    ShowYesNoMenu VAR_RESULT
    GoToIfEq VAR_RESULT, MENU_NO, GrandUndergroundHideaway1_StayInside
    CloseMessage
    ReturnToUnderground VAR_HIDEAWAY_RETURN_X, VAR_HIDEAWAY_RETURN_Z
    End

GrandUndergroundHideaway1_StayInside:
    CloseMessage
    ApplyMovement LOCALID_PLAYER, GrandUndergroundHideaway1_Movement_StepBack
    WaitMovement
    ReleaseAll
    End

GrandUndergroundHideaway1_BlackOut:
    BlackOutFromBattle
    ReleaseAll
    End

    .balign 4, 0
GrandUndergroundHideaway1_Movement_StepBack:
    WalkNormalSouth
    EndMovement
