#include "macros/scrcmd.inc"
#include "res/text/bank/field_moves.h"
#include "constants/field/field_move_helper.h"


    ScriptEntry FieldMoves_CutTree
    ScriptEntry FieldMoves_Rock
    ScriptEntry FieldMoves_Boulder
    ScriptEntry FieldMoves_RockyWall
    ScriptEntry FieldMoves_Water
    ScriptEntry FieldMoves_Fog_Unused
    ScriptEntry FieldMoves_Waterfall
    ScriptEntry FieldMoves_Dummy8
    ScriptEntry FieldMoves_UseCutFromMenu
    ScriptEntry FieldMoves_UseRockSmashFromMenu
    ScriptEntry FieldMoves_UseStrengthFromMenu
    ScriptEntry FieldMoves_UseRockClimbFromMenu
    ScriptEntry FieldMoves_UseSurfFromMenu
    ScriptEntry FieldMoves_UseWaterfallFromMenu
    ScriptEntry FieldMoves_UseDefogFromMenu
    ScriptEntry FieldMoves_UseFlashFromMenu
    ScriptEntry FieldMoves_PoketchError
    ScriptEntry FieldMoves_UseFlyFromApp
    ScriptEntryEnd

FieldMoves_CutTree:
    PlaySE SE_CONFIRM_sseq_3
    LockAll
    FacePlayer
    FindPartySlotWithMove VAR_RESULT, MOVE_CUT
    GoToIfEq VAR_RESULT, MAX_PARTY_SIZE, FieldMoves_TryAppCut
    CheckBadgeAcquired BADGE_ID_FOREST, VAR_RESULT
    GoToIfEq VAR_RESULT, FALSE, FieldMoves_CantUseCut
    Message FieldMoves_Text_WouldYouLikeToUseCut
    ShowYesNoMenu VAR_RESULT
    GoToIfEq VAR_RESULT, MENU_YES, FieldMoves_UseCutFromField
    CloseMessage
    GoTo FieldMoves_End
    End

FieldMoves_TryAppCut:
    SetVar VAR_0x8004, ITEM_HM01
    SetVar VAR_0x8005, BADGE_ID_FOREST
    SetVar VAR_0x8006, MOVE_CUT
    Call FieldMoves_CheckAppUsable
    GoToIfEq VAR_RESULT, FALSE, FieldMoves_CantUseCut
    Message FieldMoves_Text_TreeLooksLikeCanBeCut
    WaitButton
    Call FieldMoves_AskUseApp
    GoToIfEq VAR_RESULT, 0, FieldMoves_CantUseCut
    GoToIfEq VAR_RESULT, 1, FieldMoves_UseCutWithApp
    GoTo FieldMoves_End
    End

FieldMoves_UseCutWithApp:
    SetVar VAR_0x8000, FIELD_MOVE_HELPER_SLOT_CUT
    GoTo FieldMoves_UseCutFromMenuLocked
    End

FieldMoves_CantUseCut:
    Message FieldMoves_Text_TreeLooksLikeCanBeCut
    GetCurrentMapID VAR_0x8004
    CallIfEq VAR_0x8004, MAP_HEADER_ETERNA_FOREST, FieldMoves_TryEnableCherylCutscene
    WaitButton
    CloseMessage
    GoTo FieldMoves_End
    End

FieldMoves_UseCutFromField:
    FindPartySlotWithMove VAR_RESULT, MOVE_CUT
    SetVar VAR_0x8004, VAR_RESULT
    BufferPartyMonNickname 0, VAR_RESULT
    Message FieldMoves_Text_PokemonUsedCut
    CloseMessage
    PlayHMCutIn VAR_0x8004
    StartDestroyObstacleAnimation 0, VAR_0x8005
    WaitTime 7, VAR_RESULT
    RemoveObject VAR_LAST_TALKED
    GetCurrentMapID VAR_0x8004
    CreateJournalEvent LOCATION_EVENT_USED_CUT, VAR_0x8004
FieldMoves_WaitForCutAnimFromField:
    WaitTime 1, VAR_RESULT
    GoToIfEq VAR_0x8005, 0, FieldMoves_WaitForCutAnimFromField
    GoTo FieldMoves_End
    End

FieldMoves_UseCutFromMenu:
    LockAll
