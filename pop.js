const { chromium } = require(require('child_process').execSync('npm root -g').toString().trim()+'/playwright');
(async () => {
  const b = await chromium.launch(); const pg = await b.newPage({ viewport: { width: 1104, height: 621 } });
  await pg.goto('file://' + process.cwd() + '/game.html'); await pg.waitForTimeout(1200);
  await pg.evaluate(() => { startGame(); player.invulUntil=1e12; player.x=2730; player.y=GY-84; player.vy=0; game.cameraX=2300; });
  await pg.waitForTimeout(250); await pg.screenshot({ path: 'pop.png' });
  await b.close();
})();
