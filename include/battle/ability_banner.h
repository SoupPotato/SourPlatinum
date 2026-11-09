#ifndef POKEPLATINUM_BATTLE_ABILITY_BANNER_H
#define POKEPLATINUM_BATTLE_ABILITY_BANNER_H

#include "struct_decls/battle_system.h"

#include "battle/battle_context.h"

#define ABILITY_BANNER_NO_MESSAGE 0xFF

void AbilityBanner_TryShow(BattleSystem *battleSys, const BattleMessage *battleMsg, u8 msgIdx);

BOOL AbilityBanner_IsBannerOnlyMessage(const BattleMessage *battleMsg);

BOOL AbilityBanner_MessageNamesAbility(const BattleMessage *battleMsg);

void AbilityBanner_OnMessage(const BattleMessage *battleMsg);

void AbilityBanner_OnMessageBoxCleared(void);

BOOL AbilityBanner_IsHideMessage(const BattleMessage *battleMsg);

void AbilityBanner_Hide(void);

void AbilityBanner_FreeAll(void);

void AbilityBanner_AttachMessage(u8 msgIdx);

BOOL AbilityBanner_IsChangeMessage(const BattleMessage *battleMsg);

void AbilityBanner_StartChange(BattleSystem *battleSys, const BattleMessage *battleMsg);

BOOL AbilityBanner_CanShow(void);

BOOL AbilityBanner_IsIntroPlaying(void);

#endif