FieldMoves_UseCutFromMenuLocked:
    BufferPartyMonNickname 0, VAR_0x8000
    SetVar VAR_0x8001, MOVE_CUT
    Call FieldMoves_MessageUsedCut
    CloseMessage
    PlayHMCutIn VAR_0x8000
    StartDestroyObstacleAnimation 0, VAR_0x8005
    WaitTime 7, VAR_RESULT
    RemoveObject VAR_LAST_TALKED
    GetCurrentMapID VAR_0x8004
    CreateJournalEvent LOCATION_EVENT_USED_CUT, VAR_0x8004
FieldMoves_WaitForCutAnimFromMenu:
    WaitTime 1, VAR_RESULT
    GoToIfEq VAR_0x8005, 0, FieldMoves_WaitForCutAnimFromMenu
    ReleaseAll
    End

FieldMoves_TryEnableCherylCutscene:
    GoToIfNe VAR_ETERNA_FOREST_CHERYL_OLD_CHATEAU_CUTSCENE_STATE, 0, FieldMoves_DontEnableCherylCutscene
    GoToIfNe VAR_ETERNA_FOREST_FOLLOWER_CHERYL_STATE, 1, FieldMoves_DontEnableCherylCutscene
    Call FieldMoves_CheckPositionForCherylCutscene
    GoToIfEq VAR_RESULT, FALSE, FieldMoves_DontEnableCherylCutscene
    SetVar VAR_ETERNA_FOREST_CHERYL_OLD_CHATEAU_CUTSCENE_STATE, 1
    Return

FieldMoves_CheckPositionForCherylCutscene:
    SetVar VAR_RESULT, FALSE
    GetPlayerMapPos VAR_0x8004, VAR_0x8005
    GoToIfEq VAR_0x8004, 73, FieldMoves_CheckPositionX73
    GoToIfEq VAR_0x8004, 74, FieldMoves_CheckPositionX74
    GoToIfEq VAR_0x8004, 75, FieldMoves_CheckPositionX75
    GoToIfEq VAR_0x8004, 76, FieldMoves_CheckPositionX76
    GoToIfEq VAR_0x8004, 77, FieldMoves_CheckPositionX77
    Return

FieldMoves_CheckPositionX73:
    GoToIfEq VAR_0x8005, 33, FieldMoves_CorrectPositionForCherylCutscene
    Return

FieldMoves_CheckPositionX74:
    GoToIfEq VAR_0x8005, 34, FieldMoves_CorrectPositionForCherylCutscene
    Return

FieldMoves_CheckPositionX75:
    GoToIfEq VAR_0x8005, 34, FieldMoves_CorrectPositionForCherylCutscene
    Return

FieldMoves_CheckPositionX76:
    GoToIfEq VAR_0x8005, 33, FieldMoves_CorrectPositionForCherylCutscene
    Return

FieldMoves_CheckPositionX77:
    GoToIfEq VAR_0x8005, 34, FieldMoves_CorrectPositionForCherylCutscene
    Return

FieldMoves_CorrectPositionForCherylCutscene:
    SetVar VAR_RESULT, TRUE
    Return

FieldMoves_DontEnableCherylCutscene:
    Return

FieldMoves_Rock:
    PlaySE SE_CONFIRM_sseq_3
    LockAll
    FacePlayer
    FindPartySlotWithMove VAR_RESULT, MOVE_ROCK_SMASH
    SetVar VAR_0x8004, VAR_RESULT
    GoToIfEq VAR_RESULT, MAX_PARTY_SIZE, FieldMoves_TryAppRockSmash
    CheckBadgeAcquired BADGE_ID_COAL, VAR_RESULT
    GoToIfEq VAR_RESULT, FALSE, FieldMoves_CantUseRockSmash
    Message FieldMoves_Text_WouldYouLikeToUseRockSmash
    ShowYesNoMenu VAR_RESULT
    GoToIfEq VAR_RESULT, MENU_YES, FieldMoves_UseRockSmashFromField
    CloseMessage
    GoTo FieldMoves_End
    End

