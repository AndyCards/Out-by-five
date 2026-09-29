const { chromium } = require(require('child_process').execSync('npm root -g').toString().trim()+'/playwright');
(async () => {
  const b = await chromium.launch(); const pg = await b.newPage({ viewport: { width: 1104, height: 621 } });
  const errs = []; pg.on('pageerror', e => errs.push(e.message)); pg.on('console', m=>{if(m.type()==='error') errs.push(m.text());});
  await pg.goto('file://' + process.cwd() + '/game.html'); await pg.waitForTimeout(1200);
  await pg.evaluate(() => startGame());
  await pg.waitForTimeout(300);
  // walk through all 17 loot items collecting them, verify score math + point values unchanged
  const result = await pg.evaluate(() => {
    let collected = 0, expected = 0;
    const vals = { snack: 500, charger: 750, powerBank: 1000 };
    const total = pickups.filter(p => p.loot).length;
    // force-collect every loot pickup directly, bypassing physics, to check scoring math only
    for (const p of [...pickups]) {
      if (!p.loot) continue;
      expected += vals[p.type];
      player.x = p.x; player.y = p.y; player.vy = 0;
    }
    return { total };
  });
  // actually run physics: teleport to each loot's exact spot and tick a frame to trigger real pickup path
  const coords = await pg.evaluate(() => pickups.filter(p=>p.loot).map(p=>({x:p.x,y:p.y,type:p.type})));
  for (const c of coords) {
    await pg.evaluate((c) => { player.x = c.x; player.y = c.y; player.vy = 0; }, c);
    await pg.evaluate(() => update(16));
  }
  const final = await pg.evaluate(() => ({ score: game.score, loot: stats.loot, remaining: pickups.filter(p=>p.loot).length }));
  console.log('coords collected:', coords.length, 'final:', final, 'errors:', errs);
  await b.close();
})();
