# OUT BY FIVE — Complete Project Handoff Document

**Purpose of this document:** This is a complete technical and design record of "Out By Five," a browser-based 2D stealth-platformer game. It is written so that another LLM (or a human developer) with zero prior context can read this file and immediately understand everything that has been built, how it works, and how to continue development on it without re-deriving decisions that have already been made.

**Last updated:** 2026-09-28 (Loot moved into enemy territory — see §26)
**Single source of truth (code):** `game.html` — one self-contained HTML file (~6,551 lines) with all HTML, CSS, JS, and embedded font assets inline. No build step, no external dependencies, no CDN calls at runtime.

---

## 1. What This Game Is

**Out By Five** is a 2D side-scrolling stealth-platformer. You play an office Employee who must physically walk/run/platform across a sprawling 12,520px-wide office floor to reach the elevator lobby before the in-game clock hits 5:00 PM. Along the way, Managers, a Director, and Chatty Coworkers patrol the space; getting spotted by a Manager or Director triggers a "quick sync" (meeting) that sends you back to a checkpoint. The tone is corporate-office satire — meeting invites, "fake work," badge scanners, printer jams, pantry coffee — layered over classic stealth-platformer mechanics (line-of-sight detection, hiding, distraction, timed escalation).

It is built entirely in vanilla JavaScript using the HTML5 Canvas 2D API. There is no framework, no game engine, no asset pipeline — everything (sprites, backgrounds, UI, particles, sound) is drawn/synthesized procedurally in code at runtime.

---

## 2. Tech Stack

