#include "macros/scrcmd.inc"
#include "res/text/bank/route_209.h"


    ScriptEntry Route209_PokefanM
    ScriptEntry Route209_HallowedTower
    ScriptEntry Route209_ArrowSignpostHearthomeCity
    ScriptEntry Route209_ArrowSignpostSolaceonTown
    ScriptEntry Route209_Fisherman
    ScriptEntry Route209_JoggerRichard
    ScriptEntry Route209_JoggerRaul
    ScriptEntry Route209_OnTransition
    ScriptEntry Route209_TrainerTipsSignpost
    ScriptEntry Route209_HoneyTree
    ScriptEntryEnd

Route209_OnTransition:
    GetTimeOfDay VAR_MAP_LOCAL_0x00
    GoToIfEq VAR_MAP_LOCAL_0x00, TIMEOFDAY_MORNING, Route209_SetJoggersBattle
    GoToIfInRange VAR_MAP_LOCAL_0x00, TIMEOFDAY_DAY, TIMEOFDAY_LATE_NIGHT, Route209_SetJoggersNoBattle
    End

Route209_SetJoggersBattle:
    ClearFlag FLAG_HIDE_ROUTE_209_JOGGER_RICHARD
    ClearFlag FLAG_HIDE_ROUTE_209_JOGGER_RAUL
    SetFlag FLAG_HIDE_ROUTE_209_JOGGER_RICHARD_NO_BATTLE
    SetFlag FLAG_HIDE_ROUTE_209_JOGGER_RAUL_NO_BATTLE
    End

Route209_SetJoggersNoBattle:
    ClearFlag FLAG_HIDE_ROUTE_209_JOGGER_RICHARD_NO_BATTLE
    ClearFlag FLAG_HIDE_ROUTE_209_JOGGER_RAUL_NO_BATTLE
    SetFlag FLAG_HIDE_ROUTE_209_JOGGER_RICHARD
    SetFlag FLAG_HIDE_ROUTE_209_JOGGER_RAUL
    End

Route209_PokefanM:
    NPCMessage Route209_Text_ThisIsTheLostTower
    End

Route209_HallowedTower:
    PlaySE SE_CONFIRM_sseq_3
    LockAll
    GoToIfEq VAR_HALLOWED_TOWER_STATE, 1, Route209_CheckSpiritombCounter
    CheckItem ITEM_ODD_KEYSTONE, 1, VAR_RESULT
    GoToIfEq VAR_RESULT, FALSE, Route209_ThereIsABrokenTower
    Message Route209_Text_UseTheOddKeystone
    ShowYesNoMenu VAR_RESULT
    GoToIfEq VAR_RESULT, MENU_YES, Route209_UseOddKeystone
    CloseMessage
    ReleaseAll
    End

Route209_UseOddKeystone:
    BufferPlayerName 0
    Message Route209_Text_PlayerUsedTheOddKeystone
    WaitButton
    RemoveItem ITEM_ODD_KEYSTONE, 1, VAR_RESULT
    SetVar VAR_HALLOWED_TOWER_STATE, 1
    CloseMessage
    ReleaseAll
    End

Route209_CheckSpiritombCounter:
    GetSpiritombCounter VAR_RESULT
    GoToIfGe VAR_RESULT, 32, Route209_EncounterSpiritomb
    GoToIfGe VAR_RESULT, 29, Route209_SomeSortOfPresence
    GoToIfGe VAR_RESULT, 22, Route209_IsThatTowerShaking
    GoToIfGe VAR_RESULT, 15, Route209_CryingComingFromInside
    GoToIfGe VAR_RESULT, 8, Route209_StonesAppearToHaveShifted
    GoTo Route209_BuiltManyYearsAgo

Route209_EncounterSpiritomb:
    WaitSE SE_CONFIRM_sseq_3
    PlayCry SPECIES_SPIRITOMB
    Message Route209_Text_SpiritombCry
    WaitCry
    CloseMessage
    StartWildBattle SPECIES_SPIRITOMB, 25
    CheckWonBattle VAR_RESULT
    GoToIfEq VAR_RESULT, FALSE, Route209_BlackOut
    SetVar VAR_HALLOWED_TOWER_STATE, 0
    ClearSpiritombCounter
    End

Route209_BlackOut:
    BlackOutFromBattle
    ReleaseAll
    End

Route209_BuiltManyYearsAgo:
    Message Route209_Text_BuiltManyYearsAgo
    WaitButton
    CloseMessage
    ReleaseAll
    End

Route209_StonesAppearToHaveShifted:
    Message Route209_Text_StonesAppearToHaveShifted
    WaitButton
    CloseMessage
    ReleaseAll
    End

Route209_CryingComingFromInside:
    Message Route209_Text_CryingComingFromInside
    WaitButton
    CloseMessage
    ReleaseAll
    End

Route209_IsThatTowerShaking:
    Message Route209_Text_IsTheTowerShaking
    WaitButton
    CloseMessage
    ReleaseAll
    End

Route209_SomeSortOfPresence:
    Message Route209_Text_SomeSortOfPresence
    WaitButton
    CloseMessage
    ReleaseAll
    End

Route209_ThereIsABrokenTower:
    Message Route209_Text_ThereIsABrokenTower
    WaitButton
    CloseMessage
    ReleaseAll
    End