FieldMoves_TryAppRockSmash:
    SetVar VAR_0x8004, ITEM_HM06
    SetVar VAR_0x8005, BADGE_ID_COAL
    SetVar VAR_0x8006, MOVE_ROCK_SMASH
    Call FieldMoves_CheckAppUsable
    GoToIfEq VAR_RESULT, FALSE, FieldMoves_CantUseRockSmash
    Message FieldMoves_Text_RockAppearsBreakable
    WaitButton
    Call FieldMoves_AskUseApp
    GoToIfEq VAR_RESULT, 0, FieldMoves_CantUseRockSmash
    GoToIfEq VAR_RESULT, 1, FieldMoves_UseRockSmashWithApp
    GoTo FieldMoves_End
    End

FieldMoves_UseRockSmashWithApp:
    SetVar VAR_0x8000, FIELD_MOVE_HELPER_SLOT_ROCK_SMASH
    GoTo FieldMoves_UseRockSmashFromMenuLocked
    End

FieldMoves_CantUseRockSmash:
    Message FieldMoves_Text_PokemonMayBeAbleToSmashRock
    WaitButton
    CloseMessage
    GoTo FieldMoves_End
    End

FieldMoves_UseRockSmashFromField:
    BufferPartyMonNickname 0, VAR_0x8004
    Message FieldMoves_Text_PokemonUsedRockSmash
    CloseMessage
    PlayHMCutIn VAR_0x8004
    StartDestroyObstacleAnimation 1, VAR_0x8005
    WaitTime 10, VAR_RESULT
    RemoveObject VAR_LAST_TALKED
    GetCurrentMapID VAR_0x8004
    CreateJournalEvent LOCATION_EVENT_USED_ROCK_SMASH, VAR_0x8004
FieldMoves_WaitForRockSmashAnimFromField:
    WaitTime 1, VAR_RESULT
    GoToIfEq VAR_0x8005, 0, FieldMoves_WaitForRockSmashAnimFromField
    GoTo FieldMoves_End
    End

FieldMoves_UseRockSmashFromMenu:
    LockAll
FieldMoves_UseRockSmashFromMenuLocked:
    BufferPartyMonNickname 0, VAR_0x8000
    SetVar VAR_0x8001, MOVE_ROCK_SMASH
    Call FieldMoves_MessageUsedRockSmash
    CloseMessage
    PlayHMCutIn VAR_0x8000
    StartDestroyObstacleAnimation 1, VAR_0x8005
    WaitTime 10, VAR_RESULT
    RemoveObject VAR_LAST_TALKED
    GetCurrentMapID VAR_0x8004
    CreateJournalEvent LOCATION_EVENT_USED_ROCK_SMASH, VAR_0x8004
FieldMoves_WaitForRockSmashAnimFromMenu:
    WaitTime 1, VAR_RESULT
    GoToIfEq VAR_0x8005, 0, FieldMoves_WaitForRockSmashAnimFromMenu
    ReleaseAll
    End

FieldMoves_Boulder:
    PlaySE SE_CONFIRM_sseq_3
    LockAll
    FacePlayer
    DoStrengthFunc FIELD_MOVE_FUNC_CHECK_ACTIVE, VAR_RESULT
    GoToIfEq VAR_RESULT, TRUE, FieldMoves_StrenghtAlreadyActive
    FindPartySlotWithMove VAR_RESULT, MOVE_STRENGTH
    GoToIfEq VAR_RESULT, MAX_PARTY_SIZE, FieldMoves_TryAppStrength
    CheckBadgeAcquired BADGE_ID_MINE, VAR_RESULT
    GoToIfEq VAR_RESULT, FALSE, FieldMoves_CantUseStrength
    Message FieldMoves_Text_WouldYouLikeToUseStrength
    ShowYesNoMenu VAR_RESULT
    GoToIfEq VAR_RESULT, MENU_YES, FieldMoves_UseStrengthFromField
    CloseMessage
    GoTo FieldMoves_End
    End

FieldMoves_TryAppStrength:
    SetVar VAR_0x8004, ITEM_HM04
    SetVar VAR_0x8005, BADGE_ID_MINE
    SetVar VAR_0x8006, MOVE_STRENGTH
    Call FieldMoves_CheckAppUsable
    GoToIfEq VAR_RESULT, FALSE, FieldMoves_CantUseStrength
    Message FieldMoves_Text_BoulderMayBeAbleToPush
    WaitButton
    Call FieldMoves_AskUseApp
    GoToIfEq VAR_RESULT, 0, FieldMoves_CantUseStrength
    GoToIfEq VAR_RESULT, 1, FieldMoves_UseStrengthWithApp
    GoTo FieldMoves_End
    End

