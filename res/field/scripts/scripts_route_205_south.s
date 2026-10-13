#include "macros/scrcmd.inc"
#include "res/text/bank/route_205_south.h"
#include "res/field/events/events_route_205_south.h"


    ScriptEntry Route205South_OnTransition
    ScriptEntry Route205South_BugCatcher
    ScriptEntry Route205South_Youngster
    ScriptEntry Route205South_Grunts
    ScriptEntry Route205South_LittleGirl
    ScriptEntry Route205South_CoordEvent_LittleGirl
    ScriptEntry Route205South_CoordEvent_Grunts
    ScriptEntry Route205South_ArrowSignpostFloaromaTown
    ScriptEntry Route205South_ArrowSignpostEternaForest
    ScriptEntry Route205South_TrainerTipsSignpost
    ScriptEntry Route205South_HoneyTree
    ScriptEntryEnd

Route205South_OnTransition:
    End

Route205South_Grunts:
    PlaySE SE_CONFIRM_sseq_3
    LockAll
    FacePlayer
    ApplyMovement LOCALID_GRUNT_M_WEST, Route205South_Movement_GruntMWestWalkOnSpotSouth
    WaitMovement
    Message Route205South_Text_TeamGalacticConductingResearch
    CloseMessage
    ApplyMovement LOCALID_GRUNT_M_EAST, Route205South_Movement_GruntMEastWalkOnSpotSouth
    WaitMovement
    Call _00B6
    Message Route205South_Text_ResearchInvolvesCatchingPokemon2
    WaitButton
    CloseMessage
    ReleaseAll
    End

    .balign 4, 0
Route205South_Movement_GruntMWestWalkOnSpotSouth:
    WalkOnSpotNormalSouth
    EndMovement

    .balign 4, 0
Route205South_Movement_GruntMEastWalkOnSpotSouth:
    WalkOnSpotNormalSouth
    EndMovement

Route205South_CoordEvent_Grunts:
    LockAll
    ApplyMovement LOCALID_GRUNT_M_WEST, Route205South_Movement_GruntMWestWalkOnSpotEast
    WaitMovement
    Message Route205South_Text_TeamGalacticConductingResearch
    CloseMessage
    ApplyMovement LOCALID_GRUNT_M_EAST, Route205South_Movement_GruntMEastWalkOnSpotWest
    WaitMovement
    Message Route205South_Text_ResearchInvolvesCatchingPokemon1
    CloseMessage
    ApplyMovement LOCALID_GRUNT_M_WEST, Route205South_Movement_GruntMWestPushBackPlayer
    ApplyMovement LOCALID_PLAYER, Route205South_Movement_PlayerGetPushedBack
    WaitMovement
    ApplyMovement LOCALID_GRUNT_M_EAST, Route205South_Movement_GruntMEastTurnBackSouth
    WaitMovement
    Call _00B6
    ReleaseAll
    End

_00B6:
    SetFlag FLAG_DUMMY_0x007F
    Return

    .balign 4, 0
Route205South_Movement_GruntMWestWalkOnSpotEast:
    WalkOnSpotNormalEast
    EndMovement

    .balign 4, 0
Route205South_Movement_GruntMEastWalkOnSpotWest:
    WalkOnSpotNormalWest
    EndMovement

    .balign 4, 0
Route205South_Movement_GruntMWestPushBackPlayer:
    WalkFastEast
    WalkOnSpotFastSouth
    Delay8 2
    WalkNormalWest
    WalkOnSpotNormalSouth
    EndMovement

    .balign 4, 0
Route205South_Movement_GruntMEastTurnBackSouth:
    WalkOnSpotNormalSouth
    EndMovement

    .balign 4, 0
Route205South_Movement_PlayerGetPushedBack:
    WalkNormalSouth
    WalkOnSpotFastNorth
    EndMovement

Route205South_BugCatcher:
    NPCMessage Route205South_Text_ManyPoisonTypePokemon
    End

