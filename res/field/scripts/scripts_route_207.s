#include "macros/scrcmd.inc"
#include "res/text/bank/menu_entries.h"
#include "res/text/bank/route_207.h"
#include "res/field/events/events_route_207.h"


    ScriptEntry Route207_OnTransition
    ScriptEntry Route207_CoordEvent_Counterpart
    ScriptEntry Route207_Dummy3
    ScriptEntry Route207_CyclistM
    ScriptEntry Route207_ArrowSignpostMtCoronet
    ScriptEntry Route207_ArrowSignpostOreburghCity
    ScriptEntry Route207_TrainerTipsSignpost
    ScriptEntry Route207_HoneyTree
    ScriptEntryEnd

Route207_OnTransition:
    GetPlayerGender VAR_MAP_LOCAL_0x00
    GoToIfEq VAR_MAP_LOCAL_0x00, GENDER_MALE, Route207_SetCounterpartGraphicsDawn
    GoToIfEq VAR_MAP_LOCAL_0x00, GENDER_FEMALE, Route207_SetCounterpartGraphicsLucas
    End

Route207_SetCounterpartGraphicsDawn:
    SetVar VAR_OBJ_GFX_ID_0, OBJ_EVENT_GFX_PLAYER_F
    End

Route207_SetCounterpartGraphicsLucas:
    SetVar VAR_OBJ_GFX_ID_0, OBJ_EVENT_GFX_PLAYER_M
    End

Route207_CoordEvent_Counterpart:
    LockAll
    GetPlayerMapPos VAR_0x8004, VAR_0x8005
    SetObjectEventPos LOCALID_COUNTERPART, 331, VAR_0x8005
    Call Route207_ShowCounterpart
    ApplyMovement LOCALID_COUNTERPART, Route207_Movement_CounterpartNoticePlayer
    WaitMovement
    Common_SetCounterpartBGM
    ApplyMovement LOCALID_COUNTERPART, Route207_Movement_CounterpartWalkToPlayer
    WaitMovement
    ApplyMovement LOCALID_PLAYER, Route207_Movement_PlayerFaceCounterpart
    WaitMovement
    GoTo Route207_Counterpart
    End

Route207_ShowCounterpart:
    ClearFlag FLAG_HIDE_ROUTE_207_COUNTERPART
    AddObject LOCALID_COUNTERPART
    LockObject LOCALID_COUNTERPART
    Return

Route207_Counterpart:
    GetPlayerGender VAR_RESULT
    GoToIfEq VAR_RESULT, GENDER_MALE, Route207_Dawn
    GoTo Route207_Lucas

Route207_Dawn:
    BufferPlayerName 0
    Message Route207_Text_DawnChooseWhichHand
    InitGlobalTextListMenu 30, 13, 0, VAR_RESULT, NO_EXIT_ON_B
    SetMenuXOriginToRight
    AddListMenuEntry MenuEntries_Text_CounterpartHand_Right, 0
    AddListMenuEntry MenuEntries_Text_CounterpartHand_Left, 1
    ShowListMenu
    Message Route207_Text_DawnYouWantTheVsSeeker
    Call Route207_GiveVsSeeker
    Message Route207_Text_DawnHaveThisTooThen
    Call Route207_GivePoketchAppDowsingMachine
    Message Route207_Text_DawnUseDowsingMachineOften
    GoTo Route207_CounterpartLeave

Route207_Lucas:
    BufferPlayerName 0
    Message Route207_Text_LucasChooseAHand
    InitGlobalTextListMenu 30, 13, 0, VAR_RESULT, NO_EXIT_ON_B
    SetMenuXOriginToRight
    AddListMenuEntry MenuEntries_Text_CounterpartHand_Right, 0
    AddListMenuEntry MenuEntries_Text_CounterpartHand_Left, 1
    ShowListMenu
    Message Route207_Text_LucasYouWantTheVsSeeker
    Call Route207_GiveVsSeeker
    Message Route207_Text_LucasHaveThisTooThen
    Call Route207_GivePoketchAppDowsingMachine
    Message Route207_Text_LucasTryTouchingDowsingMachine
    GoTo Route207_CounterpartLeave

Route207_GiveVsSeeker:
    SetFlag FLAG_UNLOCKED_VS_SEEKER_LVL_1
    SetVar VAR_0x8004, ITEM_VS_SEEKER
    SetVar VAR_0x8005, 1
    Common_GiveItemQuantity
    Return

Route207_GivePoketchAppDowsingMachine:
    SetVar VAR_0x8004, POKETCH_APPID_DOWSINGMACHINE
    Common_GivePoketchApp
    BufferPoketchAppName 1, POKETCH_APPID_DOWSINGMACHINE
    Return