FieldMoves_UseStrengthWithApp:
    SetVar VAR_0x8000, FIELD_MOVE_HELPER_SLOT_STRENGTH
    GoTo FieldMoves_UseStrengthFromMenuLocked
    End

FieldMoves_CantUseStrength:
    Message FieldMoves_Text_BoulderMayBeAbleToPush
    WaitButton
    CloseMessage
    GoTo FieldMoves_End
    End

FieldMoves_UseStrengthFromField:
    DoStrengthFunc FIELD_MOVE_FUNC_SET_ACTIVE
    FindPartySlotWithMove VAR_RESULT, MOVE_STRENGTH
    SetVar VAR_0x8004, VAR_RESULT
    BufferPartyMonNickname 0, VAR_RESULT
    Message FieldMoves_Text_PokemonUsedStrength
    PlayHMCutIn VAR_0x8004
    CloseMessage
    Message FieldMoves_Text_PokemonStrengthMadePossibleToMove
    WaitButton
    CloseMessage
    GetCurrentMapID VAR_0x8004
    CreateJournalEvent LOCATION_EVENT_USED_STRENGTH, VAR_0x8004
    GoTo FieldMoves_End
    End

FieldMoves_StrenghtAlreadyActive:
    Message FieldMoves_Text_StrengthMadePossibleToMove
    WaitButton
    CloseMessage
    GoTo FieldMoves_End
    End

FieldMoves_UseStrengthFromMenu:
    LockAll
FieldMoves_UseStrengthFromMenuLocked:
    DoStrengthFunc FIELD_MOVE_FUNC_CHECK_ACTIVE, VAR_RESULT
    GoToIfEq VAR_RESULT, TRUE, FieldMoves_StrenghtAlreadyActive
    DoStrengthFunc FIELD_MOVE_FUNC_SET_ACTIVE
    BufferPartyMonNickname 0, VAR_0x8000
    SetVar VAR_0x8001, MOVE_STRENGTH
    Call FieldMoves_MessageUsedStrength
    CloseMessage
    PlayHMCutIn VAR_0x8000
    Message FieldMoves_Text_PokemonStrengthMadePossibleToMove
    WaitButton
    CloseMessage
    GetCurrentMapID VAR_0x8004
    CreateJournalEvent LOCATION_EVENT_USED_STRENGTH, VAR_0x8004
    GoTo FieldMoves_End3

FieldMoves_RockyWall:
    PlaySE SE_CONFIRM_sseq_3
    LockAll
    FindPartySlotWithMove VAR_RESULT, MOVE_ROCK_CLIMB
    GoToIfEq VAR_RESULT, MAX_PARTY_SIZE, FieldMoves_TryAppRockClimb
    CheckBadgeAcquired BADGE_ID_ICICLE, VAR_RESULT
    GoToIfEq VAR_RESULT, FALSE, FieldMoves_CantUseRockClimb
    CheckHasPartner VAR_RESULT
    GoToIfEq VAR_RESULT, TRUE, FieldMoves_NoRockClimbingWithPartner
    Message FieldMoves_Text_WouldYouLikeToUseRockClimb
    ShowYesNoMenu VAR_RESULT
    GoToIfEq VAR_RESULT, MENU_YES, FieldMoves_UseRockClimbFromField
    CloseMessage
    GoTo FieldMoves_End2
    End

FieldMoves_TryAppRockClimb:
    SetVar VAR_0x8004, ITEM_HM08
    SetVar VAR_0x8005, BADGE_ID_ICICLE
    SetVar VAR_0x8006, MOVE_ROCK_CLIMB
    Call FieldMoves_CheckAppUsable
    GoToIfEq VAR_RESULT, FALSE, FieldMoves_CantUseRockClimb
    CheckHasPartner VAR_RESULT
    GoToIfEq VAR_RESULT, TRUE, FieldMoves_NoRockClimbingWithPartner
    Message FieldMoves_Text_WallIsVeryRocky
    WaitButton
    Call FieldMoves_AskUseApp
    GoToIfEq VAR_RESULT, 0, FieldMoves_CantUseRockClimb
    GoToIfEq VAR_RESULT, 1, FieldMoves_UseRockClimbWithApp
    GoTo FieldMoves_End2
    End

