#include "macros/scrcmd.inc"
#include "res/text/bank/route_222.h"


    ScriptEntry Route222_Fisherman
    ScriptEntry Route222_RichBoy
    ScriptEntry Route222_ArrowSignpostHotelGrandLake
    ScriptEntry Route222_ArrowSignpostSunyshoreCity
    ScriptEntry Route222_SignboardPikachuFanClub
    ScriptEntry Route222_SignboardPokemonSizeContest
    ScriptEntry Route222_PolicemanThomas
    ScriptEntry Route222_OnTransition
    ScriptEntry Route222_HoneyTree
    ScriptEntryEnd

Route222_OnTransition:
    GetTimeOfDay VAR_MAP_LOCAL_0x00
    GoToIfInRange VAR_MAP_LOCAL_0x00, TIMEOFDAY_MORNING, TIMEOFDAY_TWILIGHT, Route222_SetPolicemanThomasNoBattle
    GoToIfInRange VAR_MAP_LOCAL_0x00, TIMEOFDAY_NIGHT, TIMEOFDAY_LATE_NIGHT, Route222_SetPolicemanThomasBattle
    End

Route222_SetPolicemanThomasNoBattle:
    ClearFlag FLAG_HIDE_ROUTE_222_POLICEMAN_THOMAS_NO_BATTLE
    SetFlag FLAG_HIDE_ROUTE_222_POLICEMAN_THOMAS
    End

Route222_SetPolicemanThomasBattle:
    ClearFlag FLAG_HIDE_ROUTE_222_POLICEMAN_THOMAS
    SetFlag FLAG_HIDE_ROUTE_222_POLICEMAN_THOMAS_NO_BATTLE
    End

Route222_RichBoy:
    PlaySE SE_CONFIRM_sseq_3
    LockAll
    FacePlayer
    GoToIfSet FLAG_RECEIVED_ROUTE_222_TM56, Route222_ExplainFling
    Message Route222_Text_IGiveTMFling
    SetVar VAR_0x8004, ITEM_TM56
    SetVar VAR_0x8005, 1
    GoToIfCannotFitItem VAR_0x8004, VAR_0x8005, VAR_RESULT, Route222_BagIsFull
    Common_GiveItemQuantity
    SetFlag FLAG_RECEIVED_ROUTE_222_TM56
    GoTo Route222_ExplainFling

Route222_ExplainFling:
    Message Route222_Text_ExplainFling
    WaitButton
    CloseMessage
    ReleaseAll
    End

Route222_BagIsFull:
    Common_MessageBagIsFull
    CloseMessage
    ReleaseAll
    End

Route222_Fisherman:
    NPCMessage Route222_Text_CatchingMadeMeHappy
    End

Route222_ArrowSignpostHotelGrandLake:
    ShowArrowSign Route222_Text_SignHotelGrandLake
    End

Route222_ArrowSignpostSunyshoreCity:
    ShowArrowSign Route222_Text_SignSunyshoreCity
    End

Route222_SignboardPikachuFanClub:
    ShowLandmarkSign Route222_Text_SignPikachuFanClub
    End

Route222_SignboardPokemonSizeContest:
    ShowLandmarkSign Route222_Text_SignPokemonSizeContest
    End

Route222_PolicemanThomas:
    NPCMessage Route222_Text_MoreAgitatedAtNight
    End

Route222_HoneyTree:
    PlaySE SE_CONFIRM_sseq_3
    LockAll
    CheckItem ITEM_HONEY, 1, VAR_RESULT
    GoToIfEq VAR_RESULT, FALSE, Route222_HoneyTreeNoHoney
    Message Route222_Text_HoneyTreeSlatherBark
    ShowYesNoMenu VAR_RESULT
    GoToIfEq VAR_RESULT, MENU_NO, Route222_HoneyTreeDeclined
    RemoveItem ITEM_HONEY, 1, VAR_RESULT
    Message Route222_Text_HoneyTreeBarkSlathered
    WaitButton
    CloseMessage
    WaitTime 30, VAR_RESULT
    Call Route222_HoneyTreePickSpecies
    PlayCry VAR_0x8004
    WaitCry
    StartLegendaryBattle VAR_0x8004, 12
    ClearFlag FLAG_MAP_LOCAL_REMOVE_OBJECT
    CheckWonBattle VAR_RESULT
    GoToIfEq VAR_RESULT, FALSE, Route222_HoneyTreeBlackOut
    ReleaseAll
    End

Route222_HoneyTreeNoHoney:
    Message Route222_Text_HoneyTreeSweetScent
    WaitButton
    CloseMessage
    ReleaseAll
    End

Route222_HoneyTreeDeclined:
    CloseMessage
    ReleaseAll
    End

Route222_HoneyTreePickSpecies:
    GetRandom VAR_RESULT, 13
    SetVar VAR_0x8004, SPECIES_COMBEE
    GoToIfEq VAR_RESULT, 0, Route222_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_COMBEE
    GoToIfEq VAR_RESULT, 1, Route222_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_COMBEE
    GoToIfEq VAR_RESULT, 2, Route222_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_WURMPLE
    GoToIfEq VAR_RESULT, 3, Route222_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_WURMPLE
    GoToIfEq VAR_RESULT, 4, Route222_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_BURMY
    GoToIfEq VAR_RESULT, 5, Route222_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_BURMY
    GoToIfEq VAR_RESULT, 6, Route222_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_CHERUBI
    GoToIfEq VAR_RESULT, 7, Route222_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_CHERUBI
    GoToIfEq VAR_RESULT, 8, Route222_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_AIPOM
    GoToIfEq VAR_RESULT, 9, Route222_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_AIPOM
    GoToIfEq VAR_RESULT, 10, Route222_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_HERACROSS
    GoToIfEq VAR_RESULT, 11, Route222_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_MUNCHLAX
    Return

Route222_HoneyTreeBlackOut:
    BlackOutFromBattle
    ReleaseAll
    End

Route222_HoneyTreePickSpeciesEnd:
    Return

    .balign 4, 0