Route205South_Youngster:
    NPCMessage Route205South_Text_SlatherHoneyOnATree
    End

Route205South_LittleGirl:
    PlaySE SE_CONFIRM_sseq_3
    LockAll
    FacePlayer
    GoToIfSet FLAG_TALKED_TO_ROUTE_205_SOUTH_LITTLE_GIRL, Route205South_IWantToSeeMyPapa
    Call Route205South_HideFloaromaTownGrunts
    Message Route205South_Text_HelpIWantToSeeMyPapa
    WaitButton
    CloseMessage
    ReleaseAll
    End

Route205South_IWantToSeeMyPapa:
    Message Route205South_Text_IWantToSeeMyPapa
    WaitButton
    CloseMessage
    ReleaseAll
    End

Route205South_HideFloaromaTownGrunts:
    SetFlag FLAG_HIDE_FLOAROMA_TOWN_GRUNTS
    SetFlag FLAG_TALKED_TO_ROUTE_205_SOUTH_LITTLE_GIRL
    SetVar VAR_VALLEY_WINDWORKS_STATE, 1
    Return

Route205South_CoordEvent_LittleGirl:
    LockAll
    GetPlayerMapPos VAR_0x8004, VAR_0x8005
    GoToIfEq VAR_0x8005, 659, Route205South_LittleGirlNoticePlayerZ659
    GoToIfEq VAR_0x8005, 660, Route205South_LittleGirlNoticePlayerZ660
    GoToIfEq VAR_0x8005, 661, Route205South_DummyZ661 @ unreachable position
    GoToIfEq VAR_0x8005, 662, Route205South_LittleGirlNoticePlayerZ662
    GoToIfEq VAR_0x8005, 663, Route205South_LittleGirlNoticePlayerZ663
    End

Route205South_LittleGirlNoticePlayerZ659:
    ApplyMovement LOCALID_LITTLE_GIRL, Route205South_Movement_TwinNoticePlayerZ659
    WaitMovement
    ApplyMovement LOCALID_PLAYER, Route205South_Movement_PlayerWalkOnSpotSouth
    WaitMovement
    GoTo Route205South_HelpIWantToSeeMyPapa

Route205South_LittleGirlNoticePlayerZ660:
    ApplyMovement LOCALID_LITTLE_GIRL, Route205South_Movement_TwinNoticePlayerZ660
    WaitMovement
    ApplyMovement LOCALID_PLAYER, Route205South_Movement_PlayerWalkOnSpotSouth
    WaitMovement
    GoTo Route205South_HelpIWantToSeeMyPapa

Route205South_DummyZ661:
    GoTo Route205South_HelpIWantToSeeMyPapa

Route205South_LittleGirlNoticePlayerZ662:
    ApplyMovement LOCALID_LITTLE_GIRL, Route205South_Movement_TwinNoticePlayerZ662
    WaitMovement
    ApplyMovement LOCALID_PLAYER, Route205South_Movement_PlayerWalkOnSpotNorth
    WaitMovement
    GoTo Route205South_HelpIWantToSeeMyPapa

Route205South_LittleGirlNoticePlayerZ663:
    ApplyMovement LOCALID_LITTLE_GIRL, Route205South_Movement_TwinNoticePlayerZ663
    WaitMovement
    ApplyMovement LOCALID_PLAYER, Route205South_Movement_PlayerWalkOnSpotNorth
    WaitMovement
    GoTo Route205South_HelpIWantToSeeMyPapa

Route205South_HelpIWantToSeeMyPapa:
    Call Route205South_HideFloaromaTownGrunts
    Message Route205South_Text_HelpIWantToSeeMyPapa
    WaitButton
    CloseMessage
    ReleaseAll
    End

    .balign 4, 0
Route205South_Movement_PlayerWalkOnSpotSouth:
    WalkOnSpotNormalSouth
    EndMovement

    .balign 4, 0
Route205South_Movement_PlayerWalkOnSpotNorth:
    WalkOnSpotNormalNorth
    EndMovement

    .balign 4, 0