FieldMoves_UseRockClimbWithApp:
    SetVar VAR_0x8000, FIELD_MOVE_HELPER_SLOT_ROCK_CLIMB
    GoTo FieldMoves_UseRockClimbFromMenuLocked
    End

FieldMoves_CantUseRockClimb:
    Message FieldMoves_Text_RockyWallWillMoveScale
    WaitButton
    CloseMessage
    GoTo FieldMoves_End2
    End

FieldMoves_NoRockClimbingWithPartner:
    Message FieldMoves_Text_NoRockClimbingWithPartner
    WaitButton
    CloseMessage
    GoTo FieldMoves_End2
    End

FieldMoves_UseRockClimbFromField:
    FindPartySlotWithMove VAR_RESULT, MOVE_ROCK_CLIMB
    SetVar VAR_0x8004, VAR_RESULT
    BufferPartyMonNickname 0, VAR_RESULT
    Message FieldMoves_Text_PokemonUsedRockClimb
    CloseMessage
    UseRockClimb VAR_0x8004
    GetCurrentMapID VAR_0x8004
    CreateJournalEvent LOCATION_EVENT_USED_ROCK_CLIMB, VAR_0x8004
    GoTo FieldMoves_End2
    End

FieldMoves_UseRockClimbFromMenu:
    LockAll
FieldMoves_UseRockClimbFromMenuLocked:
    BufferPartyMonNickname 0, VAR_0x8000
    SetVar VAR_0x8001, MOVE_ROCK_CLIMB
    Call FieldMoves_MessageUsedRockClimb
    CloseMessage
    UseRockClimb VAR_0x8000
    GetCurrentMapID VAR_0x8004
    CreateJournalEvent LOCATION_EVENT_USED_ROCK_CLIMB, VAR_0x8004
    ReleaseAll
    End

FieldMoves_Water:
    PlaySE SE_CONFIRM_sseq_3
    LockAll
    CheckHasPartner VAR_RESULT
    GoToIfEq VAR_RESULT, TRUE, FieldMoves_CantUseSurf
    FindPartySlotWithMove VAR_RESULT, MOVE_SURF
    GoToIfEq VAR_RESULT, MAX_PARTY_SIZE, FieldMoves_TryAppSurf
    Message FieldMoves_Text_WouldYouLikeToUseSurf
    ShowYesNoMenu VAR_RESULT
    GoToIfEq VAR_RESULT, MENU_YES, FieldMoves_UseSurfFromField
    CloseMessage
    GoTo FieldMoves_End2
    End

FieldMoves_TryAppSurf:
    SetVar VAR_0x8004, ITEM_HM03
    SetVar VAR_0x8005, BADGE_ID_FEN
    SetVar VAR_0x8006, MOVE_SURF
    Call FieldMoves_CheckAppUsable
    GoToIfEq VAR_RESULT, FALSE, FieldMoves_End2
    Message FieldMoves_Text_WaterIsDeepBlue
    WaitButton
    Call FieldMoves_AskUseApp
    GoToIfEq VAR_RESULT, 0, FieldMoves_End2
    GoToIfEq VAR_RESULT, 1, FieldMoves_UseSurfWithApp
    GoTo FieldMoves_End2
    End

FieldMoves_UseSurfWithApp:
    SetVar VAR_0x8000, FIELD_MOVE_HELPER_SLOT_SURF
    GoTo FieldMoves_UseSurfFromMenuLocked
    End

FieldMoves_CantUseSurf:
    Message FieldMoves_Text_NoSurfingWithPartner
    WaitButton
    CloseMessage
    GoTo FieldMoves_End2

FieldMoves_UseSurfFromField:
    FindPartySlotWithMove VAR_RESULT, MOVE_SURF
    SetVar VAR_0x8004, VAR_RESULT
    BufferPartyMonNickname 0, VAR_RESULT
    Message FieldMoves_Text_PokemonUsedSurf
    CloseMessage
    UseSurf VAR_0x8004
    GetCurrentMapID VAR_0x8004
    CreateJournalEvent LOCATION_EVENT_USED_SURF, VAR_0x8004
    GoTo FieldMoves_End2
    End

