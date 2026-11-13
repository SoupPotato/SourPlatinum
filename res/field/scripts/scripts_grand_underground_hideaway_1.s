#include "macros/scrcmd.inc"
#include "res/text/bank/grand_underground_hideaway_1.h"
#include "res/field/events/events_grand_underground_hideaway_1.h"


    ScriptEntry GrandUndergroundHideaway1_ExitNorth
    ScriptEntry GrandUndergroundHideaway1_ExitWest
    ScriptEntry GrandUndergroundHideaway1_ExitEast
    ScriptEntry GrandUndergroundHideaway1_ExitSouth
    ScriptEntryEnd

GrandUndergroundHideaway1_ExitNorth:
    LockAll
    Message GrandUndergroundHideaway1_Text_ReturnToTheUnderground
    ShowYesNoMenu VAR_RESULT
    GoToIfEq VAR_RESULT, MENU_NO, GrandUndergroundHideaway1_StayNorth
    CloseMessage
    ReturnToUnderground VAR_HIDEAWAY_RETURN_X, VAR_HIDEAWAY_RETURN_Z
    End

GrandUndergroundHideaway1_StayNorth:
    CloseMessage
    ApplyMovement LOCALID_PLAYER, GrandUndergroundHideaway1_Movement_StepBackNorth
    WaitMovement
    ReleaseAll
    End

GrandUndergroundHideaway1_ExitWest:
    LockAll
    Message GrandUndergroundHideaway1_Text_ReturnToTheUnderground
    ShowYesNoMenu VAR_RESULT
    GoToIfEq VAR_RESULT, MENU_NO, GrandUndergroundHideaway1_StayWest
    CloseMessage
    ReturnToUnderground VAR_HIDEAWAY_RETURN_X, VAR_HIDEAWAY_RETURN_Z
    End

GrandUndergroundHideaway1_StayWest:
    CloseMessage
    ApplyMovement LOCALID_PLAYER, GrandUndergroundHideaway1_Movement_StepBackWest
    WaitMovement
    ReleaseAll
    End

GrandUndergroundHideaway1_ExitEast:
    LockAll
    Message GrandUndergroundHideaway1_Text_ReturnToTheUnderground
    ShowYesNoMenu VAR_RESULT
    GoToIfEq VAR_RESULT, MENU_NO, GrandUndergroundHideaway1_StayEast
    CloseMessage
    ReturnToUnderground VAR_HIDEAWAY_RETURN_X, VAR_HIDEAWAY_RETURN_Z
    End

GrandUndergroundHideaway1_StayEast:
    CloseMessage
    ApplyMovement LOCALID_PLAYER, GrandUndergroundHideaway1_Movement_StepBackEast
    WaitMovement
    ReleaseAll
    End

GrandUndergroundHideaway1_ExitSouth:
    LockAll
    Message GrandUndergroundHideaway1_Text_ReturnToTheUnderground
    ShowYesNoMenu VAR_RESULT
    GoToIfEq VAR_RESULT, MENU_NO, GrandUndergroundHideaway1_StaySouth
    CloseMessage
    ReturnToUnderground VAR_HIDEAWAY_RETURN_X, VAR_HIDEAWAY_RETURN_Z
    End

GrandUndergroundHideaway1_StaySouth:
    CloseMessage
    ApplyMovement LOCALID_PLAYER, GrandUndergroundHideaway1_Movement_StepBackSouth
    WaitMovement
    ReleaseAll
    End

    .balign 4, 0
GrandUndergroundHideaway1_Movement_StepBackNorth:
    WalkNormalSouth
    EndMovement

GrandUndergroundHideaway1_Movement_StepBackWest:
    WalkNormalEast
    EndMovement

GrandUndergroundHideaway1_Movement_StepBackEast:
    WalkNormalWest
    EndMovement

GrandUndergroundHideaway1_Movement_StepBackSouth:
    WalkNormalNorth
    EndMovement
