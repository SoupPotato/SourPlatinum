#include "macros/scrcmd.inc"
#include "res/text/bank/route_212_north.h"


    ScriptEntry Route212North_Youngster
    ScriptEntry Route212North_ArrowSignpostHearthomeCity
    ScriptEntry Route212North_SignboardPokemonMansion
    ScriptEntry Route212North_TrainerTipsSignpost
    ScriptEntry Route212North_Collector
    ScriptEntry Route212North_PolicemanBobby
    ScriptEntry Route212North_PolicemanAlex
    ScriptEntry Route212North_PolicemanDylan
    ScriptEntry Route212North_PolicemanCaleb
    ScriptEntry Route212North_OnTransition
    ScriptEntry Route212North_HoneyTree
    ScriptEntryEnd

Route212North_OnTransition:
    GetTimeOfDay VAR_MAP_LOCAL_0x00
    GoToIfInRange VAR_MAP_LOCAL_0x00, TIMEOFDAY_MORNING, TIMEOFDAY_TWILIGHT, Route212North_SetPolicemenNoBattle
    GoToIfInRange VAR_MAP_LOCAL_0x00, TIMEOFDAY_NIGHT, TIMEOFDAY_LATE_NIGHT, Route212North_SetPolicemenBattle
    End

Route212North_SetPolicemenNoBattle:
    ClearFlag FLAG_HIDE_ROUTE_212_NORTH_POLICEMAN_BOBBY_NO_BATTLE
    ClearFlag FLAG_HIDE_ROUTE_212_NORTH_POLICEMAN_ALEX_NO_BATTLE
    ClearFlag FLAG_HIDE_ROUTE_212_NORTH_POLICEMAN_DYLAN_NO_BATTLE
    ClearFlag FLAG_HIDE_ROUTE_212_NORTH_POLICEMAN_CALEB_NO_BATTLE
    SetFlag FLAG_HIDE_ROUTE_212_NORTH_POLICEMAN_BOBBY
    SetFlag FLAG_HIDE_ROUTE_212_NORTH_POLICEMAN_ALEX
    SetFlag FLAG_HIDE_ROUTE_212_NORTH_POLICEMAN_DYLAN
    SetFlag FLAG_HIDE_ROUTE_212_NORTH_POLICEMAN_CALEB
    End

Route212North_SetPolicemenBattle:
    ClearFlag FLAG_HIDE_ROUTE_212_NORTH_POLICEMAN_BOBBY
    ClearFlag FLAG_HIDE_ROUTE_212_NORTH_POLICEMAN_ALEX
    ClearFlag FLAG_HIDE_ROUTE_212_NORTH_POLICEMAN_DYLAN
    ClearFlag FLAG_HIDE_ROUTE_212_NORTH_POLICEMAN_CALEB
    SetFlag FLAG_HIDE_ROUTE_212_NORTH_POLICEMAN_BOBBY_NO_BATTLE
    SetFlag FLAG_HIDE_ROUTE_212_NORTH_POLICEMAN_ALEX_NO_BATTLE
    SetFlag FLAG_HIDE_ROUTE_212_NORTH_POLICEMAN_DYLAN_NO_BATTLE
    SetFlag FLAG_HIDE_ROUTE_212_NORTH_POLICEMAN_CALEB_NO_BATTLE
    End

Route212North_Youngster:
    NPCMessage Route212North_Text_MrBacklotLikesVisitors
    End

Route212North_ArrowSignpostHearthomeCity:
    ShowArrowSign Route212North_Text_SignHearthomeCity
    End

Route212North_SignboardPokemonMansion:
    ShowLandmarkSign Route212North_Text_SignPokemonMansion
    End

Route212North_TrainerTipsSignpost:
    ShowScrollingSign Route212North_Text_TrainerTipsReorganizeItems
    End

Route212North_Collector:
    NPCMessage Route212North_Text_FindAttractiveTree
    End

Route212North_PolicemanBobby:
    NPCMessage Route212North_Text_SayHiToPolicemen
    End

Route212North_PolicemanAlex:
    NPCMessage Route212North_Text_PatrolsDayAndNight
    End

Route212North_PolicemanDylan:
    NPCMessage Route212North_Text_WorkingHard
    End

Route212North_PolicemanCaleb:
    NPCMessage Route212North_Text_PatrolTooMuch
    End

Route212North_HoneyTree:
    PlaySE SE_CONFIRM_sseq_3
    LockAll
    CheckItem ITEM_HONEY, 1, VAR_RESULT
    GoToIfEq VAR_RESULT, FALSE, Route212North_HoneyTreeNoHoney
    Message Route212North_Text_HoneyTreeSlatherBark
    ShowYesNoMenu VAR_RESULT
    GoToIfEq VAR_RESULT, MENU_NO, Route212North_HoneyTreeDeclined
    RemoveItem ITEM_HONEY, 1, VAR_RESULT
    Message Route212North_Text_HoneyTreeBarkSlathered
    WaitButton
    CloseMessage
    WaitTime 30, VAR_RESULT
    Call Route212North_HoneyTreePickSpecies
    PlayCry VAR_0x8004
    WaitCry
    StartLegendaryBattle VAR_0x8004, 12
    ClearFlag FLAG_MAP_LOCAL_REMOVE_OBJECT
    CheckWonBattle VAR_RESULT
    GoToIfEq VAR_RESULT, FALSE, Route212North_HoneyTreeBlackOut
    ReleaseAll
    End

Route212North_HoneyTreeNoHoney:
    Message Route212North_Text_HoneyTreeSweetScent
    WaitButton
    CloseMessage
    ReleaseAll
    End

Route212North_HoneyTreeDeclined:
    CloseMessage
    ReleaseAll
    End

Route212North_HoneyTreePickSpecies:
    GetRandom VAR_RESULT, 13
    SetVar VAR_0x8004, SPECIES_COMBEE
    GoToIfEq VAR_RESULT, 0, Route212North_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_COMBEE
    GoToIfEq VAR_RESULT, 1, Route212North_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_COMBEE
    GoToIfEq VAR_RESULT, 2, Route212North_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_WURMPLE
    GoToIfEq VAR_RESULT, 3, Route212North_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_WURMPLE
    GoToIfEq VAR_RESULT, 4, Route212North_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_BURMY
    GoToIfEq VAR_RESULT, 5, Route212North_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_BURMY
    GoToIfEq VAR_RESULT, 6, Route212North_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_CHERUBI
    GoToIfEq VAR_RESULT, 7, Route212North_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_CHERUBI
    GoToIfEq VAR_RESULT, 8, Route212North_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_AIPOM
    GoToIfEq VAR_RESULT, 9, Route212North_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_AIPOM
    GoToIfEq VAR_RESULT, 10, Route212North_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_HERACROSS
    GoToIfEq VAR_RESULT, 11, Route212North_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_MUNCHLAX
    Return

Route212North_HoneyTreeBlackOut:
    BlackOutFromBattle
    ReleaseAll
    End

Route212North_HoneyTreePickSpeciesEnd:
    Return

    .balign 4, 0
