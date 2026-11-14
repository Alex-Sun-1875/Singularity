// Synthetic view fixtures verify panel presentation and lifecycle in real Cocos.
// Story transitions, random results, resources, and saves need functional tests.
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const isolated=process.env.DICE_PANEL_ISOLATED==='1';
const panelSource=isolated?require('typescript').transpileModule(fs.readFileSync(path.resolve(__dirname,'../assets/scripts/features/dice/runtime/DicePanel.ts'),'utf8'),{compilerOptions:{module:require('typescript').ModuleKind.CommonJS,target:require('typescript').ScriptTarget.ES2020}}).outputText:null;

(async()=>{
 const out=path.resolve(__dirname,'../test-results');fs.mkdirSync(out,{recursive:true});
 const browser=await chromium.launch({executablePath:process.env.CHROME_PATH||'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true,args:['--enable-unsafe-swiftshader']});
 try {
  const page=await browser.newPage({viewport:{width:1280,height:720}}),errors=[];
  page.on('pageerror',error=>errors.push(String(error)));
  await page.goto(process.env.CHAPTER_URL||'http://localhost:7456/',{waitUntil:'domcontentloaded'});
  await page.waitForFunction(()=>globalThis.__chapter?.inspect().ready,undefined,{timeout:60000});
  // Creator's fixed design-device preview crops a narrow browser window.
  // Use its webpage-fullscreen option, then set the real engine window size.
  if(await page.locator('#view-select').isVisible()){
   await page.locator('#view-select').click();await page.locator('li[data-device="WebpageFullScreen"]').click();
  }
  await page.evaluate(async()=>{const engine=await System.import('cc');engine.screen.windowSize=new engine.Size(innerWidth,innerHeight);});
  await page.waitForTimeout(100);
  const lifecycle=await page.evaluate(source=>{
   const app=globalThis.__chapter.app;
   if(!app.dicePanel&&source){const module={exports:{}};new Function('require','module','exports',source)(id=>{if(id==='cc')return {...cc,UITransform:cc.UITransform||cc.UITransformComponent};throw Error(`Unexpected dependency ${id}`);},module,module.exports);app.dicePanel=new module.exports.DicePanel(app.hud);}
   const dice=app.dicePanel;
   if(!dice)throw Error('ChapterGame must expose the connected DicePanel as app.dicePanel');
   app.enabled=false;
   const base={id:'visual:advantage',title:'说服守卫放行',prompt:'抓住守卫迟疑的一瞬，让他相信你们是前来送药的旅人。',skillLabel:'游说',abilityLabel:'魅力',dc:15,mode:'advantage',modifiers:[{label:'魅力',value:2},{label:'熟练',value:2},{label:'旅途线索',value:1}],help:{label:'伊芙琳的鼓舞',enabled:true},roll:null,attempt:0,inspiration:2,canReroll:false,canCancel:true,successText:'守卫移开长矛。你们获得了通往北岭的道路。',failureText:'守卫握紧长矛，但另一条道路仍在等待探索。',chance:.84};
   const all=n=>[n,...n.children.flatMap(all)];
   dice.clear();dice.show(base);
   const initiallyBusy=dice.busy;
   const rolled={...base,attempt:1,canReroll:true,canCancel:false,roll:{attempt:1,faces:[7,17],kept:17,keptIndex:1,bonus:5,assist:1,total:23,success:true,critical:null}};
   dice.show(rolled);const startsBusy=dice.busy;
   const countBefore=all(app.hud.modal).length;
   for(let i=0;i<20;i++)dice.update(.02);
   const countAfter=all(app.hud.modal).length;
   dice.show({...rolled});dice.update(.7);
   const completed=!dice.busy;
   dice.clear();dice.show(rolled);const savedResultBusy=dice.busy;
   const faces=all(app.hud.modal).filter(n=>n.name.startsWith('DieFace-')).map(n=>n.getComponent(cc.Label)?.string);
   const oldRoot=app.hud.modal.children[0];
   app.hud.show('所有权检查','此界面不属于骰子面板。',[{label:'返回',action:'close'}]);
   dice.clear();const preservedOtherModal=app.hud.modal.children.length>0;
   dice.show(rolled);
   globalThis.__diceVisual={base,rolled,all};
   return {initiallyBusy,startsBusy,countBefore,countAfter,completed,savedResultBusy,faces,preservedOtherModal,oldRootValid:cc.isValid(oldRoot,true)};
  },panelSource);
  assert.equal(lifecycle.initiallyBusy,false);
  assert.equal(lifecycle.startsBusy,true,'a newly committed roll must animate and block input');
  assert.equal(lifecycle.countAfter,lifecycle.countBefore,'rolling must reuse nodes');
  assert.equal(lifecycle.completed,true,'showing the same roll must not restart its animation');
  assert.equal(lifecycle.savedResultBusy,false,'loading a saved result must settle immediately');
  assert.deepEqual(lifecycle.faces,['7','17']);
  assert.equal(lifecycle.preservedOtherModal,true,'clear must leave a later menu owned by Hud intact');
  await page.screenshot({path:path.join(out,'dice-advantage-success-1280.png')});
  await page.evaluate(()=>{const {base}=globalThis.__diceVisual;globalThis.__chapter.app.dicePanel.show({...base,id:'visual:critical',help:null,mode:'normal',roll:{attempt:1,faces:[20],kept:20,keptIndex:0,bonus:5,assist:0,total:25,success:true,critical:'success'},attempt:1,canCancel:false,canReroll:false});});
  await page.screenshot({path:path.join(out,'dice-natural20-1280.png')});
  await page.setViewportSize({width:915,height:412});
  await page.waitForTimeout(150);
  const mobile=await page.evaluate(async()=>{const engine=await System.import('cc');engine.screen.windowSize=new engine.Size(innerWidth,innerHeight);const app=globalThis.__chapter.app,{base}=globalThis.__diceVisual;app.hud.resize();const fixture={...base,id:'visual:mobile',mode:'disadvantage',help:null,dc:18,roll:{attempt:1,faces:[14,1],kept:1,keptIndex:1,bonus:5,assist:0,total:6,success:false,critical:'failure'},attempt:1,canReroll:true,canCancel:false};globalThis.__diceVisual.mobile=fixture;app.dicePanel.show(fixture);const canvas=document.querySelector('#GameCanvas'),rect=canvas.getBoundingClientRect();return {width:canvas.width,height:canvas.height,cssWidth:rect.width,cssHeight:rect.height,hudWidth:app.hud.width,hudHeight:app.hud.height};});
  assert.ok(Math.abs(mobile.width/mobile.height-915/412)<.01,'Cocos canvas must match the physical landscape aspect ratio');
  await page.screenshot({path:path.join(out,'dice-disadvantage-natural1-915.png')});
  await page.setViewportSize({width:390,height:844});await page.waitForTimeout(150);
  const portrait=await page.evaluate(async()=>{
   const engine=await System.import('cc');engine.screen.windowSize=new engine.Size(innerWidth,innerHeight);
   const app=globalThis.__chapter.app,{all,mobile,base}=globalThis.__diceVisual;app.hud.resize();
   const before=JSON.stringify(app.session.state);app.dicePanel.show(mobile);
   const inspect=()=>{const nodes=all(app.hud.modal);return {invalid:nodes.flatMap(n=>{const transform=n.getComponent(engine.UITransform);return transform&&(!Number.isFinite(transform.width)||!Number.isFinite(transform.height)||transform.width<0||transform.height<0)?[{name:n.name,width:transform.width,height:transform.height}]:[];}),faces:nodes.filter(n=>n.name.startsWith('DieFace-')).map(n=>n.getComponent(engine.Label).string),actions:nodes.filter(n=>n.name.startsWith('dice:')).map(n=>n.name),labels:nodes.flatMap(n=>{const label=n.getComponent(engine.Label);return label?[label.string]:[];})};};
   const rolled=inspect();app.dicePanel.show({...base,id:'visual:portrait-unrolled'});const unrolled=inspect();
   app.dicePanel.show(mobile);return {width:app.hud.width,height:app.hud.height,rolled,unrolled,stateUnchanged:before===JSON.stringify(app.session.state)};
  });
  await page.screenshot({path:path.join(out,'dice-rotate-pending-390.png')});
  assert.deepEqual(portrait.rolled.invalid,[],'portrait dice subtree must never create negative or nonfinite UITransform sizes');
  assert.deepEqual(portrait.unrolled.invalid,[]);
  assert.deepEqual(portrait.rolled.faces,['14','1'],'portrait must retain both actual dice faces');
  assert.deepEqual(portrait.rolled.actions,[],'rotation prompt must not submit or reroll a pending result');
  assert.deepEqual(portrait.unrolled.actions,['dice:cancel'],'an unrolled portrait check can only cancel');
  assert.ok(portrait.rolled.labels.some(text=>text.includes('请旋转到横屏')));
  assert.ok(portrait.rolled.labels.some(text=>text.includes('灵感')&&text.includes('2')));
  assert.equal(portrait.stateUnchanged,true);
  await page.setViewportSize({width:915,height:412});await page.waitForTimeout(150);
  const restored=await page.evaluate(async()=>{const engine=await System.import('cc');engine.screen.windowSize=new engine.Size(innerWidth,innerHeight);const app=globalThis.__chapter.app,{all,mobile}=globalThis.__diceVisual;app.hud.resize();app.dicePanel.show(mobile);const nodes=all(app.hud.modal);return {busy:app.dicePanel.busy,faces:nodes.filter(n=>n.name.startsWith('DieFace-')).map(n=>n.getComponent(engine.Label).string),reroll:nodes.find(n=>n.name==='dice:reroll')?.getComponentInChildren(engine.Label)?.string};});
  assert.deepEqual(restored.faces,['14','1'],'rotating back must restore the existing result without drawing again');
  assert.equal(restored.busy,false,'a settled result must not restart its animation after rotation');
  assert.match(restored.reroll,/1\s*灵感重掷.*余\s*2/,'reroll must distinguish its fixed one-point cost from the remaining balance');
  await page.evaluate(()=>{const {base,rolled}=globalThis.__diceVisual,dice=globalThis.__chapter.app.dicePanel;dice.show({...base,id:'visual:rotate-animation'});dice.show({...rolled,id:'visual:rotate-animation'});dice.update(.35);});
  await page.setViewportSize({width:390,height:844});await page.waitForTimeout(100);
  const portraitAnimation=await page.evaluate(async()=>{const engine=await System.import('cc');engine.screen.windowSize=new engine.Size(innerWidth,innerHeight);const app=globalThis.__chapter.app;app.hud.resize();app.dicePanel.update(.2);return app.dicePanel.busy;});
  assert.equal(portraitAnimation,true,'rotating mid-roll must preserve the active animation');
  await page.setViewportSize({width:915,height:412});await page.waitForTimeout(100);
  const resumedAnimation=await page.evaluate(async()=>{const engine=await System.import('cc');engine.screen.windowSize=new engine.Size(innerWidth,innerHeight);const app=globalThis.__chapter.app,{all}=globalThis.__diceVisual;app.hud.resize();app.dicePanel.update(0);app.dicePanel.update(.64);const beforeEnd=app.dicePanel.busy;app.dicePanel.update(.02);return {beforeEnd,completed:!app.dicePanel.busy,faces:all(app.hud.modal).filter(n=>n.name.startsWith('DieFace-')).map(n=>n.getComponent(engine.Label).string)};});
  assert.equal(resumedAnimation.beforeEnd,true);
  assert.equal(resumedAnimation.completed,true,'rotation must preserve elapsed animation time rather than restarting');
  assert.deepEqual(resumedAnimation.faces,['7','17']);
  const destruction=await page.evaluate(async()=>{const app=globalThis.__chapter.app,old=[...app.hud.modal.children];app.dicePanel.clear();await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));return {modalChildren:app.hud.modal.children.length,alive:old.filter(n=>cc.isValid(n,true)).length,busy:app.dicePanel.busy};});
  assert.deepEqual(destruction,{modalChildren:0,alive:0,busy:false});
  assert.deepEqual(errors,[],'panel must render without runtime errors');
  console.log(JSON.stringify({mode:isolated?'isolated panel with real Cocos/Hud APIs':'connected ChapterGame DicePanel',lifecycle,mobile,portrait,restored,portraitAnimation,resumedAnimation,destruction,screenshots:out},null,2));
 } finally {await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
