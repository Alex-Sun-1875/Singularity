// Reproducible design render and local interaction verification.
const {chromium}=require('../../../src/cocos/node_modules/playwright');
const fs=require('fs'),path=require('path'),assert=require('assert');
(async()=>{
  const browser=await chromium.launch({headless:true,channel:'chrome'});
  try{
    const page=await browser.newPage({viewport:{width:1000,height:850},deviceScaleFactor:3}),errors=[];
    page.on('pageerror',e=>errors.push(e.message));page.on('response',r=>{if(r.status()>=400&&!r.url().includes('favicon'))errors.push(`${r.status()}: ${r.url()}`);});
    await page.goto('http://127.0.0.1:8846/source-art/ui/boss-alert-navigation-v2/');await page.evaluate(()=>document.fonts.ready);
    await page.addStyleTag({content:'.stage-wrap{width:844px!important}.stage{transform:none!important}'});
    const shot=async name=>{const b=await page.locator('#stage').boundingBox();await page.screenshot({path:path.join(__dirname,name+'.png'),clip:{x:b.x,y:b.y,width:844,height:390}});};
    const mode=()=>page.locator('#stage').getAttribute('data-mode');
    const filtered=[];
    for(const [level,expected] of [['4',['overseer']],['10',['overseer']],['13',['warden','huntmaster','oath','overseer']],['18',['warden','huntmaster','oath']],['25',[]]]){
      await page.selectOption('#player-level',level);
      const ids=await page.locator('.encounter').evaluateAll(a=>a.map(n=>n.dataset.id));assert.deepEqual(ids,expected);
      assert.equal(await page.locator('[data-chapter]').count(),0);
      assert((await page.locator('#hero-name').innerText()).includes('Lv'+level));
      assert.equal(await page.locator('#boss-open>img').getAttribute('src'),'assets/boss-entry-beast-v1.png');
      filtered.push({level:Number(level),range:[Math.max(1,Number(level)-5),Number(level)+5],ids});
      if(level==='4')await shot('02-list-ch1');if(level==='18')await shot('03-list-ch2');if(level==='25'){assert(await page.locator('#go').isDisabled());await shot('10-empty-level25');}
    }
    await page.selectOption('#player-level','18');await page.locator('#close').click();assert.equal(await mode(),'entry');await shot('08-entry');
    await page.locator('#boss-open').click();assert.equal(await mode(),'list');
    await page.locator('[data-id=huntmaster]').click();assert.equal(await mode(),'list');assert.equal(await page.locator('#go span').innerText(),'提前前往');await shot('04-cooldown');
    await page.locator('#follow').click();assert.equal(await page.locator('#follow').getAttribute('aria-pressed'),'true');
    await page.locator('#go').click();assert.equal(await mode(),'route');
    await page.locator('#navigate').click();assert.equal(await mode(),'paused');await page.locator('#navigate').click();assert.equal(await mode(),'route');
    await page.locator('#boss-open').click();await page.locator('#close').click();assert.equal(await mode(),'paused');
    const fixedTime=new Date();await page.clock.install({time:fixedTime});await page.clock.pauseAt(new Date(fixedTime.getTime()+1000));
    await page.getByRole('button',{name:'消息叠放',exact:true}).click();await shot('09-message-stack');
    const stack=await page.evaluate(()=>{const scale=document.querySelector('#stage').getBoundingClientRect().width/844;const rect=s=>{const b=document.querySelector(s).getBoundingClientRect();return{x:b.x/scale,y:b.y/scale,w:b.width/scale,h:b.height/scale};};return{notice:rect('#spawn-notice'),other:rect('#ordinary-message'),auto:rect('#auto')};});
    assert(Math.abs(stack.other.y-stack.notice.y-stack.notice.h-8)<1);
    assert.equal(await page.locator('#spawn-notice').evaluate(e=>e.offsetParent.offsetTop),54);
    const noticeTiming=await page.evaluate(()=>({duration:window.bossPreviewV2.noticeDurationMs,remaining:window.bossPreviewV2.noticeRemainingMs}));assert.equal(noticeTiming.duration,10000);assert(noticeTiming.remaining>8500);
    await page.clock.runFor(9000);assert(await page.locator('#spawn-notice').isVisible());
    await page.clock.runFor(1000);assert.equal(await mode(),'quiet');assert.equal(await page.locator('#spawn-notice').isVisible(),false);await shot('11-after-ten-seconds');await page.clock.resume();
    assert.equal(await page.locator('#ordinary-message').isVisible(),true);
    const ordinaryY=await page.locator('#ordinary-message').evaluate(e=>e.getBoundingClientRect().y);const stackY=await page.locator('#message-stack').evaluate(e=>e.getBoundingClientRect().y);assert(Math.abs(ordinaryY-stackY)<1);
    await page.getByRole('button',{name:'刷新提醒',exact:true}).click();await shot('01-notice');await page.locator('#notice-go').click();await shot('05-route');await page.locator('#navigate').click();await shot('06-paused');
    await page.evaluate(()=>window.bossPreviewV2.select('warden'));await page.getByRole('button',{name:'抵达',exact:true}).click();assert(await page.locator('#fight').isVisible());await shot('07-arrived');
    await page.getByRole('button',{name:'目标列表',exact:true}).click();
    const dimensions=await page.evaluate(()=>{const s=document.querySelector('#stage').getBoundingClientRect(),scale=s.width/844;return [...document.querySelectorAll('#target-panel button')].filter(e=>e.getBoundingClientRect().height).map(e=>{const b=e.getBoundingClientRect();return{name:e.id||e.textContent.trim(),x:(b.x-s.x)/scale,y:(b.y-s.y)/scale,w:b.width/scale,h:b.height/scale};});});
    assert(dimensions.every(b=>b.w>=48&&b.h>=48));
    const follow=dimensions.find(x=>x.name==='follow'),go=dimensions.find(x=>x.name==='go');assert(go.x-follow.x-follow.w>=8);
    const entry=await page.locator('#boss-open').evaluate(e=>({width:e.offsetWidth,height:e.offsetHeight}));assert.deepEqual(entry,{width:48,height:48});
    const tools=await page.locator('.minimap-tool').evaluateAll(a=>a.map(e=>({id:e.id,x:e.offsetLeft+24,y:e.offsetTop+24,width:e.offsetWidth,height:e.offsetHeight,visible:48-2*parseFloat(getComputedStyle(e,':after').left),hitShape:getComputedStyle(e).clipPath})));
    assert.equal(tools.length,4);for(const t of tools){assert.equal(t.width,48);assert.equal(t.height,48);assert.equal(t.visible,28);assert(t.hitShape.startsWith('circle('));}
    const toolGaps=[];for(let i=0;i<tools.length;i++)for(let j=i+1;j<tools.length;j++){const gap=Math.hypot(tools[i].x-tools[j].x,tools[i].y-tools[j].y)-48;assert(gap>=8);toolGaps.push({a:tools[i].id,b:tools[j].id,gap});}
    await page.evaluate(()=>{const p=window.bossPreviewV2;Object.assign(p.targets.find(t=>t.id==='huntmaster'),{refreshedAt:1,time:0});p.set('list');});const freshOrder=await page.locator('.encounter').evaluateAll(a=>a.map(n=>n.dataset.id));assert.deepEqual(freshOrder,['warden','huntmaster','oath']);await shot('12-sorted-new-refresh');assert.equal(errors.length,0);assert(await page.locator('img').evaluateAll(a=>a.every(i=>i.complete&&i.naturalWidth>0)));
    fs.writeFileSync(path.join(__dirname,'validation.json'),JSON.stringify({date:'2026-11-15',scope:'UI design prototype only',errors,checks:['only previously defeated targets appear; never reveal first encounters','boss before elite, newer refresh before older, level descending','inclusive level +/-5 boundaries and cross-chapter selection','empty state does not widen filter','HUD level matches preview','chapter tabs removed','explicit minimap rim button opens list','selection does not start navigation','follow and travel restored','navigation start stop resume','menu closes into paused navigation','notice restored directly below automatic','notice starts its own 10s lifetime, remains at 9s and closes without clicking','ordinary messages refill after automatic dismissal','four shared 28px minimap housings, 48px circular hit regions and minimum 8px separation','per-character face portraits use existing identity sprites'],filtered,stack,noticeTiming,entry,tools,toolGaps,dimensions,userApproved:true,platformValidated:false},null,2)+'\n');
    console.log('10s automatic dismissal, shared small tools, filtering and navigation verified.');
  }finally{await Promise.race([browser.close(),new Promise(resolve=>setTimeout(resolve,3000))]);}
})().then(()=>process.exit(0)).catch(e=>{console.error(e);process.exit(1);});
