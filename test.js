const { chromium } = require('/home/claude/.npm-global/lib/node_modules/playwright');
(async () => {
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 1104, height: 621 } });
  const errs = []; pg.on('pageerror', e => errs.push(e.message)); pg.on('console', m => { if (m.type()==='error') errs.push(m.text()); });
  await pg.goto('file://' + process.cwd() + '/game.html');
  await pg.waitForTimeout(1500);
  await pg.evaluate(() => { startGame(); });
  await pg.waitForTimeout(300);
  const n = await pg.evaluate(() => pickups.filter(p => p.loot).length);
  console.log('loot count', n);
  const shots = [[1040,'z1'],[2650,'z2'],[5700,'z3a'],[6300,'z3b'],[8500,'z4'],[10700,'z5']];
  for (const [x, name] of shots) {
    await pg.evaluate((x) => { player.x = x; player.y = GY; player.invulUntil = 1e12; enemies.forEach(e=>e.awareness=0); }, x);
    await pg.waitForTimeout(400);
    await pg.screenshot({ path: `shot_${name}.png` });
  }
  // pickup test: put player on the cabinet at 1080
  const before = await pg.evaluate(() => { player.x = 1080; player.y = GY - 80; player.vy = 0; return game.score; });
  await pg.waitForTimeout(150);
  await pg.screenshot({ path: 'shot_pickup.png' });
  console.log('score', before, '->', await pg.evaluate(() => game.score), 'loot', await pg.evaluate(() => stats.loot));
  await pg.evaluate(() => { game.mode='WIN'; game.result={clock:'4:59:12', titles:[['THE GHOST','x']], score:game.score}; });
  await pg.waitForTimeout(300); await pg.screenshot({ path: 'shot_win.png' });
  await pg.evaluate(() => { game.mode='LOSE'; });
  await pg.waitForTimeout(300); await pg.screenshot({ path: 'shot_lose.png' });
  console.log('errors', errs);
  await b.close();
})();
