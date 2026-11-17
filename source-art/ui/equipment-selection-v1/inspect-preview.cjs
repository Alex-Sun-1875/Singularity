const {chromium} = require('../../../src/cocos/node_modules/playwright');
const path = require('node:path');
const fs = require('node:fs');
const {pathToFileURL} = require('node:url');

(async()=>{
  const folder='C:/Users/Alexa/.codex/visualizations/2026/11/17/01a1e853-dfaa-7992-913a-6822bff2eef8';
  const browser=await chromium.launch({headless:true});
  const page=await browser.newPage({viewport:{width:760,height:1100},deviceScaleFactor:2});
  const errors=[];
  page.on('pageerror',error=>errors.push(error.message));
  await page.goto(pathToFileURL(path.join(folder,'equipment-selection-preview.html')).href);
  const frame=page.frameLocator('iframe');
  const product=frame.locator('[data-mode="corners"] .es-product');
  await product.waitFor();
  await product.screenshot({path:path.join(__dirname,'selection-interactive-preview.png')});
  await product.locator('[data-item="steel"]').click();
  if(await product.locator('.es-name').textContent()!=='桥上的最后一人')throw Error('Selection did not update details');
  if(await product.locator('.es-worn-tile').getAttribute('class')!=='es-tile es-worn-tile')throw Error('Worn slot acquired selection');
  await product.locator('[data-item="common"]').click();
  if(await product.locator('[data-item="common"]').getAttribute('aria-pressed')!=='true')throw Error('Equipped selection did not restore');
  const responsive=[];
  for(const width of [736,620,390,320]){
    await page.setViewportSize({width,height:1200});
    const measurement=await product.evaluate(element=>{
      const own=element.getBoundingClientRect();
      const overflow=Array.from(element.querySelectorAll('*')).filter(child=>{
        const box=child.getBoundingClientRect();
        return box.width>0&&(box.left<own.left-2||box.right>own.right+2);
      }).map(child=>child.className);
      return {width:own.width,height:own.height,overflow};
    });
    responsive.push({viewport:width,...measurement});
    if(width===320)await product.screenshot({path:path.join(__dirname,'selection-narrow-preview.png')});
  }
  await page.setViewportSize({width:760,height:1100});
  await frame.locator('[data-variant="细银框与顶标"]').evaluate(section=>{
    section.parentElement.querySelectorAll(':scope > section').forEach(child=>child.hidden=child!==section);
  });
  await frame.locator('[data-mode="outline"] .es-product').screenshot({path:path.join(__dirname,'selection-alternative-preview.png')});
  const result={status:errors.length||responsive.some(row=>row.overflow.length)?'needs_attention':'passed',errors,responsive,
    interaction:'Inventory selection updates details; worn socket stays quiet; equipped state preserved.',
    boundary:'Local design preview only; not Cocos runtime, phone touch acceptance or TapTap device validation.'};
  fs.writeFileSync(path.join(__dirname,'preview-validation.json'),JSON.stringify(result,null,2)+'\n');
  console.log(JSON.stringify(result));
  await browser.close();
})().catch(error=>{console.error(error);process.exitCode=1;});