FieldMoves_UseSurfFromMenu:
    LockAll
FieldMoves_UseSurfFromMenuLocked:
    BufferPartyMonNickname 0, VAR_0x8000
    SetVar VAR_0x8001, MOVE_SURF
    Call FieldMoves_MessageUsedSurf
    CloseMessage
    ReleaseObject LOCALID_PLAYER
    UseSurf VAR_0x8000
    LockObject LOCALID_PLAYER
    GetCurrentMapID VAR_0x8004
    CreateJournalEvent LOCATION_EVENT_USED_SURF, VAR_0x8004
    ReleaseAll
    End

FieldMoves_Fog_Unused:
    PlaySE SE_CONFIRM_sseq_3
    LockAll
    FindPartySlotWithMove VAR_RESULT, MOVE_DEFOG
    GoToIfEq VAR_RESULT, MAX_PARTY_SIZE, FieldMoves_CantUseDefog_Unused
    Message FieldMoves_Text_WouldYouLikeToUseDefog_Unused
    ShowYesNoMenu VAR_RESULT
    GoToIfEq VAR_RESULT, MENU_YES, FieldMoves_UseDefogFromField_Unused
    CloseMessage
    GoTo FieldMoves_End2
    End

FieldMoves_CantUseDefog_Unused:
    Message FieldMoves_Text_DeepFogDrapesArea_Unused
    WaitButton
    CloseMessage
    GoTo FieldMoves_End2
    End

FieldMoves_UseDefogFromField_Unused:
    FindPartySlotWithMove VAR_RESULT, MOVE_DEFOG
    SetVar VAR_0x8004, VAR_RESULT
    BufferPartyMonNickname 0, VAR_RESULT
    Message FieldMoves_Text_PokemonUsedDefog
    CloseMessage
    PlayHMCutIn VAR_0x8004
    GetCurrentMapID VAR_0x8004
    CreateJournalEvent LOCATION_EVENT_USED_DEFOG, VAR_0x8004
    GetCurrentMapID VAR_0x8004
    CallIfEq VAR_0x8004, MAP_HEADER_ROUTE_209_LOST_TOWER_5F, FieldMoves_SetFlagUsedDefog_Unused
    GoTo FieldMoves_End2
    End

FieldMoves_SetFlagUsedDefog_Unused:
    SetFlag FLAG_USED_DEFOG_IN_ROUTE_209_LOST_TOWER_5F
    Return

FieldMoves_UseDefogFromMenu:
    LockAll
FieldMoves_UseDefogFromMenuLocked:
    BufferPartyMonNickname 0, VAR_0x8000
    SetVar VAR_0x8001, MOVE_DEFOG
    Call FieldMoves_MessageUsedDefog
    CloseMessage
    PlayHMCutIn VAR_0x8000
    DoDefogFunc FIELD_MOVE_FUNC_SET_ACTIVE
    PlaySE SEQ_SE_DP_FBRADE_sseq
    ScrCmd_0C4
    GetCurrentMapID VAR_0x8004
    CreateJournalEvent LOCATION_EVENT_USED_DEFOG, VAR_0x8004
    GetCurrentMapID VAR_0x8004
    CallIfEq VAR_0x8004, MAP_HEADER_ROUTE_209_LOST_TOWER_5F, FieldMoves_SetFlagUsedDefog_Unused
    GoTo FieldMoves_End3

FieldMoves_UseFlashFromMenu:
    LockAll
    BufferPartyMonNickname 0, VAR_0x8000
    Message FieldMoves_Text_PokemonUsedFlash
    CloseMessage
    PlayHMCutIn VAR_0x8000
    DoFlashFunc FIELD_MOVE_FUNC_SET_ACTIVE
    ScrCmd_0C3
    WaitTime 42, VAR_RESULT
    GoTo FieldMoves_End3

FieldMoves_MessageSummoned:
    BufferPlayerName 0
    BufferPartyMonSpeciesNameWithArticle 1, VAR_0x8000
    BufferMoveName 2, VAR_0x8001
    Message FieldMoves_Text_PlayerSummonedPokemonToUseMove
    Return

