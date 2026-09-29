const { chromium } = require(require('child_process').execSync('npm root -g').toString().trim()+'/playwright');
(async () => {
  const b = await chromium.launch(); const pg = await b.newPage({ viewport: { width: 1104, height: 621 } });
  const errs = []; pg.on('pageerror', e => errs.push(e.message));
  await pg.goto('file://' + process.cwd() + '/game.html'); await pg.waitForTimeout(1200);
  await pg.evaluate(() => { startGame(); player.invulUntil = 1e12; enemies.forEach(e=>e.awareness=0); });
  const spots = [
    [590, 'z1_snack'],       // desk snack
    [1080, 'z1_charger'],    // cabinet charger, manager nearby
    [1890, 'z1_powerbank'],  // high ledge power bank
    [2730, 'z2_charger'],
    [5150, 'z3_snack'],
    [6470, 'z3_powerbank'],
    [10945, 'z5_powerbank'],
  ];
  for (const [x, name] of spots) {
    await pg.evaluate((x) => { player.x = x - 60; player.y = GY; player.vy = 0; game.cameraX = Math.max(0, x - 550); }, x);
    await pg.waitForTimeout(350);
    await pg.screenshot({ path: `s2_${name}.png` });
  }
  console.log('errors', errs);
  await b.close();
})();
