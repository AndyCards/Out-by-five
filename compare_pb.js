const { chromium } = require(require('child_process').execSync('npm root -g').toString().trim()+'/playwright');
(async () => {
  const b = await chromium.launch();
  for (const [file, tag] of [['game.before-collectible-art-polish.html','before'], ['game.html','after']]) {
    const pg = await b.newPage({ viewport: { width: 1104, height: 621 } });
    await pg.goto('file://' + process.cwd() + '/' + file); await pg.waitForTimeout(1200);
    await pg.evaluate(() => { startGame(); player.invulUntil=1e12; enemies.forEach(e=>e.awareness=0); player.x=1830; player.y=GY-90; player.vy=0; game.cameraX=1550; });
    await pg.waitForTimeout(300);
    await pg.screenshot({ path: `pb_${tag}.png` });
    await pg.close();
  }
  await b.close();
})();