FieldMoves_MessageUsedCut:
    GoToIfGe VAR_0x8000, FIELD_MOVE_HELPER_SLOT_BASE, FieldMoves_MessageSummoned
    Message FieldMoves_Text_PokemonUsedCut
    Return

FieldMoves_MessageUsedRockSmash:
    GoToIfGe VAR_0x8000, FIELD_MOVE_HELPER_SLOT_BASE, FieldMoves_MessageSummoned
    Message FieldMoves_Text_PokemonUsedRockSmash
    Return

FieldMoves_MessageUsedStrength:
    GoToIfGe VAR_0x8000, FIELD_MOVE_HELPER_SLOT_BASE, FieldMoves_MessageSummoned
    Message FieldMoves_Text_PokemonUsedStrength
    Return

FieldMoves_MessageUsedRockClimb:
    GoToIfGe VAR_0x8000, FIELD_MOVE_HELPER_SLOT_BASE, FieldMoves_MessageSummoned
    Message FieldMoves_Text_PokemonUsedRockClimb
    Return

FieldMoves_MessageUsedSurf:
    GoToIfGe VAR_0x8000, FIELD_MOVE_HELPER_SLOT_BASE, FieldMoves_MessageSummoned
    Message FieldMoves_Text_PokemonUsedSurf
    Return

FieldMoves_MessageUsedWaterfall:
    GoToIfGe VAR_0x8000, FIELD_MOVE_HELPER_SLOT_BASE, FieldMoves_MessageSummoned
    Message FieldMoves_Text_PokemonUsedWaterfall
    Return

FieldMoves_MessageUsedDefog:
    GoToIfGe VAR_0x8000, FIELD_MOVE_HELPER_SLOT_BASE, FieldMoves_MessageSummoned
    Message FieldMoves_Text_PokemonUsedDefog
    Return

@ VAR_RESULT is TRUE if the Hidden Moves app is installed, and the player has the HM (VAR_0x8004) and the badge (VAR_0x8005)
FieldMoves_CheckAppUsable:
    CheckPoketchAppRegistered POKETCH_APPID_FIELDMOVES, VAR_RESULT
    GoToIfEq VAR_RESULT, FALSE, FieldMoves_CheckAppUsableEnd
    CheckItem VAR_0x8004, 1, VAR_RESULT
    GoToIfEq VAR_RESULT, FALSE, FieldMoves_CheckAppUsableEnd
    CheckBadgeAcquired VAR_0x8005, VAR_RESULT

FieldMoves_CheckAppUsableEnd:
    Return

@ Asks whether to use the move (VAR_0x8006) from the app. VAR_RESULT is 0 if the app can't be used, 1 for yes, 2 for no
FieldMoves_AskUseApp:
    Call FieldMoves_CheckAppUsable
    GoToIfEq VAR_RESULT, FALSE, FieldMoves_AskUseAppUnavailable
    BufferMoveName 0, VAR_0x8006
    Message FieldMoves_Text_WouldYouLikeToUseApp
    ShowYesNoMenu VAR_RESULT
    GoToIfEq VAR_RESULT, MENU_YES, FieldMoves_AskUseAppYes
    CloseMessage
    SetVar VAR_RESULT, 2
    Return

FieldMoves_AskUseAppYes:
    CloseMessage
    SetVar VAR_RESULT, 1
    Return

FieldMoves_AskUseAppUnavailable:
    SetVar VAR_RESULT, 0
    Return

FieldMoves_End:
    ReleaseAll
    End

@ The Fly destination was picked in the Hidden Moves app: VAR_0x8000 is the helper Pokemon slot code, then the map and the position
FieldMoves_UseFlyFromApp:
    LockAll
    BufferPlayerName 0
    BufferPartyMonSpeciesNameWithArticle 1, VAR_0x8000
    BufferMoveName 2, MOVE_FLY
    Message FieldMoves_Text_PlayerSummonedPokemonToUseMove
    CloseMessage
    UseFlyFromApp VAR_0x8000, VAR_0x8001, VAR_0x8002, VAR_0x8003
    End

