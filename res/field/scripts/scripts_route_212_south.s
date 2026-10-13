#include "macros/scrcmd.inc"
#include "res/text/bank/route_212_south.h"


    ScriptEntry Route212South_SchoolKidM
    ScriptEntry Route212South_Lady
    ScriptEntry Route212South_Collector
    ScriptEntry Route212South_ArrowSignpostPastoriaCity
    ScriptEntry Route212South_SignboardShardsWanted
    ScriptEntry Route212South_PolicemanDanny
    ScriptEntry Route212South_OnTransition
    ScriptEntry Route212South_TrainerTipsSignpost
    ScriptEntry Route212South_HoneyTree
    ScriptEntryEnd

Route212South_OnTransition:
    GetTimeOfDay VAR_MAP_LOCAL_0x00
    GoToIfInRange VAR_MAP_LOCAL_0x00, TIMEOFDAY_MORNING, TIMEOFDAY_TWILIGHT, Route212South_SetPolicemanNoBattle
    GoToIfInRange VAR_MAP_LOCAL_0x00, TIMEOFDAY_NIGHT, TIMEOFDAY_LATE_NIGHT, Route212South_SetPolicemanBattle
    End

Route212South_SetPolicemanNoBattle:
    ClearFlag FLAG_HIDE_ROUTE_212_SOUTH_POLICEMAN_DANNY_NO_BATTLE
    SetFlag FLAG_HIDE_ROUTE_212_SOUTH_POLICEMAN_DANNY
    End

Route212South_SetPolicemanBattle:
    ClearFlag FLAG_HIDE_ROUTE_212_SOUTH_POLICEMAN_DANNY
    SetFlag FLAG_HIDE_ROUTE_212_SOUTH_POLICEMAN_DANNY_NO_BATTLE
    End

Route212South_SchoolKidM:
    NPCMessage Route212South_Text_CrossLogsOnBike
    End

Route212South_Lady:
    NPCMessage Route212South_Text_ImNotStuck
    End

Route212South_Collector:
    NPCMessage Route212South_Text_HowAboutPokemonMansion
    End

Route212South_ArrowSignpostPastoriaCity:
    ShowArrowSign Route212South_Text_SignPastoriaCity
    End

Route212South_SignboardShardsWanted:
    ShowLandmarkSign Route212South_Text_SignShardsWanted
    End

Route212South_TrainerTipsSignpost:
    ShowScrollingSign Route212South_Text_TrainerTipsBog
    End

Route212South_PolicemanDanny:
    NPCMessage Route212South_Text_ConstantPatrol
    End

Route212South_HoneyTree:
    PlaySE SE_CONFIRM_sseq_3
    LockAll
    CheckItem ITEM_HONEY, 1, VAR_RESULT
    GoToIfEq VAR_RESULT, FALSE, Route212South_HoneyTreeNoHoney
    Message Route212South_Text_HoneyTreeSlatherBark
    ShowYesNoMenu VAR_RESULT
    GoToIfEq VAR_RESULT, MENU_NO, Route212South_HoneyTreeDeclined
    RemoveItem ITEM_HONEY, 1, VAR_RESULT
    Message Route212South_Text_HoneyTreeBarkSlathered
    WaitButton
    CloseMessage
    WaitTime 30, VAR_RESULT
    Call Route212South_HoneyTreePickSpecies
    PlayCry VAR_0x8004
    WaitCry
    StartLegendaryBattle VAR_0x8004, 12
    ClearFlag FLAG_MAP_LOCAL_REMOVE_OBJECT
    CheckWonBattle VAR_RESULT
    GoToIfEq VAR_RESULT, FALSE, Route212South_HoneyTreeBlackOut
    ReleaseAll
    End

Route212South_HoneyTreeNoHoney:
    Message Route212South_Text_HoneyTreeSweetScent
    WaitButton
    CloseMessage
    ReleaseAll
    End

Route212South_HoneyTreeDeclined:
    CloseMessage
    ReleaseAll
    End

Route212South_HoneyTreePickSpecies:
    GetRandom VAR_RESULT, 13
    SetVar VAR_0x8004, SPECIES_COMBEE
    GoToIfEq VAR_RESULT, 0, Route212South_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_COMBEE
    GoToIfEq VAR_RESULT, 1, Route212South_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_COMBEE
    GoToIfEq VAR_RESULT, 2, Route212South_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_WURMPLE
    GoToIfEq VAR_RESULT, 3, Route212South_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_WURMPLE
    GoToIfEq VAR_RESULT, 4, Route212South_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_BURMY
    GoToIfEq VAR_RESULT, 5, Route212South_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_BURMY
    GoToIfEq VAR_RESULT, 6, Route212South_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_CHERUBI
    GoToIfEq VAR_RESULT, 7, Route212South_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_CHERUBI
    GoToIfEq VAR_RESULT, 8, Route212South_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_AIPOM
    GoToIfEq VAR_RESULT, 9, Route212South_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_AIPOM
    GoToIfEq VAR_RESULT, 10, Route212South_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_HERACROSS
    GoToIfEq VAR_RESULT, 11, Route212South_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_MUNCHLAX
    Return

Route212South_HoneyTreeBlackOut:
    BlackOutFromBattle
    ReleaseAll
    End

Route212South_HoneyTreePickSpeciesEnd:
    Return
