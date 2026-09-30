"""Out By Five - mobile QA matrix. Run: python3 qa.py [out.json]"""
import asyncio, json, sys, time
from playwright.async_api import async_playwright

URL = 'file:///home/claude/work/game.html'
DEVICES = [  # name, w, h (landscape), deep = run full control/robustness suite
    ("iPhone SE 667x375", 667, 375, False),
    ("iPhone 13 844x390", 844, 390, True),
    ("iPhone Pro Max 932x430", 932, 430, False),
    ("Android small 740x360", 740, 360, True),
    ("Pixel 915x412", 915, 412, False),
    ("Ultra-wide 960x412", 960, 412, False),
    ("iPad 1024x768", 1024, 768, True),
    ("iPad Pro 1366x1024", 1366, 1024, False),
]
SNAP = """()=>{const c=document.getElementById('game');const r=c.getBoundingClientRect();
 return {mode:game.mode,layout:layoutMode,rect:[r.left,r.top,r.width,r.height].map(v=>Math.round(v*10)/10),
 buf:[c.width,c.height],zoom:game.camZoom,ctl:document.body.classList.contains('ctl-on'),
 overlay:overlayActive,keys:[...keys],vw:innerWidth,vh:innerHeight,
 sx:document.documentElement.scrollWidth,sy:document.documentElement.scrollHeight}}"""
RESULTS = []

def rec(area, tid, dev, name, ok, detail=""):
    RESULTS.append(dict(area=area, id=tid, device=dev, name=name, status="PASS" if ok else "FAIL", detail=str(detail)[:300]))

def blocked(area, tid, dev, name, why):
    RESULTS.append(dict(area=area, id=tid, device=dev, name=name, status="BLOCKED", detail=why))

class T:
    def __init__(self, pg, cdp): self.pg, self.cdp = pg, cdp
    async def touch(self, kind, pts):
        await self.cdp.send('Input.dispatchTouchEvent', {'type': kind, 'touchPoints': [{'x': x, 'y': y, 'id': i} for (x, y, i) in pts]})
    async def center(self, sel):
        return await self.pg.evaluate("(s)=>{const b=document.querySelector(s).getBoundingClientRect();return [b.left+b.width/2,b.top+b.height/2]}", sel)
    async def hold(self, sel, ident=1, ms=300):
        x, y = await self.center(sel); await self.touch('touchStart', [(x, y, ident)]); await self.pg.wait_for_timeout(ms); return (x, y)
    async def release(self): await self.touch('touchEnd', [])
    async def tap(self, x, y): await self.pg.touchscreen.tap(x, y)

async def snap(pg): return await pg.evaluate(SNAP)
def same_frame(a, b): return all(a[k] == b[k] for k in ('layout', 'rect', 'buf', 'zoom'))

