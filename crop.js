const { chromium } = require(require('child_process').execSync('npm root -g').toString().trim()+'/playwright');
(async () => {
  const b = await chromium.launch(); const pg = await b.newPage({ viewport: { width: 1104, height: 621 } });
  await pg.goto('file://' + process.cwd() + '/game.html'); await pg.waitForTimeout(1200);
  await pg.evaluate(() => { startGame(); game.mode='PAUSED'; });
  await pg.evaluate(() => { const c=document.createElement('canvas'); c.width=360;c.height=120; c.id='t'; c.style.cssText='position:fixed;left:0;top:0;z-index:99;image-rendering:pixelated'; document.body.appendChild(c); const g=c.getContext('2d'); g.imageSmoothingEnabled=false; g.fillStyle='#F4EFE4'; g.fillRect(0,0,360,120); ['snack','charger','powerBank'].forEach((k,i)=>{const sp=itemSprite(k); g.drawImage(sp,30+i*110,20,sp.width*5,sp.height*5);}); });
  await pg.screenshot({ path: 'items.png', clip:{x:0,y:0,width:360,height:120} });
  await b.close();
})();
