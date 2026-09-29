const { chromium } = require(require('child_process').execSync('npm root -g').toString().trim()+'/playwright');
(async () => {
  const b = await chromium.launch(); const pg = await b.newPage({ viewport: { width: 1104, height: 621 } });
  const errs = []; pg.on('pageerror', e => errs.push(e.message)); pg.on('console', m=>{if(m.type()==='error') errs.push(m.text());});
  await pg.goto('file://' + process.cwd() + '/game.html'); await pg.waitForTimeout(1200);
  await pg.evaluate(() => { startGame(); player.invulUntil = 1e12; enemies.forEach(e=>e.awareness=0); });
  const spots = [
    [590, 'z1_snack', 530],
    [1080, 'z1_charger', 530-90],
    [1850, 'z1_powerbank', 530-150],
    [6470, 'z3_powerbank', 530-188],
  ];
  for (const [x, name, py] of spots) {
    await pg.evaluate(({x,py}) => { player.x = x - 70; player.y = GY; player.vy = 0; game.cameraX = Math.max(0, x - 550); }, {x,py});
    await pg.waitForTimeout(350);
    await pg.screenshot({ path: `s3_${name}.png` });
  }
  // floor carpet — open desks zone, wide shot at ground level
  await pg.evaluate(() => { player.x = 400; player.y = GY; game.cameraX = 0; });
  await pg.waitForTimeout(200);
  await pg.screenshot({ path: 's3_floor_opendesks.png' });
  await pg.evaluate(() => { player.x = 7200; game.cameraX = 7100; });
  await pg.waitForTimeout(200);
  await pg.screenshot({ path: 's3_floor_meetingrooms.png' });
  // CAUGHT screen CTA buttons
  await pg.evaluate(() => {
    game.mode = 'CAUGHT'; game.caughtHold = true; game.sceneT = 999;
    game.invite = { kind:'manager', title:'Quick Sync', at:'4:57', length:'15 min', org:'Dana', agenda:'Sync on syncs.' };
  });
  await pg.waitForTimeout(150);
  await pg.screenshot({ path: 's3_caught.png' });
  // WIN screen CTA buttons
  await pg.evaluate(() => { game.mode='WIN'; game.result={clock:'4:59:12', titles:[['THE GHOST','x']], score:game.score}; });
  await pg.waitForTimeout(150);
  await pg.screenshot({ path: 's3_win.png' });
  console.log('errors', errs);
  await b.close();
})();
