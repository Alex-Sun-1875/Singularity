const {chromium}=require('../../../src/cocos/node_modules/playwright');
const {pathToFileURL}=require('node:url');
const fs=require('node:fs');
const path=require('node:path');
(async()=>{
  const folder='C:/Users/Alexa/.codex/visualizations/2026/11/17/01a1e853-dfaa-7992-913a-6822bff2eef8';
  const browser=await chromium.launch({headless:true});
  const page=await browser.newPage({viewport:{width:760,height:1000},deviceScaleFactor:2});
  const errors=[];page.on('pageerror',error=>errors.push(error.message));
  await page.goto(pathToFileURL(path.join(folder,'skill-selection-preview.html')).href);
  const frame=page.frameLocator('iframe');
  const product=frame.locator('.ss-panel');await product.waitFor();
  await product.screenshot({path:path.join(__dirname,'skill-selection-preview.png'),animations:'disabled'});
  await product.locator('[data-skill="2"]').click();
  if(await product.locator('.ss-detailname').textContent()!=='铁誓壁垒')throw Error('Detail selection failed');
  if(await product.locator('.ss-selected').count()!==1)throw Error('Selection must be unique');
  await product.screenshot({path:path.join(__dirname,'shield-selected-preview.png'),animations:'disabled'});
  await product.locator('[data-skill="3"]').click();
  if(await product.locator('.ss-detailmeta').textContent()!=='Lv.10 开放 · 群攻')throw Error('Locked-skill browsing failed');
  await product.locator('[data-skill="0"]').click();
  const responsive=[];
  for(const width of [736,620,390,320]){
    await page.setViewportSize({width,height:1100});
    const geometry=await product.evaluate(element=>{
      const p=element.getBoundingClientRect();
      const overflow=Array.from(element.querySelectorAll('*')).filter(child=>{
        const r=child.getBoundingClientRect();return r.width>0&&(r.left<p.left-2||r.right>p.right+2);
      }).map(child=>child.className);
      const rows=Array.from(element.querySelectorAll('.ss-row')).map(row=>{
        const box=row.getBoundingClientRect();
        const contentOverflow=Array.from(row.querySelectorAll('.ss-icon,.ss-copy,.ss-level')).some(child=>{
          const r=child.getBoundingClientRect();return r.top<box.top+3||r.bottom>box.bottom-3;
        });
        return {height:box.height,contentOverflow};
      });
      return {width:p.width,height:p.height,overflow,rows};
    });
    responsive.push({viewport:width,...geometry});
    if(width===320)await product.screenshot({path:path.join(__dirname,'narrow-preview.png'),animations:'disabled'});
  }
  const result={status:errors.length||responsive.some(item=>item.overflow.length||item.rows.some(row=>row.contentOverflow))?'needs_attention':'passed',errors,responsive,
    interactions:'One selected row; shield selection updates detail; locked skill remains browsable.',
    boundary:'Design preview only. Cocos runtime, horizontal phone layout, and TapTap device acceptance not performed.'};
  fs.writeFileSync(path.join(__dirname,'preview-validation.json'),JSON.stringify(result,null,2)+'\n');
  console.log(JSON.stringify(result));await browser.close();
})().catch(error=>{console.error(error);process.exitCode=1;});