| Layer | Technology |
|---|---|
| Rendering | HTML5 `<canvas>`, Canvas 2D API (no WebGL) |
| Language | Vanilla JavaScript (ES6+), no TypeScript, no modules/bundler |
| Art | 100% procedural pixel art — drawn with `ctx` primitives (rects, arcs, paths), cached to offscreen canvases per animation frame for performance |
| Audio | Web Audio API — all sound effects and ambient music are **synthesized at runtime** (oscillators/envelopes), no audio files |
| Fonts | **Fredoka** (weights 500/600/700) and **Orbitron** (weight 800) — embedded directly as base64 `woff2` data URIs inside a `<style>` block (fully self-contained, no Google Fonts network call at runtime). A third font, "Chunky Puffly," is referenced via `local()` only (falls back to Fredoka if not installed on the user's machine) |
| Persistence | `localStorage` — used for settings (`obf-settings`) and best-time/leaderboard-style records |
| Input | Keyboard (primary) + on-screen touch controls (auto-detected via `matchMedia("(pointer: coarse)")`) for mobile |
| Haptics | `navigator.vibrate()` with named vibration patterns, progressively enhanced (silently no-ops where unsupported) |
| Deployment | Single static `.html` file — can be opened directly from disk or hosted anywhere as a static asset |

**Canvas resolution:** Internal fixed game resolution is **1104 × 621px** (16:9). `fitCanvasResolution()` scales this by one uniform factor to fit any viewport (never stretches X/Y independently), centers it, and paints a full-bleed backdrop in matching office colors into any leftover gutter — so there are never black bars, but the game itself is never distorted. This logic lives around line 750 (`fitCanvasResolution`) and pairs with `paintFullBleedBackdrop()` (~line 3078).

There is a portrait-lock prompt for touch devices (`#rotatePrompt`) since this is landscape-only — a phone held upright shows a "turn your phone sideways" screen instead of a squashed layout.

---

## 3. File Structure (inside `game.html`)

The file is one long `<script>` block. Rough map by line number (as of last edit, ~6,551 total lines):

| Lines (approx) | Section |
|---|---|
| 1–13 | `<!doctype>`, `<head>`, embedded `@font-face` (base64 Fredoka/Orbitron), Chunky Puffly local() declaration |
| ~14–70 | `<style>` — layout (`.wrap`, `#game` canvas styling with `image-rendering: pixelated`), portrait-lock media query |
| ~72–80 | `<body>` — canvas element, control hint text, rotate-prompt div |
| ~85–108 | Opening JS comment block describing the sprite system |
| 109–719 | `const Sprites = (() => {...})()` — the procedural pixel-art character sprite generator (heads, torsos, parametric limbs for walk/run cycles, expression overlays, props like tablets/clipboards/briefcases). Auto-outlines every frame in 1px dark, caches to canvas, generates mirrored left-facing copies |
| 720–786 | Canvas/context setup, core constants: `W=1104`, `H=621`, `GY=530` (ground Y), `LEVEL_W=12520`, `GRAV=2300`, `JUMP_V=790`, `RUN_SPEED=250`, `JUMP_BUFFER=60`, `COYOTE=80`, `SHIFT_DURATION=105` (real seconds mapped to the in-fiction 4:55→5:00 PM window), font family constants (`F_UI`, `F_FUN`, `F_TEXT`, `F_STAMP`, `F_HEADING`) |
| 788–806 | Color palette object `C` (hair/skin/teal/navy/paper/gold/etc. — shared across all character and UI rendering) |
| 809–884 | `ZONES` array (the 6 level zones, each with x0/x1 bounds, wall color, accent color, floor material) + `zoneAt()`, `drawZoneFloors()` (per-zone floor texture: carpet/lino/tile/wood/marble, each with unique speckle/plank/seam rendering) |
| 886–932 | Settings persistence (`settings`, `saveSettings`), haptics (`HAPTIC` named patterns, `Haptics.buzz()`) |
| 934–1198 | `const Sound = (() => {...})()` — Web Audio synthesis engine (see §7) |
| 1199–1305 | Input handling: `keys`/`pressed` sets, `keyDown`/`keyPressed` helpers, touch button rects, menu/settings/how-to-play hit rects, `canvasPoint()`, `hit()`, touch release handling |
| 1306–1358 | Pause menu state machine (`menu`, `menuItems()`, `openMenu`/`closeMenu`/`menuSelect`/`menuClick`/`updateMenu`) |
| 1359–1394 | Seeded RNG (`mulberry32`), daily seed (`todayKey`/`todayLabel` — same office layout for everyone each calendar day), world arrays (`objects`, `pickups`, `meetingRooms`, `hazards`), platform-type sets (`PLATFORM`, `ONE_WAY`, `SOLID`) |
| 1396–1509 | `seedLevel()` — procedurally places every desk, cabinet, printer, coffee machine, meeting room, etc. across all 6 zones using the seeded RNG (also calls `seedLoot()`, see §20) |
| 1510–1585 | `enemies` array, `newEnemy()`, `seedEnemies()` — places Managers/Directors/Coworkers with patrol routes per zone |
| 1576–1623 | `player` object (all state fields), `throwables`/`fallers`/`particles` arrays, `spawnPantryFaller()`, `spawnParticles()` |
| 1623–1728 | Physics/collision helpers: `clamp`, `overlap`, `playerBox`, `gameSec`/`clockString`/`elapsedString`, `onScreen`, `collideVertical`, headache/door-swing logic (`canGetHeadache`, `triggerHeadache`), `updateFallers`/`drawFallers` |
| 1728–1930 | `updateHazards` (swinging doors, printer jams), `resolveSolids`, `collideHorizontal`, `moveXSolid`, enemy-specific collision helpers, **line-of-sight system** (`SIGHT_BLOCKERS`, `hasLineOfSight`, `phoneDown`, `visionRange`, `enemySeesPlayer`), **escalation table `ESC`** (5 stages, see §6), `BANNERS` (zone-transition callout text), `stageNow()`/`esc()` |
| 1932–1975 | `game` state object (the master state machine — see §5), `stats`, `hints`, `pop()`/`shake()` juice helpers, `SCORE` table (see §9, includes the office-loot entries, §20), `addScore()` |
| 1975–2012 | `startGame()` — resets all state for a fresh run |
| 2012–2098 | `update(dtMs)` — **the master per-frame update dispatcher**, branches on `game.mode` |
| 2098–2178 | `updateCamera`, `tickParticles`, `updateEscalation`, `updateClockCues`, `updateWorld` |
| 2178–2363 | `updatePlayer(dt, dtMs)` — **all player logic**: room-hiding, sitting/faking-work, sit input, file-throw input, ladders, running, jump-buffer/coyote-time, duck/hide/room-entry, physics integration, head-bonk detection, landing FX |
| 2363–2523 | `updateEnemy(e, dt)` — Manager/Director AI: awareness gain/drain, state machine (`walk`/`pause`/`chase`/`investigate`/`inspect`/`return`/`stunned`), phone-walker distraction gimmick, `awarenessCues()` (sound/haptic/badge triggers with hysteresis, "close call" detection) |
| 2523–2598 | `updateCoworker(e, dt)` — Chatty Coworker AI: dodge detection (vaulting over their head), "trap" conversation-block state, coffee-pot gossip drift |
| 2598–2680 | `interactEnemies` (stomp/hit contact resolution), `stomp()`, `registerKO()`, `jamPrinter()` |
| 2680–2790ish | `updateThrowables` (file-throw physics/collision), `updatePickups` (coffee/phone/file/loot pickup logic — loot branch is a short early-return block at the top of the loop, see §20) |
| 2790ish–2900 | Meeting invite generation (`TITLE_POOL`, `INVITES`, `LENGTH_POOL`), `caughtBy()`, `updateCaught()`, `resumeAfterCaught()`, `beginExit()`, `updateExit()` |
| 2900–2986 | Elevator ride sequence (`RIDE` timing constants, `rideFloor`, `RIDE_LINES`, `renderRide()`), `runTitles()` (earned-title logic), `recordBest()`/`readBest()` (localStorage best-time tracking) |
| 2986–3078 | `win()`, `drawConfetti()`, `zoneStatus()` (per-zone clean/1-sync/2+-sync/not-reached tracking for the results screen), `shareText()`/`copyResult()` (clipboard share-card text), `lose()` |
| 3078–3202 | `paintFullBleedBackdrop()`, `render()` (top-level render dispatcher), `renderWorld(camX)` |
| 3202–3745 | Background decor system: `decor` array, `MISSION`/`NOTICEBOARDS` data, `seedDecor()`, `renderDecor()`, dozens of small `draw*()` functions for individual background props (badge scanner, wall cabinet, posters, wall clock, plants, cooler, chairs, noticeboards, boxes, umbrellas, totes, sofas, ladders, stools), `renderCeiling()` |
| 3746–4335 | **Procedural city skyline** (visible through windows) — time-of-day sky gradient (`skyAt`, `dayProgress`), parallax city blocks/buildings/cranes/spires/towers/billboards/water-tanks/rooftop-gardens, all seeded and layered (`cityLook`, `cityCells`, `cityBlock`, etc.), window-glass rendering with reflection wash |
| 4336–4410 | Swinging pantry doors (`drawDoorPanel`, `drawSwingPanels`) — these are the headache/hazard source |
| 4410–4670 | `drawObject(o, sx)` — renders every placed world object (desks, cabinets, printers, etc.) by type |
| 4670–4748ish | `drawPickup` (file/coffee/phones primitives + the office-loot render branch, §20/§21), `groundShadow`, `playerAnim()` (state → animation-frame mapping), `drawPlayer(camX)` |
| 4748–5138ish | Enemy dialogue system (`CHATTER` phrase pools, `say()`), cone-of-vision rendering (`conePatterns`), `drawEnemy()`, per-archetype prop rendering (`drawManagerProp`, title-screen phone/watch-check idle animations), FX (`drawStars`, `drawSweatDrop`, `drawLanyard`), speech bubbles (`wrapText`, `drawSpeech`), awareness badge UI (`drawAwarenessBadge`) |
| ~5138–5171 | `drawThrowable`, `fmtClock`/`fmtSecs` |
| ~5171–5247 | Custom bitmap pixel font (`PX_FONT`, `drawPixelChar`, `pixelTextWidth`, `drawPixelText`) — used for retro-style HUD elements, distinct from the Fredoka/Orbitron canvas text |
| ~5247–5280 | `roundRect()` — shared rounded-rectangle-with-shadow primitive used everywhere (cards, buttons, panels) |
| ~5280–5480ish | Item-icon art system (`ITEM_PAL`, `ITEM_ART`, `itemSprite` cache, `drawItem`, `drawSteam`) — includes `file`/`coffee`/`phones`/settings-glyph art AND the three office-loot sprites (`snack`/`charger`/`powerBank`, see §20/§21), `drawPowerBar`, `drawMiniAvatar`, HUD icon drawers (folder/coffee/headphones/menu) |
| ~5480–5641 | `renderHUD()` — the full HUD: timer, coffee/headphone/file counters, awareness badges, invulnerability blink |
| ~5641–5741 | `renderTitle()` — title screen |
| ~5741–5981 | **How to Play** system: `HOWTO_CONTROLS`, `HOWTO_CREW`, `HOWTO_OFFICE` data, `pixelPanel`, `howtoChrome`/`howtoHeader`/`howtoNav`, three pages (`howtoPage0` controls, `drawCrewCard` for enemy roster, `howtoPage1` office guide, `drawOfficeRow`, `howtoPage2`), `renderHowToPlay()` |
| ~5981–6094 | `renderMenu()` (pause menu + settings toggles), `renderPause()` (alias), `drawCalendarIcon` |
| ~6094–6197 | `renderCaught()` — the "meeting invite" modal shown when caught (Teams-style calendar invite UI, ACCEPTED rubber-stamp animation, Restart/Continue CTA buttons) |
| ~6198–6314 | `renderResultCard(win)` — shared Win/Lose results screen (score, stat rows incl. "Office loot n / 17", earned-title pill, best-time comparison, Share/Play-Again CTA buttons), `renderWin()`/`renderLose()` aliases |
| ~6318–6411 | Meeting room rendering (`drawMeetingRoom`, `drawRoomGlass`), `drawElevatorInterior` |
| ~6411–6459 | `renderPops` (floating score/text popups), `checkCallouts` (zone-transition banner triggers) |
| ~6459–6517 | Context-sensitive interaction prompt system (`getPrompt`, `drawPrompt`), `drawTouchControls` |
| ~6517–6533 | Portrait-lock media query handling, **`loop(t)`** — the `requestAnimationFrame` main loop |
| ~6533–end | Font-loading gate (`fontsReady` via `document.fonts.load`) that defers game start until Fredoka is actually rasterizable, then kicks off `loop()` |

(Line numbers shifted slightly after §20/§21's additions — search by function name, don't trust exact numbers.)

---

## 4. Physics & Movement Constants (exact values)

```js
W = 1104, H = 621          // internal canvas resolution
GY = 530                   // ground Y coordinate
LEVEL_W = 12520            // total level width in px
GRAV = 2300                // gravity, units/s²
JUMP_V = 790                // initial jump velocity, units/s (upward)
RUN_SPEED = 250              // ground run speed, units/s
JUMP_BUFFER = 60             // ms — pressing jump slightly before landing still triggers a jump
COYOTE = 80                  // ms — coyote time after walking off a ledge
SHIFT_DURATION = 105          // REAL seconds mapped to the fictional 4:55→5:00 PM (5 in-fiction minutes / 300s)
```

Note: `SHIFT_DURATION` (105 real seconds) is intentionally shorter than a literal 5-minute (300s) real-time mapping — this was tuned so a clean, confident run comfortably beats the clock without the whole experience dragging to a literal 5 real minutes. `gameSec()` converts elapsed `timeMs` into a 0–300 "fictional seconds" value used for the clock display and escalation staging.

Player dimensions (from the original design spec, matches sprite system): standing 24×46px, ducking ~24×30px, visual scale 1.15×.

**Jump feel details actually implemented:**
- Variable jump height: releasing the jump key early while still ascending cuts `vy` by 0.6× (a tap ≈ short hop, a hold ≈ full jump), gated to kick in only after 100ms post-jump so it can't clip a jump instantly.
- Jump buffering + coyote time are both implemented as described above (`player.jumpBuffered`, `sinceGround < COYOTE`).
- Head-bonk detection: if `vy < 0` (rising) and the player's rising head crosses the bottom edge of a solid object, they're stopped and `vy` zeroed — you can't jump through the underside of a cabinet/bookshelf/printer.
- Landing sound intensity is fall-speed–dependent (`landHard` vs `land`), with more dust particles on hard landings (`fallSpeed > 950`).
- Skid-stop dust puffs trigger on sudden stops or direction reversals at speed (`Math.abs(prevVx) > 150`, cooldown 160ms).

---

## 5. Game State Machine

`game.mode` is the master state, one of:

```
TITLE → HOWTOPLAY → PLAY ⇄ PAUSED
                       ↓         ↑
                     CAUGHT ─────┘ (resumes to PLAY after hold+invul)
                       ↓
                     EXIT (elevator ride sequence) → WIN
                     (or, if clock runs out while in PLAY) → LOSE
WIN / LOSE → (Space/Enter) → PLAY (restart) via startGame()
```

`update(dtMs)` (line ~2012) is a big early-return dispatcher on `game.mode`:
- **TITLE**: waits for Space/Enter/H to call `startGame()`.
- **HOWTOPLAY**: paginated (3 pages), arrow keys/Space/Enter to navigate, Escape backs up a page or returns to TITLE.
- **WIN/LOSE**: Space/Enter restarts, `C` copies a shareable result-text summary to clipboard.
- **PAUSED**: fully frozen (no enemy movement, no timer, no particle ticking).
- **CAUGHT**: runs `updateCaught(dtMs)` + particle ticking only — everything else frozen.
- **EXIT**: runs the elevator-ride cinematic (`updateExit`) + camera + particles.
- **PLAY**: the full simulation — clock, escalation, world, player, all enemies, contact resolution, throwables, pickups, particles, hazards, fallers, solids, checkpoint/zone-progress tracking, badge-scanner checkpoints, camera.

Reaching the elevator (`player.x >= LEVEL_W - 150 && player.grounded`) is checked *before* the time-out check each frame, so a same-frame race between "reached elevator" and "clock expired" always resolves in the player's favor — arriving is never stolen by the clock ticking over in the same tick.

### CAUGHT flow in detail
`caughtBy(e)` fires when any Manager/Director's `awareness` reaches 100. It:
1. Freezes player control, plays a short "scene" with an enemy-specific dialogue line pulled from an invite pool (`TITLE_POOL`/`INVITES`).
2. Generates a fake meeting invite (`renderCaught()` shows a Microsoft-Teams-style invite card: purple header band, calendar icon, meeting title, "You're in this one (No escape.)" subtext, WHEN/LENGTH/ORGANIZER/AGENDA rows wrapped to fit the card, and an animated "ACCEPTED" rubber stamp that slams in with rotation+scale keyframing after ~450ms).
3. Once `game.caughtHold` is true (scene settled), shows two CTA buttons: **↻ RESTART SHIFT** (secondary, white bg/purple border+text) and **▶ CONTINUE** (primary, solid purple bg/white text) — side-by-side, filling the card width with equal-width halves and a small gap (see §11 for the exact button-layout math, which was the most recently completed polish pass).
4. `resumeAfterCaught()` resets the player to `checkpoint` position (~100px behind the catch point per the original design spec — actual respawn logic uses the tracked `player.checkpoint`), grants 1.5s invulnerability (`player.invulUntil`) during which the player sprite blinks and cannot be re-caught, and `stats.syncs` increments.

### EXIT / WIN flow
`beginExit()` triggers when the player reaches the elevator zone; `updateExit()` runs a scripted ride sequence (`RIDE = { start: 1650, end: 3500, done: 4100, top: 12 }` — millisecond timeline for doors closing, floor-number readout climbing via `rideFloor()`, flavor lines from `RIDE_LINES`), then transitions to `WIN`. `win()` calls `recordBest()` (compares this run's clock-out time against `localStorage`-persisted daily-best and all-time-best), computes final score, and populates `game.result`.

---

## 6. Difficulty Escalation

Escalation is driven by `stageNow()` = `min(4, floor(gameSec() / 60))` — i.e., 5 stages, one per in-fiction minute (4:55, 4:56, 4:57, 4:58, 4:59), each mapping to one entry of the `ESC` table:

```js
const ESC = [
  { speed: 0.85, vision: 1.0,  pause: 1700 },   // 4:55 — calm
  { speed: 0.95, vision: 1.0,  pause: 1300 },   // 4:56
  { speed: 1.05, vision: 1.05, pause: 1000 },   // 4:57 — managers on the move
  { speed: 1.15, vision: 1.1,  pause: 800  },   // 4:58 — director roams
  { speed: 1.3,  vision: 1.18, pause: 500  },   // 4:59 — chaos
];
```

`speed` multiplies enemy movement, `vision` multiplies detection range, `pause` shortens/lengthens patrol-endpoint dwell time. Zone-transition banner text is shown from the `BANNERS` map keyed by stage index (e.g. stage 3 → "4:58 · The Director is on the prowl.").

---

## 7. Audio (Web Audio Synthesis)

All audio is generated procedurally via the Web Audio API in the `Sound` IIFE (~line 934) — there are no audio files anywhere in the project. Each enemy archetype has a distinct sonic identity by design:
- **Manager**: bright/comedic — triangle/square oscillators, higher pitch.
- **Coworker**: bubbly/social — sine-wave "pops" and chatter blips.
- **Director**: low/serious — saw/triangle oscillators, lower pitch.

Named SFX events include (per the original design spec, implemented as `Sound.play("<name>")` calls throughout): jump, land/landHard, hide, sit, type (fake-work typing), throw, denied (no files), drop, bump, door/doorClose, badgeScan, dodge, chatter, phew (close-call), menu, powerDown, mgrNotice/mgrSuspicious, dirNotice/dirSuspicious, cwkNotice, **loot** (office-loot pickup, §20), and more. There is an ambient `Sound.startMusic()` layer and `Sound.setMuffle()` (used when wearing headphones/phones concealment, and inside meeting rooms) that low-pass-filters the mix. Mute is toggled with `M` and persisted to `settings.sound` / `localStorage`.

---

## 8. Haptics

`navigator.vibrate()`-based, progressively enhanced (silently no-ops on unsupported browsers/desktop). Named patterns in `HAPTIC` (~line 898), each deduped with an 80ms per-pattern cooldown so the game loop re-firing the same event a frame later doesn't double-buzz, while a genuine fast sequence (jump→land→dodge) still gets every pulse:

```js
jump:       [20]
hardLand:   [35]
dodge:      [30, 35, 45]
stomp:      [60]
fileThrow:  [15]
fileHit:    [45, 25, 55]
coffee:     [25, 25, 25]
headphones: [20, 30, 40]
notice:     [35]
danger:     [50, 40, 50]
caught:     [90, 45, 120]
win:        [35, 30, 35, 30, 70]
doorClose:  [45, 25, 35]
headache:   [55, 60, 30, 60, 30]
loot:       [18, 30, 28]              // office-loot pickup (§20)
```

This matches the "Haptic Instructions" project doc exactly and is fully implemented (`Haptics.buzz(pattern, force)`), gated by a `settings.haptics` toggle.

---

## 9. Scoring System

A secondary "Escape Score" mastery layer sits on top of the core win/lose condition (reaching the elevator before 5:00 PM is still the actual win condition — score is bragging-rights/replayability, not a gate):

```js
dodgeCoworker:   100 pts  "DODGED!"
fileHitManager:  100 pts  "FILE HIT!"
stompManager:    150 pts  "STOMP!"
fileHitDirector: 250 pts  "RISKY BUSINESS"
closeCall:       200 pts  "CLOSE CALL!"
hide:            100 pts  "SNEAKY"
fakeWork:         75 pts  "LOOK BUSY!"
newZone:         250 pts  "NEW ZONE!"
elevator:       1000 pts  "CLOCKED OUT!"
noMeetings:     1000 pts  "NO MEETINGS"       (bonus for a full run with 0 syncs-caught)
snack:           500 pts  "PRIORITIES."               (office loot, §20)
charger:         750 pts  "ABSOLUTELY NOT LEAVING THIS."  (office loot, §20)
powerBank:      1000 pts  "CRISIS AVERTED."           (office loot, §20)
```

Every score event spawns a floating popup (`addScore(key, x, y)` → pushes to `game.pops` with label + `+N` text, color-coded per event, 850ms lifetime) and pulses the HUD score readout (`game.scoreBumpAt`).

Tracked run stats (shown on the results screen): dodges, stomps (manager KOs), fileHits, closeCalls, syncs (times caught), coffee used, hides (successful hide-outs where an enemy walked off none the wiser), fakeWins (successful fake-work saves), trapped count, per-zone sync counts (`zoneSyncs[6]` for the zone-status strip), **loot** (office-loot items collected, out of `LOOT_TOTAL` = 17, §20).

Best-time tracking: `recordBest()`/`readBest()` persist daily-best and all-time-best clock-out times to `localStorage`, surfaced on the Win screen as "NEW ALL-TIME BEST!" / "NEW BEST TODAY!" / a quiet "TODAY'S BEST — ALL-TIME BEST" comparison line.

A seeded daily RNG (`mulberry32(todayKey())`) means the **level layout, enemy placement, and pantry-drop item mix are identical for every player on a given calendar day** (like a daily-puzzle format), while still varying day to day. `game.dropMix` (env/near/tgt pickup-spawn-location weighting) also jitters ±8 percentage points per day off the same seed so the split isn't perfectly learnable/memorizable even across days.

---

## 10. Full Gameplay Mechanics Reference

*(This section restates and confirms the original GDD mechanics against what is actually implemented in code — all of the following are live in `game.html`.)*

### Player movement
- ← → / A D: run at `RUN_SPEED` (250 u/s), ×1.4 with coffee active, ×0.55 (stacking) if dazed by a headache.
- Space / ↑ / W / Z: jump (`JUMP_V` = 790 u/s), buffered + coyote-timed, variable height on early release.
- ↓ / S: duck (grounded) → if standing under an object with `hideable`/desk-like type, becomes fully **hidden**.
- ↓ + Space (while standing on a one-way platform): drop through.
- Ladders: hold ↑ near a ladder base to grab on; climbing sets discrete "climb steps" that trigger a `type`-style sound; sideways movement without ↑/↓ held releases the ladder (a diagonal ↑+→ input still climbs).

### Hiding
- Hidden-under-desk: enemy awareness on nearby Managers **drains** while hidden (`-1.1/s` manager per GDD; implemented via per-enemy `drain` accumulation with different base rates for Manager vs Director — Directors' vision "pierces" hiding much more weakly, i.e. drain is slower for them). If an enemy is within ~140px of a hidden player, `player.hideDanger` is flagged — successfully un-hiding *without* being caught after a hideDanger flag awards the "SNEAKY" score bonus (a `hideWins` stat).
- Sitting + "fake work" (hold E at an empty chair/desk): drains awareness even faster while actively faking (`blending` in `updateEnemy` — while `player.sitting && player.fakingWork`, awareness on non-Director enemies who can currently see the player drains at `-130 * dt`, i.e. very fast). Directors are explicitly **not fooled** by fake work (only non-Director enemies get the blending discount). A successful "held your nerve through a real close call" fake-work session awards "LOOK BUSY!" bonus (`fakeWins` stat).
- Meeting rooms: pressing ↓ near an unbooked room doorway enters `player.inRoom` — fully frozen/invisible until the player moves/jumps back out; entering plays a door-close sound + haptic and a "SHH…" popup.
- Headphones/phones pickup: full concealment — while active, ALL enemy awareness is frozen/heavily drained (`+240` drain bonus term in the awareness-drain branch) regardless of line of sight.

### Offense
- Paper files: max 3 held, thrown with F (540 u/s horizontal, slight upward arc). Hitting a Manager stuns them (with a "stars" KO effect via `registerKO`/`stomp`-adjacent code) at ~2.2s per the GDD; hitting a Director stuns for a shorter ~1.0s and can flip the Director into a more-attentive "inspecting" state after impact. Coworkers cannot be hit directly (not targetable by files per design).
- Stomping: jumping on top of a Manager also KOs/stuns them (`stomp(e)`).

### Power-ups
- Coffee: ~8s speed boost (×1.4 run speed), HUD shows "CAFFEINATED 00:0X" countdown.
- Phones/headphones: ~8s full concealment, HUD shows "HEADPHONES 00:0X" countdown, very limited supply (max 2 in play at once per GDD).
- **Office loot (snack/charger/powerBank) is explicitly NOT a power-up** — score only, see §20.

### Enemies — implemented behaviors

**Manager** (`updateEnemy`, non-Director branch):
- Patrol between two waypoints (`route.a`/`route.b`) at `e.speed * esc().speed`, pausing at each end (`esc().pause`, randomized ±).
- Awareness 0→100, driven by `enemySeesPlayer()` (line-of-sight + distance-based gain, `SIGHT_BLOCKERS` set (bookshelf/cabinet/printer/coffee-machine) blocks LOS entirely) and drained when unseen, hidden, in a room, or wearing phones.
- States: `walk → pause → chase → (investigate|inspect|return) → walk`, plus `stunned` after being hit/stomped.
- Reaching awareness 100 → `caughtBy(e)`.
- Some Managers are the "phone" variant: head-down most of the time, glance up on a timer rhythm (reduced vision while looking down, per `phoneDown()`).

**Director** (same `updateEnemy` function, `isDir` branches throughout):
- Longer patrol reach, larger vision range (`visionRange` multiplied by `esc().vision`, itself higher for Directors' base `visRange`), faster awareness gain (`gain = 72 * ...` vs Manager's `60 * ...`), slower awareness *drain* while the player hides (`+36` vs Manager's `+66` bonus drain term — i.e., hiding is markedly less effective against a Director).
- Not fooled by fake-work blending at all.
- After reaching `chase` and awareness ≥30, transitions to a unique `inspect` state: walks to the last-seen location (`e.lastSeenX`) and "looks around" for ~2.4s before returning to patrol — a distinct behavior Managers don't have.
- Late-game "hunter" Directors (`e.hunter && stageNow() >= 3`) get an extended roaming route (`{a: 8800, b: LEVEL_W - 180}`) instead of a fixed short patrol, i.e. actively hunting across the Executive Floor / Elevator Lobby in the final stretch.

**Chatty Coworker** (`updateCoworker`):
- No hidden-awareness mechanic at all — actively "seeks you out" by design. Detection is pure distance + LOS + not-hidden/not-in-room/not-phones (`sees` check).
- States: `wander → hail → trapping (conversation-block) → dodged/wander`.
- **Dodge**: jumping over a coworker's head while airborne and passing to her other side (`side !== e.lastSide && !grounded && y < e.y-56 && dist<44`) triggers a "DODGED!" score event, sound, and haptic, and if she was mid-trap it ends the trap early.
- **Trap**: getting close while grounded and not invulnerable locks the coworker into a 2.4s "trapping" state — she blocks/nudges the player back toward her (`player.x = e.x + side*34`), delivers looping excuse-chatter lines, while the player fires back "excuse" dialogue. No stun/catch results — purely a time-waster, matching the GDD's "wastes time, no direct danger" design.
- Coworkers also drift toward any actively brewing coffee machine within 700px for "gossip" (a small flavor behavior not in the original GDD but consistent with its tone).

### Meeting rooms (dynamic occupancy)
Meeting rooms toggle between empty/booked on a per-room timer (`r.nextSwitch`, `r.booked`) — hiding in an *empty* room is safe; a room that becomes booked while you're inside is a distinct hazard state the GDD calls out (implementation confirmed via `drawMeetingRoom`/`roomDoorAt`/`meetingRooms` array + the "booked" visual state showing people seated inside).

### Hazards
- Swinging pantry doors: can clip the player for a "headache" debuff (`triggerHeadache`) — temporary movement-speed penalty (×0.55, stacks with none) with a woozy haptic (`HAPTIC.headache`) and presumably a visual wobble/sweat-drop tell.
- Printers "jam"/spray paper on a timer (`jamPrinter`), which is also a resource opportunity (collectible files) rather than a pure hazard.

---

## 11. Level Zones (exact boundaries, matches GDD)

```js
OPEN DESKS       x: 0     – 2400   "Leave quietly. Nobody panic."
PRINTER ZONE     x: 2400  – 4800   "Paper jams are personal."
PANTRY           x: 4800  – 7000   "Caffeine counts as a strategy."
MEETING ROOMS    x: 7000  – 9400   "Every door is a calendar invite."
EXECUTIVE FLOOR  x: 9400  – 11800  "Avoid eye contact. Avoid all contact."
ELEVATOR LOBBY   x: 11800 – 12520  "4:59 PM. So close."
```

Each zone has a distinct wall color, accent color, and **floor material** with unique procedural texture rendering (`drawZoneFloors`):
- OPEN DESKS: carpet (vertical tick-mark weave pattern)
- PRINTER ZONE: linoleum (scattered speckle dots via hashed noise)
- PANTRY: tile (grid lines + lighter tile-face highlight bands)
- MEETING ROOMS: carpet (darker tone)
- EXECUTIVE FLOOR: wood (plank seams + grain streaks via hashed noise, warm highlight)
- ELEVATOR LOBBY: marble (diagonal veining lines + bright top sheen)

A parallax **procedural city skyline** is visible through office windows behind every zone, with full day-progress-driven sky-color interpolation (`skyAt`, `dayProgress`) — buildings, cranes, spires, twin towers, radio masts, water tanks/towers, billboards, rooftop gardens, window-glass reflection — all seeded and zone-varied, purely decorative but a significant chunk of the rendering code (~600 lines).

---

## 12. UI / HUD Details

- **Top-left**: syncs-caught counter, score (large), coffee/headphone countdown chips (shown only while active), file count.
- **Top-right**: settings/menu icon chip; invulnerability blink state.
- **Center-above-enemies**: awareness badges — a small pill/badge that appears above each Manager/Director showing an emoji/stage indicator once awareness crosses a threshold (with hysteresis so it doesn't flicker at the boundary), speech bubbles for Coworker dialogue.
- **Bottom**: touch controls on mobile only (left/right, duck, E, F, jump — large jump button), auto-shown via `touchUI` pointer-type detection.
- **Prompt system**: a context-sensitive interaction hint (`getPrompt`/`drawPrompt`) appears above the player's head when near an interactable (e.g. "E TO SIT", "↓ TO HIDE") — this is a UX affordance not explicitly itemized in the original GDD but implemented to make the "unique mechanics" (blending/hiding/sitting) discoverable.
- **Toast**: a "PROGRESS SAVED · <ZONE NAME>" toast fires on entering a new zone at ground level, and "BADGE SCANNED · CHECKPOINT SAVED" fires at badge-scanner decor props — both save `player.checkpoint`, giving players more checkpoint density than a single-elevator-or-bust run.

### CTA button system (Caught screen + Win/Lose results screen) — most recently polished area
Both `renderCaught()` and `renderResultCard(win)` render two side-by-side call-to-action buttons at the bottom of their respective cards. **Final, verified-correct implementation:**

**Caught screen** (`renderCaught`, ~line 6173):
```js
const padX = 18, bh = 44, gap = 10;
const bw = (cw - padX * 2 - gap) / 2;     // cw = 430 (card width)
const bx0 = cx + padX, by = cy + chh - 16 - bh;
caughtBtns = [
  { id: "restart",  x: bx0,            y: by, w: bw, h: bh },
  { id: "continue", x: bx0 + bw + gap, y: by, w: bw, h: bh },
];
ctx.textAlign = "center"; ctx.textBaseline = "middle";
ctx.fillText("↻ RESTART SHIFT", bx0 + bw / 2, by + bh / 2);
ctx.fillText("▶ CONTINUE",      bx0 + bw + gap + bw / 2, by + bh / 2);
ctx.textBaseline = "alphabetic";  // reset after — the rest of the file assumes alphabetic baseline
```

**Win/Lose results screen** (`renderResultCard`, ~line 6292):
```js
const padX = 20, bh = 44, gap = 10;
const bw = (cw - padX * 2 - gap) / 2;     // cw = 480 (card width)
const bx0 = cx + padX, by = cy + chh - 54;
resultBtns = [
  { id: "share", x: bx0,            y: by, w: bw, h: bh },
  { id: "again", x: bx0 + bw + gap, y: by, w: bw, h: bh },
];
ctx.textAlign = "center"; ctx.textBaseline = "middle";
ctx.fillText(copied ? "✓ COPIED!" : "SHARE RESULT", bx0 + bw / 2, by + bh / 2);
ctx.fillText("↻ PLAY AGAIN",                       bx0 + bw + gap + bw / 2, by + bh / 2);
ctx.textBaseline = "alphabetic";
```

**Design decisions locked in during polish:**
1. Buttons are **side-by-side** (equal-width halves filling the card width minus padding/gap), *not* stacked full-width — this was explicitly corrected after an initial misread of "expand to fill the width."
2. Text centering uses the canonical Canvas 2D two-property technique: `textAlign = "center"` (horizontal) + `textBaseline = "middle"` (vertical), with the fill position placed at the exact geometric center of each button rect (`x + w/2, y + h/2`). This is the only mathematically-correct way to center text both axes in Canvas 2D without hardcoded fudge offsets, and was visually verified via Playwright headless screenshots across all three screens (Caught, Win, Lose) — text sits dead-center with no observable X or Y bias.
3. `textBaseline` is reset to `"alphabetic"` immediately after each button block — the rest of the codebase assumes alphabetic baseline by default, so this reset prevents leaking `"middle"` baseline into unrelated text draws later in the same frame.
4. Padding was iteratively reduced (Caught: 28→18px, Result: 30→20px; gap: 14→10px / 12→10px) purely to **widen the buttons** within the existing card width, at the request of design feedback — this was a deliberate late-stage tightening pass, not a bug fix.
5. Both cards keep the same left/right ordering convention: **secondary/neutral action on the left** (Restart Shift / Share Result — both white-background, low-emphasis), **primary/forward action on the right** (Continue / Play Again — both filled with the zone-accent or purple color, white text, highest visual weight). This left=secondary / right=primary convention should be preserved in any future CTA additions.

If more CTA-button work is needed later, the pattern to follow is exactly the two code blocks above: compute `bw` from `(cw - padX*2 - gap)/2`, position two rects at `bx0` and `bx0+bw+gap`, set `textAlign=center`+`textBaseline=middle` once, draw both labels at each button's `x+w/2, y+h/2`, then reset `textBaseline` before returning.

---

## 13. Typography

| Font | Weight(s) used | Usage |
|---|---|---|
| Fredoka | 500, 600, 700 | Primary UI font everywhere: HUD (`F_UI`), body/dialogue text (`F_TEXT`), big pop/logo text (`F_FUN`), and headings at weight 700 (`F_HEADING`) |
| Orbitron | 800 | `F_STAMP` — used exclusively for the rubber-stamp "ACCEPTED" text on the Caught screen, for a mechanical/official contrast against the rounder Fredoka |
| Chunky Puffly | n/a (local() only, not embedded) | Referenced as an opt-in local font for the logo/big-pop text — falls back to Fredoka automatically via CSS if the user doesn't have it installed. Free-for-personal-use font, hence not bundled as base64 like Fredoka/Orbitron. |

**Letter-spacing / kerning decisions (explicitly tuned via feedback in this session):**
- Meeting-invite title (Caught screen) and the "YOU'RE OUT! / SHIFT OVER" result-card title both use Fredoka Bold (700) at `ctx.letterSpacing = "0.4px"` — this was arrived at after iterative reduction from an initial over-wide setting (Caught screen: 1.5px → 0.8px → 0.4px final; Result screen: 3px → 1.5px → 0.4px final). The brief was "breezier" spacing without reading as loose/broken kerning — 0.4px was confirmed as the final, correct value in both places. **Do not re-widen this unless explicitly asked.**
- `ctx.letterSpacing` is reset to `"0px"` immediately after each of these titles, for the same "don't leak state into later draws" reason as the textBaseline reset above.

---

## 14. Responsive Scaling Architecture

Implemented per an explicit 10-point specification (from earlier in this session) to eliminate black bars and distortion across arbitrary aspect ratios:
- Fixed internal render resolution (1104×621) is never changed.
- `fitCanvasResolution()` computes one uniform scale factor = min(viewport width / 1104, viewport height / 621) — X and Y always scale together, never independently (no stretching/squashing).
- The scaled game is centered in the viewport (`DISPLAY.offX`/`offY`).
- `paintFullBleedBackdrop()` fills any leftover gutter space (top/bottom or left/right bars that would otherwise show as black/empty) with a color-matched wash so the page background blends into the game rather than showing hard bars.
- `DISPLAY` object tracks `dpr` (devicePixelRatio), `scale`, `offX/offY`, `bw/bh` (backing-store width/height), `gutterX/gutterY`.
- Portrait phones get a dedicated rotate-prompt overlay instead of attempting to lay out the landscape-only game vertically.

---

## 15. How to Play Screens

A dedicated 3-page paginated instructional flow (`HOWTOPLAY` mode), explicitly rebuilt from scratch per a detailed design brief earlier in this session (previous versions were discarded, not iterated on):
- **Page 0**: Controls reference + crew roster cards (`drawCrewCard` — one card per enemy archetype introducing Manager/Director/Coworker with their "problem" framing).
- **Page 1**: Office-zone guide (`drawOfficeRow` — presumably one row per zone with icon/name/description).
- **Page 2**: (final page — advancing past it with →/Space/Enter starts the game via `startGame()`).
- Navigation: ← → to move between pages, Escape backs up one page (or returns to TITLE from page 0), Enter/Space also advances (and starts the game from the last page).
- Uses the shared `pixelPanel`/`howtoChrome`/`howtoHeader`/`howtoNav` chrome components for a consistent retro-panel look, distinct from the softer Canvas UI used elsewhere (this section leans into the `PX_FONT` bitmap font system, line 5171+, rather than Fredoka).

---

## 16. Known Design Deviations From the Original GDD

For transparency, a few implementation details differ slightly from (or add nuance beyond) the literal original Game Design Document text, based on actual code inspection:

1. **Shift duration**: GDD specifies "5 real-time minutes (300 seconds)... 1 second of game time ≈ 1 real second." Actual implementation uses `SHIFT_DURATION = 105` real seconds mapped onto the fictional 4:55–5:00 (300 fictional-second) window via `gameSec()` — i.e., the game compresses roughly 2.86 fictional seconds into every 1 real second. This was a deliberate pacing tune, not an oversight.
2. **Checkpoints are denser than "100px behind catch point" alone**: in addition to the catch-point checkpoint, checkpoints also save automatically on entering a new zone at ground level, and at badge-scanner decor props scattered through the level — both show a toast and play a sound.
3. **Escape Score** is an entirely additive system layered on top of the GDD's core win/lose condition — the GDD's original "Summary of Unique Mechanics" list doesn't mention scoring, but it's fully implemented as a mastery/replayability layer (§9), later extended with office loot (§20).
4. **Seeded daily levels**: not mentioned in the original GDD at all — the entire level layout, enemy placement, and pantry item-drop mix are seeded per calendar day (`mulberry32(todayKey())`), so the game plays like a daily challenge (same for all players on a given day, changes at midnight) rather than a fully-random-every-run experience. Replayability within a single day is about optimizing your route/strategy against a fixed layout, not RNG variance.
5. **Coworker "coffee gossip" drift behavior** is a small addition beyond the literal GDD text, consistent with the intended tone.
6. **Director "hunter" late-game behavior** (extended roaming route across Executive Floor + Elevator Lobby once stage ≥3) is an implementation detail that operationalizes the GDD's "Director actively hunting" 4:59–5:00 escalation bullet.
7. **Office Loot** (§20) is an entirely additive collectible system not in the original GDD — score-only, placed to pull players off the safe path into riskier/optional parts of the office.

---

## 17. Development History / Session Log (chronological, most recent last)

1. Swapped a body/heading font to **Gluten**, then further iterated to **Fredoka** (final) for UI, and **Fredoka Bold** specifically for headings, with **Orbitron** reserved for the "ACCEPTED" stamp only.
2. Implemented the full **responsive scaling architecture** (§14) per a detailed 10-point spec — uniform scale factor, centered offset, full-bleed backdrop wash, no black bars, no distortion at any aspect ratio.
3. Built the **How to Play** instructional flow from scratch (§15) per a detailed design brief, explicitly discarding any previous how-to-play version rather than iterating on it.
4. Wired the How to Play flow into `game.html` directly (single-file architecture confirmed/maintained).
5. Tuned heading letter-spacing (kerning) on Fredoka Bold headings down from an initially-too-wide setting through two rounds of feedback to a final **0.4px** value (§13).
6. **CTA button pass** (§12): fixed text centering on the Caught/Win/Lose CTA buttons, corrected to side-by-side equal-width halves, tightened padding/gap, verified via Playwright screenshots.
7. **Office Loot added** (§20): three score-only collectibles (snack/charger/powerBank), 17 fixed placements across all 6 zones, deliberately off the safe running line.
8. **Office Loot artwork redesigned** (§21): the original placeholder art (especially the power bank) didn't read clearly at gameplay scale — rebuilt all three sprites for silhouette readability, replaced the big gold halo with a restrained collectible presentation, and gave each a distinct, correctly-sized pixel-art identity.

**Current status:** No open bugs or pending visual issues are known as of this document's writing.

---

## 18. How to Run / Test This Project

- **Run it**: open `game.html` directly in any modern browser (double-click, or `file://` URL) — zero build step, zero server required, zero external network calls at runtime (fonts are embedded base64, no CDN).
- **Visual QA approach used throughout this project**: Playwright (`chromium.launch()`), navigate to `file://<path>/game.html`, wait for load, then **directly mutate the `game` global object** via `page.evaluate()` to jump straight to any screen/state (e.g. set `game.mode = 'CAUGHT'`, populate `game.invite`, `game.caughtHold = true`, or teleport `player.x/y` next to a specific pickup) rather than simulating real input through an entire run. This is dramatically faster for iterating on UI/visual polish (HUD, cards, buttons, text layout, collectible art) since it bypasses gameplay entirely. Take a `page.screenshot()` after a short `waitForTimeout` to let one render frame settle.
- For collectible/sprite-level art iteration, it's faster to prototype the pixel grid in a small standalone script (build the ASCII grid + a matching color palette, rasterize with Pillow at both a large inspection scale and the *actual* in-game scale) before touching `game.html`, then paste the finished `ITEM_ART` rows in once the silhouette reads correctly at true size next to a mocked-up player/enemy for scale reference.
- **No test framework** (Jest/Playwright Test config, etc.) is set up in this project — ad hoc Playwright scripts have been the QA method throughout.
- **No package.json / node_modules** — this is intentionally a zero-dependency static file. If Playwright is needed for QA, it's a locally-available tool in the dev environment, not a project dependency.

---

## 19. If You Are an LLM Picking This Up Cold

Read this document fully, then open `game.html` and jump straight to the line-number map in §3 for whatever you need to touch. A few orientation tips:
- The file is single-script, ~6,600+ lines, no modules — search by function name (`grep -n "^function "`) rather than trying to read it top-to-bottom; several early lines contain huge embedded base64 font data that will blow out a naive "read whole file" attempt — read in bounded line ranges instead, or grep first.
- `game` (the state object, ~line 1932) and `update(dtMs)` (~line 2012) are the two things to understand before touching gameplay logic — everything branches off `game.mode`.
- `render()` (~line 3094) is the top-level draw dispatcher, mirroring `update`'s mode branches.
- Colors/fonts/zone data/constants are all centralized near the top (§4 has the exact physics constants; `C` object has the palette; `ZONES` has zone data) — change values there rather than hunting for magic numbers scattered through draw calls.
- When making visual/UI changes, follow the established QA pattern in §18 (inject state, screenshot, verify) rather than playing through full runs.
- Preserve the reset-state-after-use convention (`ctx.textBaseline = "alphabetic"` after any `"middle"` usage, `ctx.letterSpacing = "0px"` after any nonzero value) — this codebase relies on Canvas context state being predictable between draw calls since there's no per-draw-call `save()`/`restore()` wrapper around every single text operation (only around larger composite blocks).
- When touching `ITEM_ART`/`ITEM_PAL` (collectible pixel art), remember `drawItem(kind, cx, cy, scale, dim)` reads the sprite's width/height directly off the `ITEM_ART[kind]` grid — resizing a grid changes its on-screen footprint at a given `scale` with no other code changes needed. See §20/§21 for the current sizing rationale.

---

## 20. Office Loot — score-only collectibles (added 2026-09-27)

Three pickup types that ONLY add Escape Score (no speed, no concealment, no ammo, no health, no gameplay effect whatsoever). Backup of the pre-change file: `game.before-score-collectibles.html`.

| Type (`pickups[].type`) | Points | Pop message | SCORE key |
|---|---|---|---|
| `snack` (cookie) | +500 | PRIORITIES. | `snack` |
| `charger` (USB-C brick + cable) | +750 | ABSOLUTELY NOT LEAVING THIS. | `charger` |
| `powerBank` | +1000 | CRISIS AVERTED. | `powerBank` |

**These point values, pickup copy, and placements are locked in — do not change them without being asked. The §21 art pass touched only rendering/animation, nothing here.**

- Code: `LOOT` set + `LOOT_TOTAL` (17) declared right after `SCORE`; `seedLoot()` (called from `seedLevel()`) holds every one of the 17 placements with a one-line design reason each; the loot branch is the first check inside the pickup loop in `updatePickups()`; `stats.loot` is shown as an "Office loot n / 17" row on both the Win and Lose result cards.
- Loot is not reset when caught (same as other pickups) — only on a new run (`startGame()` re-seeds the level, which re-seeds loot).
- **Placement philosophy** (never on the safe running line — collectibles pull the player into parts of the office they'd otherwise skip):
  - **Snacks** (6, easiest): desks/counters/sofas, sometimes just past a coworker.
  - **Chargers** (6, moderate): patrolled desks, printer/cabinet tops, in a manager's sightline, or requiring a small jump.
  - **Power banks** (5, most tempting/risky): over a manager's head on a high ledge (x1890, x3740), under the pantry cupboards where mugs fall (x6470), over the hover manager (x8690), atop the Director-patrolled bookshelf via the ladder (x10945).
  - Height `GY-205` sits just out of reach of a flat-ground jump, so those spots require the standing-desk→ledge route (a deliberate "oh, I can get up there" moment).
- Total if you collect all 17: 6×500 + 6×750 + 5×1000 = **12,500 points** (verified by a headless test that teleports the player onto every loot coordinate and runs the real `update()` pickup path — see §18's QA approach).
- If you add/remove a placement, update `LOOT_TOTAL` and re-run that same total-score sanity check.

---

## 21. Office Loot — art & readability redesign (2026-09-27)

The original v1 art (§20) was functionally correct but not readable enough during actual play — the power bank in particular did not read as a power bank at a glance. This was treated as a **game-art readability problem**, not an illustration-polish pass: silhouette, exaggeration, and value hierarchy over decoration. Backup of the pre-redesign file: `game.before-collectible-art-polish.html`. Nothing about point values, pickup copy, collision behavior, scoring logic, level geometry, or enemy behavior changed in this pass — verified with the same all-17-pickups score-sum test as §20 (still totals 12,500).

### What changed
**`ITEM_PAL`** gained six new colors for this family: `K`/`m` (dark chocolate + a lighter chip glint, cookie), `A`/`F` (slate-navy body + a lighter left-edge highlight, power bank), `e`/`g` (bright "charged" green LED + a dimmer cap pixel above it, power bank).

**`ITEM_ART`** — all three grids were rebuilt from scratch, larger and with deliberately different silhouettes so they're distinguishable from each other at a glance, not just from their color:
- **`snack` (cookie), 17×15px grid:** an irregular (not perfectly round) baked edge generated from a jittered-radius circle, six large chocolate-chip blobs (each a 5-pixel plus-shape, big enough to survive downscaling, each with a 1px lighter glint), warm highlight/shadow shading. Reads as "cookie," not "coin" — round and organic vs. the other two's rectangular forms. (An earlier version also carved a bite out of the edge per the brief's suggestion, but it produced small disconnected single-pixel artifacts at this resolution — cut for a cleaner silhouette; the chips alone read clearly as a cookie.)
- **`charger`, 20×16px grid:** a small rectangular brick (rounded corners, two wall-prong ticks on top, one small teal LED on its face) with a chunky 2px-thick teal staircase cable curving out and down to an oversized, clearly separate USB-C-style connector paddle. Silhouette: small brick → looping cable → connector.
- **`powerBank`, 15×23px grid:** a thick vertical rounded-rect body (visibly taller/thicker than the charger's brick, phone-proportioned but chunkier), 4 bright green status LEDs across the top face (the fastest "portable battery" read), a horizontal divider line under them, a charging-port notch at the bottom edge, and its own short teal cable + connector plugged in below. This is the most substantial silhouette of the three, on purpose (§9's value hierarchy) — vertical and blocky vs. the cookie's round shape and the charger's small-brick-plus-diagonal-cable shape.

All three were generated with a small offline Python/Pillow script (draw at a large inspection scale, then re-render at the *actual* in-game 2× scale next to a mocked player-size reference) before being pasted into `game.html`, specifically so the "does this read in a fraction of a second at gameplay size" check happened before, not after, wiring them in. That workflow is worth reusing for any future collectible/sprite work (see §18).

### `drawPickup()` presentation — the loot branch was rewritten to be a restrained "ordinary object," not RPG treasure
Previously: a large 18–21px-radius gold circular halo behind every loot item (same for all three) plus a fairly frequent white sparkle cross. This was explicitly too much per the brief ("avoid large halos, glowing rings, excessive sparkles") and didn't communicate value hierarchy (all three glowed identically).

Now, per `LOOT_ACCENT` (`{ snack: "#E0A542", charger: "#7FE0DA", powerBank: "#3FE6A0" }`) and `LOOT_RADIUS` (`{ snack: 13, charger: 12, powerBank: 15 }`), both declared right next to `LOOT`/`LOOT_TOTAL`:
- **Small, item-colored highlight**, not a uniform gold halo — alpha ~0.12–0.19, radius 12–15px (roughly the item's own footprint, not a big aura), so it reads as "this one thing is slightly different from the static desk clutter around it," not "this is glowing treasure."
- **Gentle scale "breathe"**: `1 + 0.05*sin(now/260 + p.x*0.02)` multiplies the `drawItem` scale — a very subtle pulse, not a bounce.
- **Existing float/bob** (shared with all pickups, ±3px sine) is unchanged.
- **Occasional tiny glint**: a small 1px-thick cross highlight that appears briefly (~12% of a ~2.2s cycle, sized 1.5–3.5px) near the item's upper-right — deliberately rare ("occasional," not a constant sparkle loop) and tiny.
- Value hierarchy is **not** communicated by glow intensity — it comes from the sprite sizes themselves (cookie smallest/simplest, charger a bit bigger with cable movement, power bank the largest/most detailed) plus placement risk (§20), exactly as directed.

### Pickup feedback (moment of collection)
- The sprite still disappears **immediately** on pickup (same `pickups.splice()` as before — no lingering fade).
- `spawnParticles()` on pickup now uses each item's own `LOOT_ACCENT` color (was a single uniform gold for all three before) and a slightly bigger/snappier burst (12 particles, spread 100 vs. the previous 10/90) — a quick, item-colored "pop" rather than a generic effect.
- The floating pickup message (`addScore` → `game.pops`) now uses the shared `SCORE_POP_MS` (850ms) like every other score event, inside the brief's 700–900ms window. (A short-lived earlier version of this stretched the loot message to 1200ms "to give the longer charger line more time to read" — that override was removed in this pass since it wasn't asked for and the default already fits comfortably.)
- Sound (`Sound.play("loot")`) and haptic (`HAPTIC.loot`) are unchanged from §20.

### If you touch this again
- Sprite sizing is driven entirely by the `ITEM_ART[kind]` grid dimensions × the `scale` passed to `drawItem` in `drawPickup`'s loot branch (currently `2 * breathe` for all three) — resize the *grid*, not just the scale multiplier, if you want a genuinely different footprint, since a non-integer scale on a small grid can look slightly uneven at this pixel density.
- Keep the "small highlight, not a halo" rule if you add a fourth loot type: alpha under ~0.2, radius close to the sprite's own half-size, one accent color per item.
- Re-run the all-17-pickup score-sum sanity check (§20) after any placement or `ITEM_ART` dimension change, since a resized/repositioned sprite's collision box (`{x: p.x-14, y: p.y-14, w:28, h:28}`, unchanged, centered on `p.x/p.y`) doesn't automatically move with a visual-only resize.

---

## 22. Office Loot v3 — smooth vector art, purple glow, carpet fix, wider CTAs (2026-09-27)

Follow-up to §21 based on direct feedback: the §21 art was still a small pixel-art bitmap grid (`ITEM_ART`/`itemSprite`, upscaled 2×), which reads as pixelated/jagged on the cookie's round edge in particular — not in keeping with the rest of the world's flat, smooth art (desks, sofas, cabinets, etc. are all drawn with plain `ctx` primitives at native resolution, never a low-res grid). Also flagged: the "carpet" floor was actually a checkerboard of square tiles with grout seams, so it read as tile, not fabric. Backup of the pre-change file: `game.before-vector-polish.html`.

**Point values, pickup copy, placements (all 17 coordinates), collision box, and scoring logic are still untouched** — re-verified with the same all-17-pickup score-sum test as §20/§21 (still totals 12,500).

### Collectibles rebuilt as smooth vector art (no pixel grid)
`ITEM_ART.snack` / `.charger` / `.powerBank` and their `ITEM_PAL` entries were removed entirely. In their place, three dedicated draw functions live right after `drawPickup()`:
- **`drawLootCookie(sx, y, scale)`** — a circle filled with a radial gradient (warm tan center → darker brown edge) for a baked, domed look, a soft rim stroke, and six chocolate-chip circles at fixed unit-circle positions (each with a tiny highlight dot). Fully round, smooth arcs — no jagged edge at any scale.
- **`drawLootCharger(sx, y, scale)`** — a rounded-rect brick (`roundRect2`, a plain fill-only rounded rect helper added alongside these) with two small wall-prong ticks, a teal LED, a bottom bevel shade, and a smooth **bezier-curve cable** (`ctx.bezierCurveTo`, not the old pixel staircase) ending in a rounded-rect connector paddle with a small pin detail.
- **`drawLootPowerBank(sx, y, scale)`** — a taller rounded-rect body with a top-to-bottom linear gradient for volume, a left highlight / right shade streak (clipped to the rounded body), 4 glowing green status LEDs with a soft halo behind each, a divider line, a charging-port notch, and the same bezier-cable-plus-connector as the charger, just shorter.

All three take a `scale` multiplier (~1, gently breathing) and are centered on `(sx, y)` exactly like the old `drawItem` calls were, so `drawPickup`'s call sites needed only their body swapped, not their positioning math.

### Purple glow sphere (replaces the old per-item accent highlight)
`LOOT_GLOW = { snack: 21, charger: 23, powerBank: 27 }` (radius in px, still scales up with value — the power bank keeps the largest glow) and `LOOT_GLOW_COLOR = "179,151,255"` (soft violet) are declared next to `LOOT`/`LOOT_TOTAL`. `drawPickup`'s loot branch now paints a `ctx.createRadialGradient` sphere (bright violet core fading to transparent) behind every loot item before drawing the item itself — an actual small sphere of purple light, per explicit direction, rather than the more restrained item-colored highlight from §21. It still has a slow pulse (alpha breathes) and the item itself still does a gentle scale breathe; the occasional tiny glint is unchanged. The pickup-moment particle burst (`spawnParticles`) is now a uniform violet (`#B197FF`) instead of a per-item accent, to match.

### Carpet floor: real fabric texture instead of tile
`drawZoneFloors()`'s `"carpet"` branch (used by OPEN DESKS, MEETING ROOMS, ELEVATOR LOBBY) no longer draws a light/dark checkerboard with grout-seam strokes. A new `getCarpetPattern(f1, f2)` helper (declared just above `drawZoneFloors`) renders a small 28×28 seamless tile once per zone's color pair to an offscreen canvas — dense fine flecking in 3 close tones (~140 sub-pixel dots via a seeded `mulberry32` RNG, not `Math.random`, so it's stable across re-renders) plus a very faint two-direction diagonal hatch for a woven/nap feel — and caches it (`carpetPatternCache`, keyed by the two color strings). `drawZoneFloors` turns that into a `ctx.createPattern(tile, "repeat")`, anchors it to world space with `pattern.setTransform(new DOMMatrix().translate(-camX, 0))` (so it doesn't swim as the camera scrolls, same requirement the old tile grid was solving), and fills the zone's floor rect with it in one `fillRect` call — cheaper per frame than the old per-cell loop, and reads as short-pile carpet rather than floor tile.

### CTA buttons widened
Per explicit request ("increase the width... slightly"), both button pairs got a bit wider (both stay centered via the existing `bx0 = W/2 - bw - gap/2` math, so no other layout code changed):
- **Caught screen** (`renderCaught`, `caughtBtns`): `bw` 172→188, `gap` 14→12 (`bh` unchanged at 42).
- **Win/Lose results screen** (`renderResultCard`, `resultBtns`): `bw` 176→192, `gap` 12→10 (`bh` unchanged at 40).

Both still sit comfortably inside their card widths (`cw` 430 / 480) with room to spare — verified visually via the existing inject-state-and-screenshot QA pattern (§18).

### If you touch this again
- The loot sprites are now ordinary drawing code, not a resizable bitmap grid — resize by changing the literal pixel constants inside `drawLootCookie`/`drawLootCharger`/`drawLootPowerBank` (they're all expressed as `N * scale`), not by touching a grid.
- `roundRect2` is a deliberately separate, minimal helper from the existing `roundRect()` (which always expects a fill-or-shadow argument and is tuned for UI cards) — reuse `roundRect2` for any future flat-fill rounded shape in world-space art.
- If you add a fourth loot type, give it its own `LOOT_GLOW` radius (keep the value-hierarchy ordering) and reuse `LOOT_GLOW_COLOR` — don't reintroduce a per-item accent color for the glow itself unless asked; that was tried in §21 and explicitly replaced with the uniform purple in this pass.
- If another zone ever wants the "carpet" floor style, it just needs a `floor: "carpet"` entry with its own `f1`/`f2` — `getCarpetPattern` caches per color pair automatically.

## 23. Cupcake collectible, cable-free charger/power bank, fine glow outline, wider everyday-pickup art, wider CTAs again (2026-09-27)

Direct follow-up feedback on §22's vector art pass. Snapshot taken first: `game.before-cupcake-nocable.html`.

### Cookie → cupcake
`drawLootCookie` was replaced outright with `drawLootCupcake` (same call site in `drawPickup`, `p.type === "snack"`). Built from the same primitives as the rest of the loot art: a trapezoid paper liner (linear gradient + pleat lines), a cake dome peeking above the rim, three stacked radial-gradient dollops for the frosting swirl, and a small cherry with a highlight dot. `LOOT_GLOW.snack` (radius) was left untouched — only the sprite changed.

### Charger & power bank: cable removed
Both `drawLootCharger` and `drawLootPowerBank` had their dangling cable + connector-plug artwork deleted entirely (the bezier cable stroke in `C.teal`, the `roundRect2` plug body, and its two metal pins). What's left is just the device itself — brick + prongs + LED for the charger, body + 4 status LEDs + bottom port for the power bank. Nothing else in either function changed; the body drawing, gradients and highlight streaks are exactly as in §22.

### Fine outline on the purple glow sphere
In `drawPickup`'s loot branch, right after the radial-gradient fill, a thin stroked circle was added at the same radius:
```js
ctx.strokeStyle = `rgba(${LOOT_GLOW_COLOR},${(0.38 + 0.12 * pulse).toFixed(3)})`;
ctx.lineWidth = 0.6;
ctx.beginPath(); ctx.arc(sx, y, r, 0, Math.PI * 2); ctx.stroke();
```
0.6px width so it reads as a crisp edge to the "bubble," not a bold ring — pulses gently in sync with the existing glow pulse.

### Everyday pickups (file, coffee, headphones) rebuilt as vector art
These were plain flat `fillRect` shapes before; they're now three dedicated functions (`drawWorldFile`, `drawWorldCoffee`, `drawWorldPhones`, defined right after `roundRect2`, before the character-sprites section) using the same flat-shaded-plus-gradient language as the loot art and furniture:
- **File**: rounded-rect paper with a faint offset second sheet behind for depth, a linear-gradient body, a teal header band clipped to the rounded corners, and three text-line bars.
- **Coffee**: trapezoid cup (tapered, gradient-shaded) with a dark lid-rim ellipse, a tan sleeve band, and three bezier steam curls that rise and fade (replacing the old blocky rectangle "steam").
- **Headphones**: arc band + two gradient rounded ear cups with highlight strokes.
These are *not* wrapped in the purple `LOOT_GLOW` sphere — that treatment stays specific to the three score-only loot items. They keep their existing ambient teal glow-pulse ring (unchanged, drawn after the `if/else if` block in `drawPickup`).

### CTA buttons widened again
Per direct feedback that they should be wider still while staying side-by-side:
- Caught screen (`renderCaught`): `bw` 188→198, `gap` 12→10 (was 172/14 originally in §21, then 188/12 in §22).
- Result screen (`renderResultCard`): `bw` 192→202, `gap` 10→9.
Centering formula (`bx0 = Math.round(W / 2 - bw - gap / 2)`) unchanged. Verified via screenshot that both button pairs still sit comfortably inside their card widths (430px and 480px respectively) with even margins.

### Verification
- `node -e` syntax check of all `<script>` blocks: clean.
- Teleport-and-`update()` sweep over all 17 loot coordinates (sequential per-item `page.evaluate` calls, not batched — batching caused a stale-position race in-test, not a real game bug): score still lands on exactly **12,500**, all 17 collected, no console/page errors.
- Visual QA via Playwright screenshots + crops for the cupcake, cable-free charger, cable-free power bank, file, coffee, headphones, and both CAUGHT/WIN modals.

### If you touch this again
- The cupcake, like the other loot sprites, is plain drawing code (`N * scale` literals) — resize by editing those constants, not a grid.
- Don't re-add a cable/connector to the charger or power bank sprites unless explicitly asked back — it was deliberately removed twice now (first shortened in concept, then deleted outright).
- The fine glow-sphere outline lives inside `drawPickup`'s loot branch, not inside the individual `drawLoot*` functions — if you change the glow radius/color, the outline follows automatically since it reuses `r` and `LOOT_GLOW_COLOR`.
- `drawWorldFile`/`drawWorldCoffee`/`drawWorldPhones` are separate from the HUD chip icons `drawCoffeeIcon`/`drawHeadphonesIcon` (used in the top-bar UI) — don't conflate the two; the world-pickup versions are scaled and shaded for in-level readability, the HUD ones are flat and small.

## 24. Charger recenter, samosa, rotating pickup copy, 2-CTA pause menu, HUD icons matched to runway art, manager chatter (2026-09-27)

Direct follow-up feedback on §23. Snapshot taken first: `game.before-samosa-pause-hud.html` (this captures the state right after §23's cupcake/cable-removal changes, before this batch).

### Charger centered in its glow sphere
`drawLootCharger`'s bounding box (brick + prongs) wasn't actually centered on `(sx, y)` — the prongs extend 3.5×scale above the brick top, which was never accounted for, so the sprite sat visibly high-left inside the purple sphere. Fixed by recomputing the origin from the full bounding box (brick + prongs) rather than the brick alone:
```js
// bounding box (brick + prongs) centered on (sx, y) — prongs add 3.5*scale above the brick top
const ox = sx - 8.5 * scale, oy = y - 5.25 * scale, bw = 17 * scale, bh = 14 * scale, r = 3 * scale;
```
(was `ox = sx - 13*scale, oy = y - 12*scale`). Nothing else in the function changed. The power bank didn't have this problem (its body's bounding box was already symmetric on `(sx,y)`), so it was left alone.

### Cupcake → samosa
`drawLootCupcake` was replaced with `drawLootSamosa` (same call site in `drawPickup`, `p.type === "snack"`): a rounded triangle (gently convex sides via `quadraticCurveTo`, apex up) with a linear gradient for pastry-shell shading, a few crimped-seam tick marks along the right fold, a highlight streak, and small darker "fried" speckles. `LOOT_GLOW.snack` untouched.

### Everyday pickups (file/coffee/headphones) now also drive the HUD
The HUD's top-right chips (files/coffee/phones power-up chips) were still using the *old* pixel-grid `ITEM_ART`/`itemSprite()`/`drawItem()` system, so they visually mismatched the new vector runway art from §23. Added `drawHudPickupIcon(kind, cx, cy, scale, dim)` (right after `drawWorldPhones`) which calls the same `drawWorldFile`/`drawWorldCoffee`/`drawWorldPhones` functions used on the ground, and uses `ctx.filter = "grayscale(1) opacity(0.5)"` for the washed-out "not active" chip state instead of a separate desaturated bitmap. `renderHUD()`'s power-chip helper and the files chip now call this instead of `drawItem(...)`; the old per-chip `drawSteam(...)` call for coffee was removed since `drawWorldCoffee` already animates its own steam curls. `drawItem()`/`ITEM_ART` are untouched and still used for the sound/music/haptics settings-menu glyphs — only the file/coffee/phones HUD chips were switched over.

### Rotating pickup copy for the loot pop text
New `LOOT_COPY` map + `LOOT_COPY_IDX` counters (declared next to `LOOT_GLOW`) cycle each loot type's pickup message **in order** (not random) so repeat pickups of the same type don't always show the same line:
```js
snack:     ["PRIORITIES!", "WORK HARD, SNACK HARDER!", "MORALE BOOSTED!"],
charger:   ["MY PRECIOUSSS.", "ABSOLUTELY NOT LEAVING THIS."],
powerBank: ["NO CAP, I'M INVINCIBLE.", "CRISIS AVERTED.", "VICTORY IS MINE."],
```
`addScore()` now looks up `LOOT_COPY[key]` first and falls back to `SCORE[key].label` for everything else (dodges, stuns, zone bonuses, etc., which are untouched). The three counters reset to 0 in `startGame()` so every run starts each type's cycle from its first line. Point values (`SCORE.snack/charger/powerBank.pts` = 500/750/1000) were **not** touched — verified via the same teleport-and-`update()` sweep as previous rounds: total from all 17 loot items alone is still exactly 12,500 (a separate, pre-existing "NEW ZONE! +250" checkpoint bonus can stack on top of that in an artificial test that teleports across the whole level in one pass — that bonus is unrelated to loot and was already in the game before this session).

### Pause menu: two CTAs instead of three, Resume made primary-green and moved to the bottom row
Per direct feedback, the in-game PAUSED screen (`menu.from === "PLAY"`) no longer has a standalone full-width teal "Resume" button up top, and no longer has "Quit to Title" at all. `menuItems()` now returns, for `PLAY`: `[...toggles, {id:"restart"}, {id:"resume"}]` — Resume is now the **right-hand, primary green** button in the same bottom row as Start Over (left, white/outline, unchanged style), replacing where Quit to Title used to sit. The **title-screen** Settings modal (`menu.from === "TITLE"`) is untouched: it still shows the single full-width "◀ BACK" primary button up top and no bottom row, because it never included restart/quit items to begin with.
`renderMenu()` was restructured so the "top big primary button" rendering path is now keyed off `menu.from === "TITLE"` specifically (via a `topResumeIdx` lookup) rather than off `it.id === "resume"` positionally — that positional assumption broke once Resume moved to the end of the PLAY items array. The settings-toggle panel box is now drawn once, unconditionally, right before the toggle loop (previously it was only drawn as a side-effect of the top-button branch). The bottom-row branch now checks `it.id === "resume"` to pick the primary-green style (`C.teal` fill, white text, "▶ RESUME") versus the existing white/outline "↻ START OVER" style. Keyboard nav (`updateMenu`) needed no changes — it already just used `menuItems().length`, not fixed indices. `menuSelect()`'s dead `if (it.id === "quit")` branch was left in place (harmless, unreachable now) rather than removed, to minimize the diff.

### Manager ambient one-liners (new)
Per the design doc's original intent ("managers... speak occasional dialogue") the manager never actually had ambient patrol chatter — only the CAUGHT-screen invite agendas had jokes. Added a `mgrChatter` pool to `CHATTER` (14 classic-manager lines: "Let's circle back on that.", "Per my last email…", "Low-hanging fruit, people!", etc.) and wired it into `updateEnemy()`'s plain-patrol branch (the `else` at the bottom, which only plain back-and-forth managers/directors reach — hover-variant and phone-walker managers already have their own chatter elsewhere):
- ~50% chance to say a line whenever the manager reaches a route end and transitions into `"pause"`.
- A small per-frame chance (`Math.random() < 0.0015`, gated so it never interrupts an existing bubble) to say a line mid-walk too, so it's not only at the endpoints.
Directors are explicitly excluded (`!isDir`) — they stay dry/silent on patrol, consistent with the existing "Director = short, dry, quietly terrifying, no jokes" comment already in the code above the CAUGHT invites.

### Verification
- Syntax check of all `<script>` blocks: clean.
- Teleport-and-`update()` sweep over all 17 loot coordinates, reading each pickup's actual pop label: confirmed exactly 500/750/1000 per type every time, loot-only total 12,500, and each type's copy rotates through its full list in order with no repeats until the list wraps.
- `updateEnemy()` sanity test: forced a manager through 60 route-end pause transitions with the clock manually advanced past the say() cooldown each time — saw 12 of the 14 `mgrChatter` lines appear, no errors, directors never triggered it.
- Visual QA via Playwright screenshots + crops: samosa, recentered charger (now visibly centered in its sphere), HUD chips in both active (full-color, matches runway art) and inactive (grayscale) states, the new 2-button PAUSED modal, the untouched title-screen Settings modal, and a manager's speech bubble showing a `mgrChatter` line in-scene.

### If you touch this again
- If you add a fourth `LOOT` type, give it an entry in `LOOT_COPY` too (or it'll silently fall back to whatever single `SCORE[key].label` you set — not wrong, just not rotating).
- `drawHudPickupIcon`'s `dim` parameter uses a canvas `filter` string, not a separate palette — if you need the dim look somewhere `ctx.filter` isn't supported (it's fine in all real browsers/Electron/Chromium here), you'd need to fall back to the old pixel-desaturation approach in `itemSprite()`.
- The pause-menu rendering now branches on `menu.from === "TITLE"` for the top-button case — if you ever want a *third* CTA in the in-game PAUSED row, you can't just add a third item to the bottom-row array as-is; the row layout math (`bw = (inW - 12) / 2`, `idxInRow = it.id === "restart" ? 0 : 1`) assumes exactly two.
- `mgrChatter` only fires from the plain-patrol `else` branch in `updateEnemy` — a manager with `variant === "hover"` or `variant === "phone"` won't say these lines (they have their own `hover`/`phoneLook`/`phoneTap` pools instead); that's intentional, not an oversight.

## 25. Samosa → strawberry-cream donut (2026-09-28)

Snapshot taken first: `game.before-donut.html`.

`drawLootSamosa` was replaced with `drawLootDonut` (same call site in `drawPickup`, `p.type === "snack"`): a true ring donut built from two-circle compound paths filled with `ctx.fill("evenodd")` (outer dough circle + inner hole circle — evenodd leaves the doubly-covered center transparent, so whatever's behind the donut shows through the hole, no fake background-color patch needed). Layers: a gradient dough ring, an inset pink strawberry-glaze ring (leaving a thin dough rim visible at both edges), a glossy highlight arc, a few white quadratic-curve "drizzle" strokes around the glaze, and small rotated rectangle sprinkles in four colors scattered around the ring. `LOOT_GLOW.snack` and `LOOT_COPY.snack` (the rotating "PRIORITIES!" / "WORK HARD, SNACK HARDER!" / "MORALE BOOSTED!" pickup copy from §24) were both left untouched — only the sprite changed.

### Verification
- Syntax check: clean.
- Score sweep: all 17 loot items still collect for the correct per-type values (500/750/1000, loot-only total 12,500).
- Visual QA screenshot confirms the donut reads clearly with a see-through hole, pink glaze, drizzle and sprinkles, still centered in the purple glow sphere.

### If you touch this again
- The evenodd double-circle trick (`ctx.arc` twice into one path, then `ctx.fill("evenodd")`) is the way to punch a true hole through to whatever's behind a shape in this codebase — reuse it rather than painting a background-colored patch, which would look wrong against the purple glow/scrolling scene behind it.

## 26. Loot moved into enemy territory (2026-09-28)

Snapshot taken first: `game.before-loot-placement.html`.

**Why:** feedback was that the donut/charger/power bank never sat anywhere genuinely dangerous. Two root causes, both confirmed in code:
1. `enemySeesPlayer()` rejects anything more than 110px above the enemy (`Math.abs(dy) > 110`). All five power banks and one charger were on 150–205px ledges/shelves/bookshelf tops, so while grabbing them the player was invisible to every manager. The "risky" high road was actually the safest place in the level.
2. Several items sat in the gaps *between* patrols (first desk x590, the "quiet desk" x8090, the hideable lobby sofa), and the back half of the Printer Zone (x4000–4800, manager #5's whole route) had no loot at all.

**What changed (`seedLoot()` only; point values, `LOOT_COPY`, counts and `LOOT_TOTAL = 17` unchanged — still 6 donuts / 6 chargers / 5 power banks):**
- Every item sits near the *centre* of an enemy's patrol route. Route centres stay inside the route for any daily ±90 jitter (`seedEnemies` `j(90)`), so this holds every day.
- Every support surface is ≤ 90px (desk/stool 48, sofa 40, counter 60, cabinet 72, printer 84, standing desk 90, or the floor), so the patrolling enemy can always see you at grab height. All are reachable with the normal jump (apex ≈ 135px).
- Value follows danger: donuts guard a single patrol; chargers add a second pressure (coworker, the booked meeting room you can't hide in, pantry mug drops, the Director); power banks sit at hover-manager posts (they plant at route centre and turn on a beat — red light/green light), on manager #5's printer, on the Director's beat, and on the cabinet next to the lift (camped coworker + 2nd Director at 4:58:30 + hover wave at 4:58:55).
- Phone-walker lanes (x3700, x6470, x9710, x9885) are intentionally "grab between glances": head-down vision is 80px, full 200px when they look up.

| Item | x | Surface | Who's watching |
|---|---|---|---|
| donut | 1370 | desk | manager #1 |
| charger | 1785 | standing desk | manager #2 (4:55:20) |
| charger | 2872 | floor under the ledge | manager #3 |
| donut | 3700 | desk | phone manager |
| power bank | 4290 | printer | manager #5 (4:55:40) |
| donut | 5480 | sofa | hover manager |
| power bank | 5700 | counter at hover post | hover manager |
| charger | 6470 | counter under mug cupboards | phone manager + mugs |
| charger | 7720 | jump-grab by booked room | manager #8 + coworker |
| power bank | 8660 | desk at hover post | hover manager |
| donut | 9710 | sofa | phone manager + Director |
| charger | 9885 | standing desk | phone manager + Director |
| donut | 10205 | standing desk | Director (300px sight) |
| power bank | 10525 | standing desk | manager #11 + Director |
| charger | 11367 | stool at hover post | hover manager + Director |
| donut | 11950 | lobby counter | lobby manager + 4:57:20 wave + Director |
| power bank | 12284 | cabinet by the lift | coworker + 2nd Director + hover wave |

**Verification (Playwright, real game code):** each item collected from its own surface (or with one jump for x7720) with enemies parked; each item lies inside ≥1 patrol route; for each, a route-owning enemy placed 120px away and facing the player returns `enemySeesPlayer() === true` at grab height (phone-walkers tested with their glance-up active). Score sweep: loot-only total still 12,500, no page errors.

### If you touch this again
- Before placing loot above ~110px, remember managers literally cannot see up there — it will be a safe spot, not a risky one. Directors share the same 110px limit.
- To keep an item "in territory" across daily jitter, place it within ±(half route length − 90) of the route centre.
