const playwright = require('playwright');

(async () => {
  const browser = await playwright.chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  
  await page.goto('file:///home/claude/work/game.html', { waitUntil: 'load' });
  await page.waitForTimeout(2000); // Wait for game to load and render
  
  await page.screenshot({ path: '/tmp/claude-0/-home-claude/ce4891c6-a0da-5bb1-ba8b-7c4683ffb0f3/scratchpad/game_screenshot.png', fullPage: false });
  
  await browser.close();
  console.log('Screenshot saved!');
})();
