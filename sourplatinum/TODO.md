# Sour Platinum TODO

Ideas and planned work that hasn't been started yet.

## Hidden Moves Pokétch app

- [ ] **Unique Pokémon for each HM move.** Each of the eight moves in the app (Rock Smash, Cut, Strength, Fly, Defog,
  Surf, Rock Climb, Waterfall) should be performed by its own Pokémon, like the helper Pokémon in Brilliant Diamond
  and Shining Pearl, instead of the first Pokémon in the party. The Pokémon is used for the "used <move>!" message and
  the HM cut-in animation. The user of the move is chosen in `StartMenu_GetPoketchFieldMoveUser` in `src/start_menu.c`;
  the cut-in (`HMCutIn_StartTask`, `PlayHMCutIn`) takes a party slot, so it needs a way to show a Pokémon that isn't in
  the party. Decide first which Pokémon does which move.
- [ ] **Tell the player about the app whenever they get a new HM.** Add a short script message each time an HM is
  received (Cut, Fly, Surf, Strength, Defog, Rock Smash, Waterfall, Rock Climb) saying the move can be used from the
  Hidden Moves app. Only show it when the player has the app. The HMs are given by different NPCs, so each of those
  scripts needs the message. The Oreburgh Gate 1F hiker (Rock Smash) already explains the app.

## Battle

- [x] **Gen 5 style ability notifications.** Show a banner with the Pokémon and its ability name whenever an ability
  activates in battle (on switch-in for Intimidate and weather abilities, when Static or Rough Skin trigger, and so on),
  like in Black and White, instead of only the text message. Needs a battle UI element for the banner and a hook
  where the ability messages are shown in the battle scripts.
