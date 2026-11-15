// Re-render design deliverables with the repository's installed Playwright and Chrome.
// From repository root: node source-art/ui/boss-alert-navigation-v1/render.cjs
const path = require('path');
const { chromium } = require('../../../src/cocos/node_modules/playwright');
const { pathToFileURL } = require('url');
(async () => {
  const browser = await chromium.launch({ headless: true, channel: 'chrome' });
  try {
    const page = await browser.newPage({ viewport: {width:1200,height:900}, deviceScaleFactor:3 });
    await page.goto(pathToFileURL(path.join(__dirname,'index.html')).href);
    await page.evaluate(() => document.fonts.ready);
    await page.addStyleTag({content:'.viewport{width:844px!important}.game{transform:none!important}'});
    const states = [['刷新提醒','01-notice'],['目标列表','02-list'],['正在寻路','03-route'],['遇敌暂停','04-paused'],['抵达入口','05-arrived'],['等待复战','06-cooldown'],['精英出现','07-elite'],['战斗中','08-combat']];
    for (const [label,file] of states) {
      await page.getByRole('button',{name:label,exact:true}).click();
      const b = await page.locator('#game').boundingBox();
      await page.screenshot({path:path.join(__dirname,file+'.png'),clip:{x:b.x,y:b.y,width:844,height:390}});
    }
    const board = await browser.newPage({viewport:{width:1808,height:1200},deviceScaleFactor:1});
    await board.goto(pathToFileURL(path.join(__dirname,'board.html')).href);
    await board.evaluate(() => document.fonts.ready);
    await board.screenshot({path:path.join(__dirname,'design-board.png'),fullPage:true});
    console.log('Rendered 8 states at 2532 × 1170 and design-board.png');
  } finally { await browser.close(); }
})().catch(e=>{console.error(e);process.exitCode=1;});