Route205South_Movement_TwinNoticePlayerZ659:
    WalkOnSpotNormalNorth
    EmoteExclamationMark
    Delay8
    WalkNormalNorth
    EndMovement

    .balign 4, 0
Route205South_Movement_TwinNoticePlayerZ660:
    WalkOnSpotNormalNorth
    EmoteExclamationMark
    Delay8
    EndMovement

    .balign 4, 0
Route205South_Movement_TwinNoticePlayerZ662:
    WalkOnSpotNormalSouth
    EmoteExclamationMark
    Delay8
    EndMovement

    .balign 4, 0
Route205South_Movement_TwinNoticePlayerZ663:
    WalkOnSpotNormalSouth
    EmoteExclamationMark
    Delay8
    WalkNormalSouth
    EndMovement

Route205South_ArrowSignpostFloaromaTown:
    ShowArrowSign Route205South_Text_SignFloaromaTown
    End

Route205South_ArrowSignpostEternaForest:
    ShowArrowSign Route205South_Text_SignEternaForest
    End

Route205South_TrainerTipsSignpost:
    ShowScrollingSign Route205South_Text_TrainerTipsItemsAutomaticallySorted
    End

Route205South_HoneyTree:
    PlaySE SE_CONFIRM_sseq_3
    LockAll
    CheckItem ITEM_HONEY, 1, VAR_RESULT
    GoToIfEq VAR_RESULT, FALSE, Route205South_HoneyTreeNoHoney
    Message Route205South_Text_HoneyTreeSlatherBark
    ShowYesNoMenu VAR_RESULT
    GoToIfEq VAR_RESULT, MENU_NO, Route205South_HoneyTreeDeclined
    RemoveItem ITEM_HONEY, 1, VAR_RESULT
    Message Route205South_Text_HoneyTreeBarkSlathered
    WaitButton
    CloseMessage
    WaitTime 30, VAR_RESULT
    Call Route205South_HoneyTreePickSpecies
    PlayCry VAR_0x8004
    WaitCry
    StartLegendaryBattle VAR_0x8004, 12
    ClearFlag FLAG_MAP_LOCAL_REMOVE_OBJECT
    CheckWonBattle VAR_RESULT
    GoToIfEq VAR_RESULT, FALSE, Route205South_HoneyTreeBlackOut
    ReleaseAll
    End

Route205South_HoneyTreeNoHoney:
    Message Route205South_Text_HoneyTreeSweetScent
    WaitButton
    CloseMessage
    ReleaseAll
    End

Route205South_HoneyTreeDeclined:
    CloseMessage
    ReleaseAll
    End

Route205South_HoneyTreePickSpecies:
    GetRandom VAR_RESULT, 13
    SetVar VAR_0x8004, SPECIES_COMBEE
    GoToIfEq VAR_RESULT, 0, Route205South_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_COMBEE
    GoToIfEq VAR_RESULT, 1, Route205South_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_COMBEE
    GoToIfEq VAR_RESULT, 2, Route205South_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_WURMPLE
    GoToIfEq VAR_RESULT, 3, Route205South_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_WURMPLE
    GoToIfEq VAR_RESULT, 4, Route205South_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_BURMY
    GoToIfEq VAR_RESULT, 5, Route205South_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_BURMY
    GoToIfEq VAR_RESULT, 6, Route205South_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_CHERUBI
    GoToIfEq VAR_RESULT, 7, Route205South_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_CHERUBI
    GoToIfEq VAR_RESULT, 8, Route205South_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_AIPOM
    GoToIfEq VAR_RESULT, 9, Route205South_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_AIPOM
    GoToIfEq VAR_RESULT, 10, Route205South_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_HERACROSS
    GoToIfEq VAR_RESULT, 11, Route205South_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_MUNCHLAX
    Return

Route205South_HoneyTreeBlackOut:
    BlackOutFromBattle
    ReleaseAll
    End

Route205South_HoneyTreePickSpeciesEnd:
    Return

    .balign 4, 0