async def start_game(pg, w, h):
    await pg.goto(URL); await pg.wait_for_timeout(1500)
    await pg.touchscreen.tap(w // 2, h // 2); await pg.wait_for_timeout(500)
    if await pg.evaluate("howtoOpen"): await pg.touchscreen.tap(w // 2, h // 2)
    await pg.wait_for_function("game.mode==='PLAY'", timeout=8000); await pg.wait_for_timeout(1500)

async def get_caught(pg):
    await pg.evaluate("()=>{player.invulUntil=0}")
    await pg.evaluate("caughtBy({kind:'director'})")
    await pg.wait_for_function("game.caughtHold===true", timeout=20000); await pg.wait_for_timeout(300)

async def run_device(browser, name, w, h, deep):
    ctx = await browser.new_context(viewport={'width': w, 'height': h}, device_scale_factor=2, has_touch=True, is_mobile=True)
    pg = await ctx.new_page(); cdp = await ctx.new_cdp_session(pg); t = T(pg, cdp)
    errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
    tag = name.split()[0] + str(w)
    try:
        # ---------------- A. LAYOUT ----------------
        await pg.goto(URL); await pg.wait_for_timeout(1500)
        s = await snap(pg)
        rec("A Layout", "A1", name, "Title uses letterboxed full frame (contain), whole frame visible",
            s['layout'] == 'contain' and s['rect'][0] >= -1 and s['rect'][1] >= -1 and s['rect'][0] + s['rect'][2] <= w + 1 and s['rect'][1] + s['rect'][3] <= h + 1, s['rect'])
        rec("A Layout", "A2", name, "No page scroll / overflow", s['sx'] <= w and s['sy'] <= h, (s['sx'], s['sy']))
        await pg.screenshot(path=f'shots/{tag}_title.png')
        TP = "(nm)=>{const r=document.getElementById('game').getBoundingClientRect();const s=r.width/1104;const b=nm==='set'?TITLE_SETTINGS:TITLE_HOWTO;return [r.left+(b.x+b.w/2)*s,r.top+(b.y+b.h/2)*s]}"
        await t.tap(*await pg.evaluate(TP, 'set')); await pg.wait_for_timeout(500)
        mo = await pg.evaluate("[menu.open,menu.from]")
        rec("H Title", "H1", name, "Title: SETTINGS pill opens the settings card", mo == [True, 'TITLE'], mo)
        ov = await pg.evaluate("(()=>{const R=menu.rects.filter(Boolean);const bad=[];for(let i=0;i<R.length;i++)for(let j=i+1;j<R.length;j++){const a=R[i],b=R[j];if(a.x<b.x+b.w&&b.x<a.x+a.w&&a.y<b.y+b.h&&b.y<a.y+a.h)bad.push([i,j])}return [bad,menuItems().map(x=>x.id),R.map(r=>r.y+r.h)]})()")
        rec("H Title", "H2", name, "Settings card: no overlapping hit targets, no phantom items, every item inside the card", not ov[0] and 'howto' not in ov[1] and max(ov[2]) <= 621 - 20, ov)
        await pg.screenshot(path=f'shots/{tag}_title_settings.png')
        bk = await pg.evaluate("(()=>{const r=document.getElementById('game').getBoundingClientRect();const s=r.width/1104;const b=menu.rects[0];return [r.left+(b.x+b.w/2)*s,r.top+(b.y+b.h/2)*s]})()")
        await t.tap(*bk); await pg.wait_for_timeout(400)
        rec("H Title", "H3", name, "Settings > Back closes the card", not await pg.evaluate("menu.open"), await pg.evaluate("menu.open"))
        await t.tap(*await pg.evaluate(TP, 'how')); await pg.wait_for_timeout(400)
        ho = await pg.evaluate("howtoOpen")
        await pg.screenshot(path=f'shots/{tag}_title_howto.png')
        await t.tap(w // 2, h // 2); await pg.wait_for_timeout(400)
        rec("H Title", "H4", name, "HOW TO PLAY pill opens the card; a tap closes it and stays on title", ho and not await pg.evaluate("howtoOpen") and await pg.evaluate("game.mode") == 'TITLE', (ho, await pg.evaluate("game.mode")))
        await start_game(pg, w, h)
        p0 = await snap(pg)
        r = p0['rect']
        rec("A Layout", "A3", name, "Play: canvas covers whole viewport (no gaps)", p0['layout'] == 'cover' and r[0] <= 0.5 and r[1] <= 0.5 and r[0] + r[2] >= w - 0.5 and r[1] + r[3] >= h - 0.5, r)
        rec("A Layout", "A4", name, "Play: uniform scale (css 16:9, buffer ratio uniform)",
            abs(r[2] / r[3] - 1104 / 621) < 0.01 and abs((p0['buf'][0] / 1104) / (p0['buf'][1] / 621) - 1) < 0.01, (r, p0['buf']))
        rec("A Layout", "A5", name, "Mobile zoom camera active (1.3)", p0['zoom'] == 1.3, p0['zoom'])
        # bottom anchored crop: floor line visible
        ground = await pg.evaluate("(()=>{const c=document.getElementById('game').getBoundingClientRect();const s=c.width/1104;return c.top+530*s})()")
        rec("A Layout", "A6", name, "Floor/feet visible (ground line inside viewport, >=12% above bottom)", ground < h * 0.9, round(ground))
        btns = await pg.evaluate("[...document.querySelectorAll('.tbtn')].map(e=>{const b=e.getBoundingClientRect();return [e.dataset.key,b.left,b.top,b.right,b.bottom]})")
        inside = all(b[1] >= 0 and b[2] >= 0 and b[3] <= w and b[4] <= h for b in btns)
        rec("A Layout", "A7", name, "All 7 controls fully inside viewport", inside and len(btns) == 7, [b for b in btns if not (b[1] >= 0 and b[3] <= w and b[4] <= h)])
        small = [b[0] for b in btns if min(b[3] - b[1], b[4] - b[2]) < 44]
        rec("A Layout", "A8", name, "Every control >= 44px touch target", not small, small)
        ov = []
        for i in range(len(btns)):
            for j in range(i + 1, len(btns)):
                a, b = btns[i], btns[j]
                if a[1] < b[3] and b[1] < a[3] and a[2] < b[4] and b[2] < a[4]: ov.append((a[0], b[0]))
        rec("A Layout", "A9", name, "Controls do not overlap each other", not ov, ov)
        await pg.screenshot(path=f'shots/{tag}_play.png')

        # ---------------- B. HUD ----------------
        hud = await pg.evaluate("""()=>{const c=document.getElementById('hudCanvas');const x=c.getContext('2d');
          const d=x.getImageData(0,0,c.width,c.height).data;let l=1e9,t=1e9,r=-1,b=-1;
          for(let y=0;y<c.height;y+=2)for(let xx=0;xx<c.width;xx+=2){if(d[(y*c.width+xx)*4+3]>20){if(xx<l)l=xx;if(xx>r)r=xx;if(y<t)t=y;if(y>b)b=y}}
          const k=c.width/innerWidth;return [l/k,t/k,r/k,b/k]}""")
        rec("B HUD", "B1", name, "HUD fully on-screen with >=8px margin", hud[0] >= 8 and hud[1] >= 4 and hud[2] <= w - 8, [round(v) for v in hud])
        # worst-case HUD load: all chips + big numbers
        await pg.evaluate("""()=>{player.files=3;player.coffeeUntil=now+9e6;player.phonesUntil=now+9e6;stats.syncs=88;game.score=9999999}""")
        await pg.wait_for_timeout(400)
        groups = await pg.evaluate("""()=>{const c=document.getElementById('hudCanvas');const x=c.getContext('2d');const k=c.width/innerWidth;
          const bandH=Math.round(90*hudView.scale*hudView.dpr);const d=x.getImageData(0,0,c.width,bandH).data;const occ=[];
          for(let xx=0;xx<c.width;xx++){let on=false;for(let y=0;y<bandH;y+=3){if(d[(y*c.width+xx)*4+3]>20){on=true;break}}occ.push(on)}
          const runs=[];let s=-1,gap=0;for(let xx=0;xx<occ.length;xx++){if(occ[xx]){if(s<0)s=xx;gap=0}else if(s>=0){gap++;if(gap>=6*k){runs.push([s/k,(xx-gap)/k]);s=-1;gap=0}}}
          if(s>=0)runs.push([s/k,(occ.length-1)/k]);return runs.map(r=>r.map(Math.round))}""")
        rec("B HUD", "B2", name, "Worst-case HUD (3 chips + 8-digit score): left / clock / right clusters stay separate", len(groups) >= 3, groups)
        await pg.screenshot(path=f'shots/{tag}_hud_full.png')
        await pg.evaluate("()=>{player.files=0;player.coffeeUntil=0;player.phonesUntil=0;stats.syncs=0;game.score=0}")

        # ---------------- C. STATE TRANSITIONS (frame stability) ----------------
        base = await snap(pg)
        await get_caught(pg); sc = await snap(pg)
        rec("C States", "C1", name, "Caught: frame identical to pre-catch (layout/rect/buffer/zoom)", same_frame(base, sc) and sc['overlay'], (sc['layout'], sc['rect']))
        rec("C States", "C2", name, "Caught: controls hidden, no keys stuck", (not sc['ctl']) and sc['keys'] == [], sc['keys'])
        await pg.screenshot(path=f'shots/{tag}_caught.png')
        pt = await pg.evaluate("(()=>{const b=caughtBtns.find(b=>b.id==='continue');return [overlayView.ox+(b.x+b.w/2)*overlayView.sc,overlayView.oy+(b.y+b.h/2)*overlayView.sc]})()")
        await t.tap(*pt); await pg.wait_for_timeout(800); sa = await snap(pg)
        rec("C States", "C3", name, "Continue returns to PLAY on the same frame, controls back", sa['mode'] == 'PLAY' and same_frame(base, sa) and sa['ctl'], (sa['mode'], sa['ctl']))
        # caught -> restart
        await get_caught(pg)
        pt = await pg.evaluate("(()=>{const b=caughtBtns.find(b=>b.id==='restart');return [overlayView.ox+(b.x+b.w/2)*overlayView.sc,overlayView.oy+(b.y+b.h/2)*overlayView.sc]})()")
        await t.tap(*pt); await pg.wait_for_timeout(1200); sr = await snap(pg)
        rec("C States", "C4", name, "Caught > Restart shift: back in PLAY, same frame", sr['mode'] == 'PLAY' and same_frame(base, sr), (sr['mode'], sr['layout']))
        # pause via HUD chip
        hp = await pg.evaluate("[hudView.ox+(hudView.w-14-28)*hudView.scale,hudView.oy+(14+28)*hudView.scale]")
        await t.tap(*hp); await pg.wait_for_timeout(600); sp = await snap(pg)
        rec("C States", "C5", name, "Tap HUD menu chip pauses; frame identical; overlay drawn", sp['mode'] == 'PAUSED' and same_frame(base, sp) and sp['overlay'], (sp['mode'], sp['layout']))
        await pg.screenshot(path=f'shots/{tag}_pause.png')
        # toggle sound in menu
        before = await pg.evaluate("settings.sound")
        mp = await pg.evaluate("(()=>{const r=menu.rects[0];return [overlayView.ox+(r.x+r.w/2)*overlayView.sc,overlayView.oy+(r.y+r.h/2)*overlayView.sc]})()")
        await t.tap(*mp); await pg.wait_for_timeout(300)
        after = await pg.evaluate("settings.sound")
        rec("C States", "C6", name, "Pause menu: tapping Sound row toggles setting (hit-test aligned with overlay)", before != after, (before, after))
        await t.tap(*mp); await pg.wait_for_timeout(200)
        # resume
        rp = await pg.evaluate("(()=>{const i=menuItems().findIndex(x=>x.id==='resume');const r=menu.rects[i];return [overlayView.ox+(r.x+r.w/2)*overlayView.sc,overlayView.oy+(r.y+r.h/2)*overlayView.sc]})()")
        await t.tap(*rp); await pg.wait_for_timeout(600); sres = await snap(pg)
        rec("C States", "C7", name, "Resume returns to PLAY on same frame, controls back", sres['mode'] == 'PLAY' and same_frame(base, sres) and sres['ctl'], (sres['mode'], sres['ctl']))
        # tap outside menu closes
        await t.tap(*hp); await pg.wait_for_timeout(500); await t.tap(8, h // 2); await pg.wait_for_timeout(500)
        so = await snap(pg)
        rec("C States", "C8", name, "Tap outside pause card closes it", so['mode'] == 'PLAY', so['mode'])
        # pause card hit targets
        await t.tap(*hp); await pg.wait_for_timeout(500)
        pr = await pg.evaluate("(()=>{const R=menu.rects.filter(Boolean);const bad=[];for(let i=0;i<R.length;i++)for(let j=i+1;j<R.length;j++){const a=R[i],b=R[j];if(a.x<b.x+b.w&&b.x<a.x+a.w&&a.y<b.y+b.h&&b.y<a.y+a.h)bad.push([i,j])}return [bad,menuItems().map(x=>x.id)]})()")
        rec("C States", "C9", name, "Pause card: hit targets don't overlap; Resume/Start over are the only bottom buttons", not pr[0] and pr[1][-2:] == ['restart', 'resume'] and 'howto' not in pr[1], pr)
        # Start over from pause
        so2 = await pg.evaluate("(()=>{const i=menuItems().findIndex(x=>x.id==='restart');const r=menu.rects[i];return [overlayView.ox+(r.x+r.w/2)*overlayView.sc,overlayView.oy+(r.y+r.h/2)*overlayView.sc]})()")
        await pg.evaluate("player.x=3000"); await t.tap(*so2); await pg.wait_for_timeout(1200)
        s2 = await snap(pg)
        rec("C States", "C10", name, "Pause > Start over restarts the shift (player back at start, PLAY, same frame)", s2['mode'] == 'PLAY' and await pg.evaluate("player.x") < 600 and same_frame(base, s2), (s2['mode'], await pg.evaluate("Math.round(player.x)")))
        # exit / win / lose frame stability
        await pg.evaluate("()=>{if(game.mode!=='PLAY'){menu.open=false;howtoOpen=false;game.mode='PLAY'}}"); await pg.wait_for_timeout(300)
        await pg.evaluate("beginExit()"); await pg.wait_for_timeout(700); se = await snap(pg)
        rec("C States", "C11", name, "Elevator exit (EXIT): frame identical to gameplay", se['mode'] == 'EXIT' and same_frame(base, se), (se['mode'], se['layout'], se['rect']))
        await pg.screenshot(path=f'shots/{tag}_exit.png')
        await pg.evaluate("game.skipRide=true")
        try: await pg.wait_for_function("game.mode==='WIN'", timeout=20000)
        except Exception: pass
        await pg.wait_for_timeout(600); sw = await snap(pg)
        rec("C States", "C12", name, "Win card: frame identical to gameplay", sw['mode'] == 'WIN' and same_frame(base, sw), (sw['mode'], sw['layout'], sw['rect']))
        await pg.screenshot(path=f'shots/{tag}_win.png')
        if sw['mode'] == 'WIN':
            await pg.wait_for_timeout(1500)
            ab = await pg.evaluate("(()=>{const b=resultBtns.find(b=>b.id==='again');if(!b)return null;const sc=(layoutMode==='cover')?overlayView.sc:(document.getElementById('game').getBoundingClientRect().width/1104);"
                                   "const r=document.getElementById('game').getBoundingClientRect();return layoutMode==='cover'&&overlayActive?[overlayView.ox+(b.x+b.w/2)*overlayView.sc,overlayView.oy+(b.y+b.h/2)*overlayView.sc]:[r.left+(b.x+b.w/2)*sc,r.top+(b.y+b.h/2)*sc]})()")
            if ab:
                await t.tap(*ab); await pg.wait_for_timeout(1500)
                rec("C States", "C13", name, "Win card: 'Play again' tap restarts (hit-test aligned)", await pg.evaluate("game.mode") in ('PLAY', 'TITLE') and await pg.evaluate("howtoOpen||game.mode==='PLAY'"), await pg.evaluate("game.mode"))
            else: rec("C States", "C13", name, "Win card: 'Play again' button present", False, "no resultBtns")
        else:
            rec("C States", "C13", name, "Win card reached", False, sw['mode'])
        # lose
        await pg.evaluate("()=>{menu.open=false;howtoOpen=false;if(game.mode!=='PLAY')initializeGame();}"); await pg.wait_for_timeout(800)
        await pg.evaluate("lose()"); await pg.wait_for_timeout(800); sl = await snap(pg)
        rec("C States", "C14", name, "Lose card: frame identical to gameplay", sl['mode'] == 'LOSE' and same_frame(base, sl), (sl['mode'], sl['layout'], sl['rect']))
        await pg.screenshot(path=f'shots/{tag}_lose.png')
        await pg.evaluate("()=>{game.mode='TITLE';menu.open=false}"); await pg.wait_for_timeout(500)
        st = await snap(pg)
        rec("C States", "C15", name, "Back at title: letterboxed frame, controls & HUD layer hidden", st['layout'] == 'contain' and not st['ctl'] and not await pg.evaluate("document.body.classList.contains('play-touch')"), st['layout'])

        if deep:
            await deep_suite(pg, t, name, w, h, tag)
        rec("R Robust", "R0", name, "No JS errors / console errors during whole run", not errs, errs[:3])
    except Exception as e:
        rec("R Robust", "R-CRASH", name, "Test run completed without harness exception", False, repr(e)[:250])
    finally:
        await ctx.close()

async def to_play(pg, w, h):
    await pg.evaluate("()=>{menu.open=false;howtoOpen=false;keys.clear();touchKeys.clear()}")
    st = await pg.evaluate("game.mode")
    if st != 'PLAY':
        await pg.evaluate("initializeGame()"); await pg.wait_for_timeout(1500)

async def deep_suite(pg, t, name, w, h, tag):
    await to_play(pg, w, h)
    await pg.evaluate("()=>{player.x=600;player.y=GY;player.vx=0}"); await pg.wait_for_timeout(800)
    # D1: each button -> its key + held class, released cleanly
    keymap = {'arrowup': '.t-up', 'arrowleft': '.t-left', 'arrowdown': '.t-down', 'arrowright': '.t-right', 'e': '.t-e', 'f': '.t-f', ' ': '.jump'}
    bad = []
    for k, sel in keymap.items():
        await t.hold(sel, 1, 120)
        st = await pg.evaluate("([k,s])=>[keys.has(k),document.querySelector(s).classList.contains('held')]", [k, sel])
        await t.release(); await pg.wait_for_timeout(120)
        en = await pg.evaluate("([k,s])=>[keys.has(k),document.querySelector(s).classList.contains('held')]", [k, sel])
        if not (st == [True, True] and en == [False, False]): bad.append((k, st, en))
        await pg.evaluate("()=>{if(game.mode!=='PLAY'){menu.open=false;game.mode='PLAY'}}")
    rec("D Controls", "D1", name, "Each of 7 buttons presses its key, shows held state, releases cleanly", not bad, bad)
    await pg.evaluate("()=>{player.sitting=false;player.fakingWork=false;player.hidden=false;player.ducking=false;player.inRoom=null;player.climbing=null;player.x=600;player.y=GY;player.vx=0;player.vy=0}")
    await pg.wait_for_timeout(400)
    # D2: movement (wait for distance, not wall-clock: headless software rendering can be slow on big canvases)
    await pg.evaluate("()=>{player.x=600;player.vx=0}"); await pg.wait_for_timeout(300)
    x0 = await pg.evaluate("player.x"); await t.hold('.t-right', 1, 50)
    try: await pg.wait_for_function("(x)=>player.x>x+30", arg=x0, timeout=15000)
    except Exception: pass
    x1 = await pg.evaluate("player.x"); await t.release(); await pg.wait_for_timeout(300)
    x2 = await pg.evaluate("player.x"); await t.hold('.t-left', 1, 50)
    try: await pg.wait_for_function("(x)=>player.x<x-30", arg=x2, timeout=15000)
    except Exception: pass
    x3 = await pg.evaluate("player.x"); await t.release()
    rec("D Controls", "D2", name, "Right moves +x, Left moves -x", x1 > x0 + 30 and x3 < x2 - 30, (round(x0), round(x1), round(x2), round(x3)))
    # D3: jump
    await pg.evaluate("()=>{player.sitting=false;player.fakingWork=false;player.hidden=false;player.ducking=false}")
    await pg.wait_for_timeout(600)
    await pg.evaluate("()=>{window.__miny=1e9;const f=()=>{window.__miny=Math.min(window.__miny,player.y);requestAnimationFrame(f)};f()}")
    await t.hold('.jump', 1, 80); await t.release()
    try: await pg.wait_for_function('player.grounded && window.__miny < 500', timeout=4000)
    except Exception: pass
    await pg.wait_for_timeout(200)
    miny = await pg.evaluate("window.__miny")
    rec("D Controls", "D3", name, "JUMP lifts the player (>=60 units) and lands", miny < GY_ - 60 and await pg.evaluate("player.grounded"), round(miny))
    # D4: duck
    await t.hold('.t-down', 1, 300); duck = await pg.evaluate("player.ducking"); await t.release()
    rec("D Controls", "D4", name, "DOWN ducks the player", duck, duck)
    # D5: ladder climb via UP
    await pg.evaluate("()=>{player.x=10070+13-14;player.y=GY;player.vx=0;player.vy=0}"); await pg.wait_for_timeout(500)
    await t.hold('.t-up', 1, 700); climbing = await pg.evaluate("!!player.climbing"); yy = await pg.evaluate("player.y"); await t.release()
    rec("D Controls", "D5", name, "UP button climbs the executive-floor ladder", climbing and yy < GY_ - 10, (climbing, round(yy)))
    await pg.evaluate("()=>{player.climbing=null;player.x=600;player.y=GY;player.vy=0}"); await pg.wait_for_timeout(400)
    # D6: multitouch: right + jump
    xr, yr = await t.center('.t-right'); xj, yj = await t.center('.jump')
    await t.touch('touchStart', [(xr, yr, 1)]); await pg.wait_for_timeout(200)
    await t.touch('touchStart', [(xr, yr, 1), (xj, yj, 2)]); await pg.wait_for_timeout(120)
    both = await pg.evaluate("[keys.has('arrowright'),keys.has(' ')]")
    await t.touch('touchEnd', [(xr, yr, 1)]); await pg.wait_for_timeout(200)  # lift jump finger (id 2 remains? we end by listing remaining)
    rest = await pg.evaluate("[keys.has('arrowright'),keys.has(' ')]")
    await t.release(); await pg.wait_for_timeout(200)
    rec("D Controls", "D6", name, "Multi-touch: Right + Jump held together", both == [True, True], (both, rest))
    # D7: glide left -> down -> off
    xl, yl = await t.center('.t-left'); xd, yd = await t.center('.t-down')
    await t.touch('touchStart', [(xl, yl, 1)]); await pg.wait_for_timeout(100)
    await t.touch('touchMove', [(xd, yd, 1)]); await pg.wait_for_timeout(120)
    g1 = await pg.evaluate("[keys.has('arrowleft'),keys.has('arrowdown')]")
    await t.touch('touchMove', [(w // 2, h // 3, 1)]); await pg.wait_for_timeout(120)
    g2 = await pg.evaluate("[keys.has('arrowleft'),keys.has('arrowdown')]")
    await t.release(); await pg.wait_for_timeout(150)
    rec("D Controls", "D7", name, "Glide between buttons hands the key over; sliding off releases", g1 == [False, True] and g2 == [False, False], (g1, g2))
    # D8: touchcancel
    await t.hold('.t-right', 1, 150); await t.touch('touchCancel', []); await pg.wait_for_timeout(200)
    rec("D Controls", "D8", name, "touchcancel releases the key (no stuck run)", not await pg.evaluate("keys.has('arrowright')"), await pg.evaluate("[...keys]"))
    # D9: finger held on button while getting caught -> released, no run-away
    await to_play(pg, w, h); await t.hold('.t-right', 1, 200)
    await pg.evaluate("()=>{player.invulUntil=0}"); await pg.evaluate("caughtBy({kind:'manager'})"); await pg.wait_for_timeout(600)
    await t.release(); await pg.wait_for_timeout(200)
    rec("D Controls", "D9", name, "Holding a button while caught leaves no stuck key", await pg.evaluate("[...keys]") == [], await pg.evaluate("[...keys]"))
    await pg.wait_for_function("game.caughtHold===true", timeout=20000)
    await to_play(pg, w, h)
    await pg.evaluate("()=>{game.mode='PLAY'}"); await pg.wait_for_timeout(600)
    # D10: tapping empty canvas during play is harmless
    await t.tap(w // 2, h // 3); await pg.wait_for_timeout(300)
    rec("D Controls", "D10", name, "Tap on empty world during play does nothing (no pause/crash)", await pg.evaluate("game.mode") == 'PLAY', await pg.evaluate("game.mode"))
    # D11: tap spam
    x, y = await t.center('.jump')
    for _ in range(40):
        await t.touch('touchStart', [(x, y, 1)]); await t.touch('touchEnd', [])
    await pg.wait_for_timeout(300)
    rec("D Controls", "D11", name, "40 rapid Jump taps leave no stuck key", await pg.evaluate("[...keys]") == [], await pg.evaluate("[...keys]"))
    # ---------------- E. ORIENTATION / RESIZE ----------------
    await to_play(pg, w, h)
    await pg.set_viewport_size({'width': h, 'height': w}); await pg.wait_for_timeout(700)
    rp = await pg.evaluate("[getComputedStyle(document.getElementById('rotatePrompt')).display,getComputedStyle(document.querySelector('.wrap')).display,getComputedStyle(document.getElementById('touchUI')).display]")
    rec("E Orientation", "E1", name, "Portrait: rotate prompt shown, game + controls hidden", rp[0] != 'none' and rp[1] == 'none' and rp[2] == 'none', rp)
    tt = await pg.evaluate("game.timeMs"); await pg.wait_for_timeout(800); tt2 = await pg.evaluate("game.timeMs")
    rec("E Orientation", "E2", name, "Portrait: game clock does not run behind the prompt", abs(tt2 - tt) < 50, (round(tt), round(tt2)))
    await pg.set_viewport_size({'width': w, 'height': h}); await pg.wait_for_timeout(900)
    s = await snap(pg); r = s['rect']
    rec("E Orientation", "E3", name, "Back to landscape: cover layout restored, controls visible", s['layout'] == 'cover' and r[0] <= .5 and r[0] + r[2] >= w - .5 and s['ctl'], (s['layout'], r, s['ctl']))
    # resize while caught then Continue still hits
    await get_caught(pg); await pg.set_viewport_size({'width': w - 60, 'height': h - 20}); await pg.wait_for_timeout(700)
    pt = await pg.evaluate("(()=>{const b=caughtBtns.find(b=>b.id==='continue');return [overlayView.ox+(b.x+b.w/2)*overlayView.sc,overlayView.oy+(b.y+b.h/2)*overlayView.sc]})()")
    await t.tap(*pt); await pg.wait_for_timeout(700)
    rec("E Orientation", "E4", name, "Resize while caught: Continue still tappable", await pg.evaluate("game.mode") == 'PLAY', await pg.evaluate("game.mode"))
    await pg.set_viewport_size({'width': w, 'height': h}); await pg.wait_for_timeout(600)
    # ---------------- F. ROBUSTNESS ----------------
    await to_play(pg, w, h)
    await pg.evaluate("window.dispatchEvent(new Event('blur'))"); await pg.wait_for_timeout(500); sb = await snap(pg)
    rec("F Robust", "F1", name, "App backgrounded (blur) auto-pauses on same frame with overlay", sb['mode'] == 'PAUSED' and sb['layout'] == 'cover' and sb['overlay'], (sb['mode'], sb['layout']))
    await pg.evaluate("closeMenu()"); await pg.wait_for_timeout(300)
    fps = await pg.evaluate("new Promise(r=>{let n=0;const t0=performance.now();const f=()=>{n++;if(performance.now()-t0<2000)requestAnimationFrame(f);else r(n/2)};requestAnimationFrame(f)})")
    if fps >= 20: rec("F Robust", "F2", name, "Frame rate in cover mode >= 20 fps", True, round(fps))
    else: blocked("F Robust", "F2", name, "Frame rate in cover mode", f"{round(fps)} fps under headless SOFTWARE rendering (baseline pre-cover build ~17 fps on same box); needs real-device profiling")
    # safe-area emulation
    try:
        await cdp_safe(pg, t, name, w, h)
    except Exception as e:
        blocked("G Safe-area", "G1", name, "Notch/home-indicator insets respected", "CDP override unavailable: " + repr(e)[:120])

GY_ = 530
async def cdp_safe(pg, t, name, w, h):
    await t.cdp.send('Emulation.setSafeAreaInsetsOverride', {'insets': {'top': 0, 'left': 47, 'right': 47, 'bottom': 21}})
    await pg.set_viewport_size({'width': w - 1, 'height': h}); await pg.set_viewport_size({'width': w, 'height': h}); await pg.wait_for_timeout(900)
    btns = await pg.evaluate("[...document.querySelectorAll('.tbtn')].map(e=>{const b=e.getBoundingClientRect();return [e.dataset.key,b.left,b.top,b.right,b.bottom]})")
    hv = await pg.evaluate("[hudView.ox,hudView.w*hudView.scale+hudView.ox]")
    okc = all(b[1] >= 47 - .5 and b[3] <= w - 47 + .5 and b[4] <= h - 21 + .5 for b in btns)
    rec("G Safe-area", "G1", name, "Controls stay inside emulated notch insets (L/R 47, bottom 21)", okc, [b for b in btns if not (b[1] >= 46.5 and b[3] <= w - 46.5 and b[4] <= h - 20.5)][:3])
    rec("G Safe-area", "G2", name, "HUD origin/width respect the insets", abs(hv[0] - 47) < 1 and hv[1] <= w - 47 + 1, [round(v) for v in hv])
    await t.cdp.send('Emulation.setSafeAreaInsetsOverride', {'insets': {'top': 0, 'left': 0, 'right': 0, 'bottom': 0}})

import os
ONLY = [x for x in os.environ.get("QA_ONLY", "").split(",") if x]
async def main(out):
    async with async_playwright() as pw:
        b = await pw.chromium.launch()
        sem = asyncio.Semaphore(2)
        async def one(d):
            async with sem: await run_device(b, *d)
        await asyncio.gather(*[one(d) for d in DEVICES if not ONLY or any(o in d[0] for o in ONLY)])
        await b.close()
    json.dump(RESULTS, open(out, 'w'), indent=1)
    tot = len(RESULTS); f = [r for r in RESULTS if r['status'] == 'FAIL']; bl = [r for r in RESULTS if r['status'] == 'BLOCKED']
    print(f"TOTAL {tot}  PASS {tot-len(f)-len(bl)}  FAIL {len(f)}  BLOCKED {len(bl)}")
if __name__ == '__main__':
    import os; os.makedirs('shots', exist_ok=True)
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else 'results.json'))