FieldMoves_PoketchError:
    LockAll
    GoToIfEq VAR_0x8000, 2, FieldMoves_PoketchErrorBadge
    GoToIfEq VAR_0x8000, 3, FieldMoves_PoketchErrorPartner
    GoToIfEq VAR_0x8000, 4, FieldMoves_PoketchErrorSurfing
    Message FieldMoves_Text_CantUseThatHere
    GoTo FieldMoves_PoketchErrorEnd

FieldMoves_PoketchErrorBadge:
    Message FieldMoves_Text_CantBeUsedUntilBadgeIsObtained
    GoTo FieldMoves_PoketchErrorEnd

FieldMoves_PoketchErrorPartner:
    Message FieldMoves_Text_CantUseWhenYouHaveSomeoneWithYou
    GoTo FieldMoves_PoketchErrorEnd

FieldMoves_PoketchErrorSurfing:
    Message FieldMoves_Text_YoureAlreadySurfing
    GoTo FieldMoves_PoketchErrorEnd

FieldMoves_PoketchErrorEnd:
    WaitButton
    CloseMessage
    ReleaseAll
    End

FieldMoves_End2:
    ReleaseAll
    End

FieldMoves_End3:
    ReleaseAll
    End

FieldMoves_Waterfall:
    PlaySE SE_CONFIRM_sseq_3
    LockAll
    FindPartySlotWithMove VAR_RESULT, MOVE_WATERFALL
    GoToIfEq VAR_RESULT, MAX_PARTY_SIZE, FieldMoves_TryAppWaterfall
    CheckBadgeAcquired BADGE_ID_BEACON, VAR_RESULT
    GoToIfEq VAR_RESULT, FALSE, FieldMoves_CantUseWaterfall
    Message FieldMoves_Text_WouldYouLikeToUseWaterfall
    ShowYesNoMenu VAR_RESULT
    GoToIfEq VAR_RESULT, MENU_YES, FieldMoves_UseWaterfallFromField
    CloseMessage
    GoTo FieldMoves_End2
    End

FieldMoves_TryAppWaterfall:
    SetVar VAR_0x8004, ITEM_HM07
    SetVar VAR_0x8005, BADGE_ID_BEACON
    SetVar VAR_0x8006, MOVE_WATERFALL
    Call FieldMoves_CheckAppUsable
    GoToIfEq VAR_RESULT, FALSE, FieldMoves_CantUseWaterfall
    Message FieldMoves_Text_LargeWaterfall
    WaitButton
    Call FieldMoves_AskUseApp
    GoToIfEq VAR_RESULT, 0, FieldMoves_CantUseWaterfall
    GoToIfEq VAR_RESULT, 1, FieldMoves_UseWaterfallWithApp
    GoTo FieldMoves_End2
    End

FieldMoves_UseWaterfallWithApp:
    SetVar VAR_0x8000, FIELD_MOVE_HELPER_SLOT_WATERFALL
    GoTo FieldMoves_UseWaterfallFromMenuLocked
    End

FieldMoves_CantUseWaterfall:
    Message FieldMoves_Text_WallOfWater
    WaitButton
    CloseMessage
    GoTo FieldMoves_End2
    End

FieldMoves_UseWaterfallFromField:
    FindPartySlotWithMove VAR_RESULT, MOVE_WATERFALL
    SetVar VAR_0x8004, VAR_RESULT
    BufferPartyMonNickname 0, VAR_RESULT
    Message FieldMoves_Text_PokemonUsedWaterfall
    CloseMessage
    UseWaterfall VAR_0x8004
    GetCurrentMapID VAR_0x8004
    CreateJournalEvent LOCATION_EVENT_USED_WATERFALL, VAR_0x8004
    GoTo FieldMoves_End2
    End

FieldMoves_UseWaterfallFromMenu:
    LockAll
FieldMoves_UseWaterfallFromMenuLocked:
    BufferPartyMonNickname 0, VAR_0x8000
    SetVar VAR_0x8001, MOVE_WATERFALL
    Call FieldMoves_MessageUsedWaterfall
    CloseMessage
    ReleaseObject LOCALID_PLAYER
    UseWaterfall VAR_0x8000
    LockObject LOCALID_PLAYER
    GetCurrentMapID VAR_0x8004
    CreateJournalEvent LOCATION_EVENT_USED_WATERFALL, VAR_0x8004
    ReleaseAll
    End

FieldMoves_Dummy8:
    End

    .balign 4, 0