Route209_Fisherman:
    PlaySE SE_CONFIRM_sseq_3
    LockAll
    FacePlayer
    SetVar VAR_0x8004, ITEM_GOOD_ROD
    BufferItemNameWithArticle 0, VAR_0x8004
    CapitalizeFirstLetter 0
    GoToIfSet FLAG_RECEIVED_GOOD_ROD, Route209_AskExplainHowToFish
    Message Route209_Text_GoodRodIsReallyGood
    ShowYesNoMenu VAR_RESULT
    GoToIfEq VAR_RESULT, MENU_YES, Route209_AcceptGoodRod
    GoToIfEq VAR_RESULT, MENU_NO, Route209_RefuseGoodRod
    End

Route209_AskExplainHowToFish:
    BufferItemName 0, VAR_0x8004
    Message Route209_Text_DoINeedToExplain
    ShowYesNoMenu VAR_RESULT
    GoToIfEq VAR_RESULT, MENU_YES, Route209_ExplainHowToFish
    GoToIfEq VAR_RESULT, MENU_NO, Route209_WhenYouReelYouBattle
    End

Route209_ExplainHowToFish:
    Message Route209_Text_ExplainHowToFish
    WaitButton
    CloseMessage
    ReleaseAll
    End

Route209_WhenYouReelYouBattle:
    Message Route209_Text_WhenYouReelYouBattle
    WaitButton
    CloseMessage
    ReleaseAll
    End

Route209_RefuseGoodRod:
    Message Route209_Text_YouDontLikeToFish
    WaitButton
    CloseMessage
    ReleaseAll
    End

Route209_AcceptGoodRod:
    BufferItemName 0, VAR_0x8004
    Message Route209_Text_TakeThisGoodRod
    SetVar VAR_0x8005, 1
    Common_GiveItemQuantity
    SetFlag FLAG_RECEIVED_GOOD_ROD
    GoTo Route209_AskExplainHowToFish

Route209_ArrowSignpostHearthomeCity:
    ShowArrowSign Route209_Text_SignHearthomeCity
    End

Route209_ArrowSignpostSolaceonTown:
    ShowArrowSign Route209_Text_SignSolaceonTown
    End

Route209_TrainerTipsSignpost:
    ShowScrollingSign Route209_Text_TrainerTipsRegisterKeyItems
    End

Route209_JoggerRichard:
    NPCMessage Route209_Text_DoYouJogEveryMorning
    End

Route209_JoggerRaul:
    NPCMessage Route209_Text_PokemonChasedAfterMe
    End

Route209_HoneyTree:
    PlaySE SE_CONFIRM_sseq_3
    LockAll
    CheckItem ITEM_HONEY, 1, VAR_RESULT
    GoToIfEq VAR_RESULT, FALSE, Route209_HoneyTreeNoHoney
    Message Route209_Text_HoneyTreeSlatherBark
    ShowYesNoMenu VAR_RESULT
    GoToIfEq VAR_RESULT, MENU_NO, Route209_HoneyTreeDeclined
    RemoveItem ITEM_HONEY, 1, VAR_RESULT
    Message Route209_Text_HoneyTreeBarkSlathered
    WaitButton
    CloseMessage
    WaitTime 30, VAR_RESULT
    Call Route209_HoneyTreePickSpecies
    PlayCry VAR_0x8004
    WaitCry
    StartLegendaryBattle VAR_0x8004, 12
    ClearFlag FLAG_MAP_LOCAL_REMOVE_OBJECT
    CheckWonBattle VAR_RESULT
    GoToIfEq VAR_RESULT, FALSE, Route209_HoneyTreeBlackOut
    ReleaseAll
    End

Route209_HoneyTreeNoHoney:
    Message Route209_Text_HoneyTreeSweetScent
    WaitButton
    CloseMessage
    ReleaseAll
    End

Route209_HoneyTreeDeclined:
    CloseMessage
    ReleaseAll
    End

Route209_HoneyTreePickSpecies:
    GetRandom VAR_RESULT, 13
    SetVar VAR_0x8004, SPECIES_COMBEE
    GoToIfEq VAR_RESULT, 0, Route209_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_COMBEE
    GoToIfEq VAR_RESULT, 1, Route209_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_COMBEE
    GoToIfEq VAR_RESULT, 2, Route209_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_WURMPLE
    GoToIfEq VAR_RESULT, 3, Route209_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_WURMPLE
    GoToIfEq VAR_RESULT, 4, Route209_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_BURMY
    GoToIfEq VAR_RESULT, 5, Route209_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_BURMY
    GoToIfEq VAR_RESULT, 6, Route209_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_CHERUBI
    GoToIfEq VAR_RESULT, 7, Route209_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_CHERUBI
    GoToIfEq VAR_RESULT, 8, Route209_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_AIPOM
    GoToIfEq VAR_RESULT, 9, Route209_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_AIPOM
    GoToIfEq VAR_RESULT, 10, Route209_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_HERACROSS
    GoToIfEq VAR_RESULT, 11, Route209_HoneyTreePickSpeciesEnd
    SetVar VAR_0x8004, SPECIES_MUNCHLAX
    Return

Route209_HoneyTreeBlackOut:
    BlackOutFromBattle
    ReleaseAll
    End

Route209_HoneyTreePickSpeciesEnd:
    Return

    .balign 4, 0