Route207_CounterpartLeave:
    CloseMessage
    ApplyMovement LOCALID_COUNTERPART, Route207_Movement_CounterpartLeave
    WaitMovement
    RemoveObject LOCALID_COUNTERPART
    Common_FadeToDefaultMusic
    SetVar VAR_ROUTE_207_COUNTERPART_TRIGGER_STATE, 1
    ReleaseAll
    End

    .balign 4, 0
Route207_Movement_PlayerFaceCounterpart:
    WalkOnSpotNormalWest
    EndMovement

Route207_Movement_Unused:
    Delay8 8
    WalkOnSpotNormalWest
    EndMovement

Route207_Movement_Unused2:
    Delay8 1
    WalkOnSpotNormalNorth
    EndMovement

    .balign 4, 0
Route207_Movement_CounterpartNoticePlayer:
    WalkNormalEast 3
    EmoteExclamationMark
    EndMovement

    .balign 4, 0
Route207_Movement_CounterpartWalkToPlayer:
    WalkNormalEast 5
    EndMovement

    .balign 4, 0
Route207_Movement_CounterpartLeave:
    WalkNormalWest 8
    EndMovement

Route207_Dummy3:
    NPCMessage Route207_Text_Dummy8
    End

Route207_CyclistM:
    PlaySE SE_CONFIRM_sseq_3
    LockAll
    FacePlayer
    GoToIfSet FLAG_RECEIVED_BICYCLE, Route207_ChangeGearTakeARun
    Message Route207_Text_ThatSlopesTooSlippery
    WaitButton
    CloseMessage
    ReleaseAll
    End

Route207_ChangeGearTakeARun:
    Message Route207_Text_ChangeGearTakeARun
    WaitButton
    CloseMessage
    ReleaseAll
    End

Route207_ArrowSignpostMtCoronet:
    ShowArrowSign Route207_Text_SignMtCoronet
    End

Route207_ArrowSignpostOreburghCity:
    ShowArrowSign Route207_Text_SignOreburghCity
    End

Route207_TrainerTipsSignpost:
    ShowScrollingSign Route207_Text_TrainerTipsImmobilizedIfAsleepOrParalyzed
    End

Route207_HoneyTree:
    PlaySE SE_CONFIRM_sseq_3
    LockAll
    CheckItem ITEM_HONEY, 1, VAR_RESULT
    GoToIfEq VAR_RESULT, FALSE, Route207_HoneyTreeNoHoney
    Message Route207_Text_HoneyTreeSlatherBark
    ShowYesNoMenu VAR_RESULT
    GoToIfEq VAR_RESULT, MENU_NO, Route207_HoneyTreeDeclined
    RemoveItem ITEM_HONEY, 1, VAR_RESULT
    Message Route207_Text_HoneyTreeBarkSlathered
    WaitButton
    CloseMessage
    WaitTime 30, VAR_RESULT
    Call Route207_HoneyTreePickSpecies
    PlayCry VAR_0x8004
    WaitCry
    StartLegendaryBattle VAR_0x8004, 12
    ClearFlag FLAG_MAP_LOCAL_REMOVE_OBJECT
    CheckWonBattle VAR_RESULT
    GoToIfEq VAR_RESULT, FALSE, Route207_HoneyTreeBlackOut
    ReleaseAll
    End

Route207_HoneyTreeNoHoney:
    Message Route207_Text_HoneyTreeSweetScent
    WaitButton
    CloseMessage
    ReleaseAll
    End

Route207_HoneyTreeDeclined:
    CloseMessage
    ReleaseAll
    End

Route207_HoneyTreePickSpecies:
    GetRandom VAR_RESULT, 13
    SetVar VAR_0x8004, SPECIES_COMBEE
    GoToIfEq VAR_RESULT, 0, Route207_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_COMBEE
    GoToIfEq VAR_RESULT, 1, Route207_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_COMBEE
    GoToIfEq VAR_RESULT, 2, Route207_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_WURMPLE
    GoToIfEq VAR_RESULT, 3, Route207_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_WURMPLE
    GoToIfEq VAR_RESULT, 4, Route207_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_BURMY
    GoToIfEq VAR_RESULT, 5, Route207_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_BURMY
    GoToIfEq VAR_RESULT, 6, Route207_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_CHERUBI
    GoToIfEq VAR_RESULT, 7, Route207_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_CHERUBI
    GoToIfEq VAR_RESULT, 8, Route207_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_AIPOM
    GoToIfEq VAR_RESULT, 9, Route207_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_AIPOM
    GoToIfEq VAR_RESULT, 10, Route207_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_HERACROSS
    GoToIfEq VAR_RESULT, 11, Route207_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_MUNCHLAX
    Return

Route207_HoneyTreeBlackOut:
    BlackOutFromBattle
    ReleaseAll
    End

Route207_HoneyTreePickSpeciesEnd:
    Return

    .balign 4, 0
