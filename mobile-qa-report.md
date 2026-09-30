# Out By Five — Mobile QA: test matrix, results, bugs

**Build tested:** `main` @ d28be75 (game.html) · **Date:** 2026-09-30 · **Method:** automated, Chromium with touch emulation (Playwright + CDP touch events), 2× DPR, landscape.

## Result

**305 checks · 302 pass · 0 fail · 3 indicative (frame rate, see below).** Four product bugs found and fixed during the run; the final matrix below is the passing regression run.

## Devices (landscape)

| Short | Viewport | Aspect | Why it's in the matrix |
|---|---|---|---|
| SE | 667×375 | 1.78 | smallest common iPhone, tightest HUD/controls budget |
| 13 | 844×390 | 2.16 | mainstream iPhone (deep suite) |
| ProMax | 932×430 | 2.17 | largest phone |
| Andr | 740×360 | 2.06 | short Android viewport (deep suite) |
| Pixel | 915×412 | 2.22 | common Android |
| UWide | 960×412 | 2.33 | extreme aspect, most vertical crop |
| iPad | 1024×768 | 1.33 | tablet, horizontal crop instead of vertical (deep suite) |
| iPadPro | 1366×1024 | 1.33 | big tablet, buffer-size cap |

"Deep suite" = controls, orientation and robustness checks (D, E, F, G rows) also run; the other devices run layout, HUD, state and title checks.

## Areas covered

- **A Layout** — cover fill, uniform scale, camera zoom, floor visible, controls inside viewport, 44 px targets, no overlaps, no scroll.
- **B HUD** — on-screen margins, worst-case load (3 chips + 8-digit score) stays separated.
- **C States** — frame stability across play → caught → continue / restart → pause → resume / start over → exit → win → lose → title; overlay hit-testing; hit targets.
- **D Controls** — every button, movement, jump, duck, ladder climb, multi-touch, glide, touchcancel, held-while-caught, tap spam.
- **E Orientation** — portrait prompt, clock stops behind it, landscape restore, resize while a modal is open.
- **F Robustness** — background/blur auto-pause, frame rate.
- **G Safe-area** — notch/home-indicator insets (L/R 47 px, bottom 21 px) via Chromium's inset emulation.
- **H Title** — Settings pill, Back, How to Play pill, hit targets.

## Matrix (✅ pass · ⚠️ indicative only · · not run on that device)

