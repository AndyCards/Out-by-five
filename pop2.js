const { chromium } = require(require('child_process').execSync('npm root -g').toString().trim()+'/playwright');
(async () => {
  const b = await chromium.launch(); const pg = await b.newPage({ viewport: { width: 1104, height: 621 } });
  const errs = []; pg.on('pageerror', e => errs.push(e.message));
  await pg.goto('file://' + process.cwd() + '/game.html'); await pg.waitForTimeout(1200);
  await pg.evaluate(() => { startGame(); player.invulUntil=1e12; player.x=1080; player.y=GY-90; player.vy=0; game.cameraX=850; });
  await pg.waitForTimeout(60);
  await pg.screenshot({ path: 'pop_mid.png' });
  await pg.waitForTimeout(500);
  await pg.screenshot({ path: 'pop_after.png' });
  console.log('errors', errs, 'score', await pg.evaluate(()=>game.score), 'loot', await pg.evaluate(()=>stats.loot));
  await b.close();
})();
