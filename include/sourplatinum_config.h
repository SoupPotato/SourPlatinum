#ifndef POKEPLATINUM_SOURPLATINUM_CONFIG_H
#define POKEPLATINUM_SOURPLATINUM_CONFIG_H

// When set to 1, single-player battles run the main loop at 60 ticks per second.
// Code that was written for the original 30 Hz loop still runs on every other tick, so it keeps
// its original pace. Code that has been converted to run natively (see SysTask_SetTickDiv and the
// SP_NATIVE_* settings below) runs on every tick and produces real 60 fps motion.
// Set to 0 for the original 30 fps behavior.
#define SP_BATTLE_60FPS 1

// When set to 1, menu screens that have been converted (see MenuFps60_Begin) run at 60 ticks per second like the
// battles do, with their original pace. It does nothing while a link/wireless connection is active.
#define SP_MENUS_60FPS 1

// Wild Pokemon modifier for testing (replaces the Action Replay code). Type a number into the Poketch calculator and
// press L to set the species (National Dex number, 0 turns it off), R for the level (1-100, 0 turns it off) or
// Select for the nature (0-24, a bigger number turns it off). Every wild Pokemon created after that uses these
// values. A sound confirms each press. Keep this at 0 for the normal ROM.
#define SP_DEBUG_WILD_MODIFIER 0

// Registers the Poketch field moves app (HM app) as soon as the Poketch is created, for testing without the NPC.
#define SP_DEBUG_REGISTER_FIELD_MOVES_APP 0

// Debug switches for tracking down visual problems (1 = on, the normal setting).
#define SP_DEBUG_NATIVE_TASKS 1 // move animation tasks that run on every tick
#define SP_DEBUG_PARTICLES_60 1 // simulate particles at 60 Hz
#define SP_DEBUG_REDRAW_3D    1 // resubmit the 3D scene (Pokemon sprites, particles) on the in-between ticks
#define SP_DEBUG_BLEND_3D     1 // smooth Pokemon sprite motion between original-rate frames
#define SP_DEBUG_BLEND_OAM    1 // smooth OAM sprite motion between original-rate frames

// Pace of the code that runs natively at 60 fps, in percent of the original pace.
// 100 = same speed as the original game, 50 = twice as slow, 200 = twice as fast.
// These only have an effect while SP_BATTLE_60FPS is 1.
#define SP_PACE_ANIM_PERCENT      100 // move animation motion (lerps, shakes, revolutions)
#define SP_PACE_HEALTHBOX_PERCENT 100 // healthbox slide in/out and bobbing
#define SP_PACE_SPRITE_PERCENT    100 // send out, return, faint and other Pokemon sprite effects
#define SP_PACE_BARS_PERCENT      100 // HP and EXP bar draining/filling speed multiplier (200 = twice as fast)

// HP and EXP bars move at a constant visual speed, however much HP or EXP is involved (like Gen 5).
// The HP bar is 48 pixels long and the EXP bar 96 pixels long. At 60 pixels per second the HP bar would move
// exactly one pixel on every 60 Hz tick, which looks the smoothest. The numbers count along with the bar.
#define SP_BAR_HP_PIXELS_PER_SECOND  60
#define SP_BAR_EXP_PIXELS_PER_SECOND 60
#define SP_PACE_TEXT_PERCENT      100 // message text printing speed and scrolling (200 = twice as fast)

#endif // POKEPLATINUM_SOURPLATINUM_CONFIG_H