| ID | Area | Check | SE | 13 | ProMax | Andr | Pixel | UWide | iPad | iPadPro |
|---|---|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| A1 | Layout | Title uses letterboxed full frame (contain), whole frame visible | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| A2 | Layout | No page scroll / overflow | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| A3 | Layout | Play: canvas covers whole viewport (no gaps) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| A4 | Layout | Play: uniform scale (css 16:9, buffer ratio uniform) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| A5 | Layout | Mobile zoom camera active (1.3) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| A6 | Layout | Floor/feet visible (ground line inside viewport, >=12% above bottom) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| A7 | Layout | All 7 controls fully inside viewport | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| A8 | Layout | Every control >= 44px touch target | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| A9 | Layout | Controls do not overlap each other | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| B1 | HUD | HUD fully on-screen with >=8px margin | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| B2 | HUD | Worst-case HUD (3 chips + 8-digit score): left / clock / right clusters stay separate | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| C1 | States | Caught: frame identical to pre-catch (layout/rect/buffer/zoom) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| C2 | States | Caught: controls hidden, no keys stuck | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| C3 | States | Continue returns to PLAY on the same frame, controls back | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| C4 | States | Caught > Restart shift: back in PLAY, same frame | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| C5 | States | Tap HUD menu chip pauses; frame identical; overlay drawn | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| C6 | States | Pause menu: tapping Sound row toggles setting (hit-test aligned with overlay) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| C7 | States | Resume returns to PLAY on same frame, controls back | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| C8 | States | Tap outside pause card closes it | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| C9 | States | Pause card: hit targets don't overlap; Resume/Start over are the only bottom buttons | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| C10 | States | Pause > Start over restarts the shift (player back at start, PLAY, same frame) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| C11 | States | Elevator exit (EXIT): frame identical to gameplay | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| C12 | States | Win card: frame identical to gameplay | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| C13 | States | Win card: 'Play again' tap restarts (hit-test aligned) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| C14 | States | Lose card: frame identical to gameplay | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| C15 | States | Back at title: letterboxed frame, controls & HUD layer hidden | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| D1 | Controls | Each of 7 buttons presses its key, shows held state, releases cleanly | · | ✅ | · | ✅ | · | · | ✅ | · |
| D2 | Controls | Right moves +x, Left moves -x | · | ✅ | · | ✅ | · | · | ✅ | · |
| D3 | Controls | JUMP lifts the player (>=60 units) and lands | · | ✅ | · | ✅ | · | · | ✅ | · |
| D4 | Controls | DOWN ducks the player | · | ✅ | · | ✅ | · | · | ✅ | · |
| D5 | Controls | UP button climbs the executive-floor ladder | · | ✅ | · | ✅ | · | · | ✅ | · |
| D6 | Controls | Multi-touch: Right + Jump held together | · | ✅ | · | ✅ | · | · | ✅ | · |
| D7 | Controls | Glide between buttons hands the key over; sliding off releases | · | ✅ | · | ✅ | · | · | ✅ | · |
| D8 | Controls | touchcancel releases the key (no stuck run) | · | ✅ | · | ✅ | · | · | ✅ | · |
| D9 | Controls | Holding a button while caught leaves no stuck key | · | ✅ | · | ✅ | · | · | ✅ | · |
| D10 | Controls | Tap on empty world during play does nothing (no pause/crash) | · | ✅ | · | ✅ | · | · | ✅ | · |
| D11 | Controls | 40 rapid Jump taps leave no stuck key | · | ✅ | · | ✅ | · | · | ✅ | · |
| E1 | Orientation | Portrait: rotate prompt shown, game + controls hidden | · | ✅ | · | ✅ | · | · | ✅ | · |
| E2 | Orientation | Portrait: game clock does not run behind the prompt | · | ✅ | · | ✅ | · | · | ✅ | · |
| E3 | Orientation | Back to landscape: cover layout restored, controls visible | · | ✅ | · | ✅ | · | · | ✅ | · |
| E4 | Orientation | Resize while caught: Continue still tappable | · | ✅ | · | ✅ | · | · | ✅ | · |
| F1 | Robust | App backgrounded (blur) auto-pauses on same frame with overlay | · | ✅ | · | ✅ | · | · | ✅ | · |
| F2 | Robust | Frame rate in cover mode | · | ⚠️ | · | ⚠️ | · | · | ⚠️ | · |
| G1 | Safe-area | Controls stay inside emulated notch insets (L/R 47, bottom 21) | · | ✅ | · | ✅ | · | · | ✅ | · |
| G2 | Safe-area | HUD origin/width respect the insets | · | ✅ | · | ✅ | · | · | ✅ | · |
| H1 | Title | Title: SETTINGS pill opens the settings card | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| H2 | Title | Settings card: no overlapping hit targets, no phantom items, every item inside the card | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| H3 | Title | Settings > Back closes the card | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| H4 | Title | HOW TO PLAY pill opens the card; a tap closes it and stays on title | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| R0 | Robust | No JS errors / console errors during whole run | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

## Bugs found and fixed

| # | Severity | Bug | Root cause | Fix |
|---|---|---|---|---|
| 1 | **High** (pre-existing, touch + desktop mouse) | Tapping/clicking **Resume** in the pause menu opened an invisible How-to card and left the game stuck in PAUSED. | A "How to play" item in the menu list had no button of its own and was drawn in the bottom row at exactly Resume's position; hit-test returned it first. Same item drew a stray "↻ START OVER" button hanging off the title Settings card. | Removed the phantom item from both menus (title has its own How to Play pill). |
| 2 | Medium (regression from the cover layout) | Elevator exit, Win card and Lose card switched back to the small letterboxed frame — the same visual jump as caught/pause. | Cover layout only covered PLAY / CAUGHT / PAUSED. | EXIT / WIN / LOSE stay in the cover frame; their dim and cards draw on the viewport layer. |
| 3 | Low | Console error: blocked `navigator.vibrate` before the first tap. | Game haptics fired before browser user-activation. | Guard on `navigator.userActivation`. |
| 4 | Low (performance) | Tablet canvas buffer 4.2 MP in cover mode. | Pixel cap too high for big screens. | Cap lowered 4.4 MP → 2.6 MP (phones unchanged at ~1.6 MP). |

Found earlier in the session by the same approach: pause chip tap target was offset (fixed), and the caught/pause frame jump (fixed).

## Not verified / residual risk

- **Frame rate (F2, ⚠️):** headless software rendering gives 7–15 fps here, and the *pre-cover* build measured ~17 fps on the same machine (cover is ~18% slower there, from ~55% more pixels). Not a real-GPU number — profile on a device.
- **Real iOS Safari / Android Chrome:** not run. Address-bar collapse, `100dvh` behaviour, real notch insets and real multi-touch hardware need a device pass. Safe-area handling was validated only through Chromium's emulation.
- **Audio, haptics feel, and the gyroscope rotate gesture** are not covered by automation.
- **iPad-width crop** (horizontal) was checked for controls/HUD/camera but not for every enemy interaction near the cropped strips.

## Re-running

`python3 qa.py results.json` (all devices, ~10 min) or `QA_ONLY="iPhone 13,iPad 1024" python3 qa.py out.json`. Requires Playwright + Chromium; opens `/home/claude/work/game.html`.
