// Actual frozen Cocos UI: cold native-image requests, normal menu actions and input.
const fs=require('node:fs'),path=require('node:path'),http=require('node:http'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'../../..'),cocos=path.join(root,'src/cocos');
const {chromium,devices}=require(path.join(cocos,'node_modules/playwright'));
const proof=JSON.parse(fs.readFileSync(path.join(__dirname,'snapshot.json'),'utf8')),build=path.resolve(root,proof.servedSnapshot);
const sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
if(sha(path.join(build,proof.mainFile))!==proof.compiledSha256||sha(proof.copyManifest)!==proof.copyManifestSha256)throw Error('Frozen proof mismatch');
const onlyPhone=process.argv.includes('--only-phone'),output=path.join(__dirname,onlyPhone?'native-qa-phone-r3':'native-qa');fs.mkdirSync(output,{recursive:true});
const prep=fs.readFileSync(path.join(cocos,'assets/scripts/app/PreparationResources.ts'),'utf8');
const skins=Function('return '+prep.match(/const workshopChrome=([\s\S]*?);\s*const workshopPage/)[1])();
const uuids=skins.map(id=>JSON.parse(fs.readFileSync(path.join(cocos,'assets/resources/ui/quiet-bronze',id+'.png.meta'),'utf8')).uuid);
const mime={'.html':'text/html','.js':'text/javascript','.json':'application/json','.png':'image/png','.jpg':'image/jpeg','.wasm':'application/wasm','.css':'text/css'};
const server=http.createServer((req,res)=>{const p=decodeURIComponent(new URL(req.url,'http://127.0.0.1').pathname),file=path.resolve(build,'.'+(p==='/'?'/index.html':p));if(!file.startsWith(build+path.sep)||!fs.existsSync(file)||!fs.statSync(file).isFile()){res.writeHead(404).end();return;}res.setHeader('Content-Type',mime[path.extname(file)]||'application/octet-stream');res.setHeader('Cache-Control','no-store');fs.createReadStream(file).pipe(res);});
const pause=ms=>new Promise(r=>setTimeout(r,ms));
async function waitHost(test,ms=30000){const until=Date.now()+ms;while(!test()){if(Date.now()>until)throw Error('Timed out waiting for delayed workshop image requests');await pause(40);}}
async function ready(page,name){await page.waitForFunction(name=>{const a=findForgeApp();function find(n){return n.name===name?n:n.children.map(find).find(Boolean);}return !a.preparingPage&&!!find(a.hud.modal);},name,{timeout:90000});await page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));}
async function inspect(page){return page.evaluate(async()=>{
 const cc=await System.import('cc'),a=findForgeApp(),all=[];function visit(n){all.push(n);n.children.forEach(visit);}visit(a.hud.modal);
 const node=name=>all.find(n=>n.name===name),room=node('ForgeRoom'),weapon=node('ForgeWeaponArt'),scale=innerHeight/a.hud.height;
 const rect=n=>{if(!n)return null;const b=n.getComponent(cc.UITransform)?.getBoundingBoxToWorld();return b?{x:(b.x+a.hud.width/2)*scale,y:innerHeight-(b.y+b.height+a.hud.height/2)*scale,width:b.width*scale,height:b.height*scale}:null;};
 const labels=(room?.children??[]).map(n=>n.getComponent(cc.Label)).filter(Boolean),title=labels.find(l=>/\+\d/.test(l.string)),quality=labels.find(l=>l.string.includes(' · '));
 const art=weapon?.children.find(n=>n.name.startsWith('EquipmentIconFrame:'))??weapon?.children[0],titleBox=rect(title?.node),qualityBox=rect(quality?.node),artBox=rect(art);
 const plates=all.filter(n=>n.name.startsWith('Skin:ui/quiet-bronze/rpg-forge-')||n.name==='Skin:ui/quiet-bronze/rpg-anvil-v2').map(n=>({name:n.name,loaded:!!n.getComponent(cc.Sprite)?.spriteFrame?.isValid,active:n.activeInHierarchy}));
 const tabs=all.filter(n=>/^(forge-item:|gems:|forge-targets:)/.test(n.name)&&n.parent===room?.parent?.parent).map(n=>({action:n.name,rect:rect(n)}));
 const headerTabs=all.filter(n=>/^(forge-item:|gems:|forge-targets:)/.test(n.name)&&n.children.some(c=>c.name.includes('rpg-forge-tab-'))).map(n=>({action:n.name,rect:rect(n),skinReady:n.children.some(c=>c.name.includes('rpg-forge-tab-')&&!!c.getComponent(cc.Sprite)?.spriteFrame?.isValid)}));
 return {menu:a.menu,preparing:a.preparingPage,appEnabled:a.enabled,gamePaused:cc.game.isPaused(),resources:a.preparationResources.inspect(),forgePresent:!!node('ForgeWorkshop'),title:title?{string:title.string,font:title.fontSize,lineHeight:title.lineHeight,wrap:title.enableWrapText,rect:titleBox}:null,quality:quality?{string:quality.string,rect:qualityBox}:null,art:artBox,titleArtGap:titleBox&&artBox?titleBox.x-artBox.x-artBox.width:null,qualityArtGap:qualityBox&&artBox?qualityBox.x-artBox.x-artBox.width:null,titleQualityGap:titleBox&&qualityBox?qualityBox.y-titleBox.y-titleBox.height:null,plates,headerTabs,level:a.session.state.progression.level,inventory:JSON.stringify(a.session.state.inventory),equipment:JSON.stringify(a.session.state.equipment)};
 });}
async function clickNode(page,name,touch){
 const target=()=>page.evaluate(async name=>{const cc=await System.import('cc'),a=findForgeApp();function find(n){return n.name===name?n:n.children.map(find).find(Boolean);}const n=find(a.hud.modal);if(!n)throw Error('Missing actual UI action '+name);const s=innerHeight/a.hud.height,rect=n=>{const t=n.getComponent(cc.UITransform),p=t.convertToWorldSpaceAR(new cc.Vec3(-t.width*t.anchorPoint.x,-t.height*t.anchorPoint.y)),q=t.convertToWorldSpaceAR(new cc.Vec3(t.width*(1-t.anchorPoint.x),t.height*(1-t.anchorPoint.y)));return{x:(p.x+a.hud.width/2)*s,y:innerHeight-(q.y+a.hud.height/2)*s,width:(q.x-p.x)*s,height:(q.y-p.y)*s};};let ancestor=n.parent;while(ancestor&&ancestor.name!=='Viewport')ancestor=ancestor.parent;const b=rect(n);return{x:b.x+b.width/2,y:b.y+b.height/2,viewport:ancestor?rect(ancestor):null};},name);
 let r=await target(),scrolled=false;
 if(r.viewport&&(r.y>r.viewport.y+r.viewport.height-8||r.y<r.viewport.y+8)){
  const p=r.viewport,cx=p.x+p.width/2,y1=p.y+p.height-12,y2=p.y+12;
  if(touch){const cdp=await page.context().newCDPSession(page);await cdp.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x:cx,y:y1,id:1}]});for(let i=1;i<=10;i++){await cdp.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x:cx,y:y1+(y2-y1)*i/10,id:1}]});await pause(16);}await cdp.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});await cdp.detach();}
  else{await page.mouse.move(cx,(y1+y2)/2);await page.mouse.wheel(0,160);}
  await pause(250);r=await target();scrolled=true;
 }
 if(r.viewport&&(r.y>r.viewport.y+r.viewport.height||r.y<r.viewport.y))throw Error('UI action is still clipped after real scrolling: '+name);
 if(touch)await page.touchscreen.tap(r.x,r.y);else await page.mouse.click(r.x,r.y);return{...r,scrolled};
}
async function scenario(browser,label,options,cancel){
 const context=await browser.newContext(options),page=await context.newPage(),errors=[],consoleErrors=[],held=[],delayed=[];let delay=false;
 page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')consoleErrors.push(m.text());});
 const cdp=await context.newCDPSession(page);await cdp.send('Network.enable');await cdp.send('Network.setCacheDisabled',{cacheDisabled:true});
 await page.route('**/*',async route=>{const url=route.request().url();if(delay&&url.includes('/native/')&&uuids.some(id=>url.includes(id))){delayed.push(url);await new Promise(r=>held.push(r));}try{await route.continue();}catch{}});
 const result={label,viewport:options.viewport,dpr:options.deviceScaleFactor,cacheDisabled:true,cancelDuringLoad:cancel,errors,consoleErrors,delayed};
 try{
  await page.goto('http://127.0.0.1:'+server.address().port+'/?view=2d&player=3d',{waitUntil:'load'});
  await page.waitForFunction(()=>!!globalThis.System,undefined,{timeout:60000});
  await page.evaluate(async()=>{const cc=await System.import('cc');globalThis.findForgeApp=()=>{function find(n){return n?.getComponent('ChapterGame')||n?.children.map(find).find(Boolean);}return find(cc.director.getScene());};});
  await page.waitForFunction(()=>{const a=findForgeApp();return a?.session&&a.actors&&!a.loading&&a.platform.auth.ready;},undefined,{timeout:120000});
  result.initial=await inspect(page);delay=true;await page.evaluate(()=>findForgeApp().click('forge'));await waitHost(()=>delayed.length>0);
  await pause(250);result.pending=await inspect(page);await page.screenshot({path:path.join(output,label+'-cold-pending.png')});
  if(!result.pending.preparing||result.pending.forgePresent)throw Error('Partial workshop became visible before its skin requests completed');
  if(cancel)await page.evaluate(()=>findForgeApp().click('close'));
  delay=false;held.splice(0).forEach(r=>r());
  if(cancel){await pause(300);result.cancelled=await inspect(page);if(result.cancelled.forgePresent)throw Error('Cancelled skin completion reopened the workshop');await page.evaluate(()=>findForgeApp().click('forge'));}
  await ready(page,'ForgeWorkshop');result.firstComplete=await inspect(page);await page.screenshot({path:path.join(output,label+'-cold-complete.png')});
  if(!result.firstComplete.resources.workshopReady||result.firstComplete.plates.some(s=>!s.loaded))throw Error('Incomplete first workshop skin state');
  // Select the real initially owned staff. Its unchanged square frame exercises
  // the same armour/title bounds without granting items or changing gameplay.
  result.squareSelectionInput=await clickNode(page,'forge-item:W11',!!options.hasTouch);await page.waitForFunction(()=>findForgeApp().menu==='forge-item:W11');await ready(page,'ForgeWorkshop');result.squareArt=await inspect(page);await page.screenshot({path:path.join(output,label+'-square-item.png')});
  if(result.squareArt.titleArtGap<0||result.squareArt.qualityArtGap<0||result.squareArt.titleQualityGap<-.1)throw Error('Equipment/name/quality rectangles overlap');
  if(options.hasTouch&&result.squareArt.headerTabs.some(t=>t.rect.height<47.9||t.rect.width<47.9))throw Error('Workshop touch target below48 logical pixels');
  const originalTitle=await page.evaluate(async()=>{const cc=await System.import('cc'),a=findForgeApp();function find(n){return n.name==='ForgeRoom'?n:n.children.map(find).find(Boolean);}const l=find(a.hud.modal).children.map(n=>n.getComponent(cc.Label)).find(l=>l&&/\+\d/.test(l.string));const original=l.string;l.string='远古守望者的精钢护盔 +0';return original;});
  await pause(120);result.longTitle=await inspect(page);await page.screenshot({path:path.join(output,label+'-long-title-two-lines.png')});
  await page.evaluate(async value=>{const cc=await System.import('cc'),a=findForgeApp();function find(n){return n.name==='ForgeRoom'?n:n.children.map(find).find(Boolean);}const l=find(a.hud.modal).children.map(n=>n.getComponent(cc.Label)).find(l=>l&&/\+\d/.test(l.string));l.string=value;},originalTitle);
  await clickNode(page,'gems:W11',!!options.hasTouch);await ready(page,'GemWorkshop');result.gems=await inspect(page);await page.screenshot({path:path.join(output,label+'-gems.png')});
  await clickNode(page,'forge-targets:W11',!!options.hasTouch);await ready(page,'ForgeServices');result.transfer=await inspect(page);
  await clickNode(page,'forge-item:W11',!!options.hasTouch);await ready(page,'ForgeWorkshop');result.returned=await inspect(page);
  if(options.hasTouch)await page.touchscreen.tap(4,options.viewport.height/2);else await page.mouse.click(4,options.viewport.height/2);
  await page.waitForFunction(()=>{const a=findForgeApp();function find(n){return n.name==='ForgeWorkshop'||n.children.some(find);}return !find(a.hud.modal);});
  await page.evaluate(()=>findForgeApp().click('forge-item:W11'));await ready(page,'ForgeWorkshop');result.reopened=await inspect(page);await page.screenshot({path:path.join(output,label+'-reopened.png')});
  if(result.reopened.plates.some(s=>!s.loaded)||result.reopened.inventory!==result.initial.inventory||result.reopened.equipment!==result.initial.equipment||result.reopened.level!==result.initial.level)throw Error('Reopen changed inventory/equipment or lost skins');
  result.pass=errors.length===0;return result;
 }catch(error){result.failure=String(error);await page.screenshot({path:path.join(output,label+'-failure.png')}).catch(()=>{});return result;}
 finally{delay=false;held.splice(0).forEach(r=>r());fs.writeFileSync(path.join(output,label+'.json'),JSON.stringify(result,null,2));await context.close();}
}
(async()=>{await new Promise(r=>server.listen(0,'127.0.0.1',r));const browser=await chromium.launch({headless:true,args:['--enable-webgl','--enable-unsafe-swiftshader','--use-angle=swiftshader','--mute-audio']});const results=[];try{
 const mobile={...devices['iPhone 14 landscape'],viewport:{width:844,height:390},deviceScaleFactor:3};
 if(!onlyPhone){results.push(await scenario(browser,'desktop',{viewport:{width:1280,height:636},deviceScaleFactor:1},false));console.log('desktop',results.at(-1).pass,results.at(-1).failure??'');}
 results.push(await scenario(browser,'iphone14',mobile,true));console.log('iphone14',results.at(-1).pass,results.at(-1).failure??'');
 const report={compiledSha256:proof.compiledSha256,servedSnapshot:build,copyManifestSha256:proof.copyManifestSha256,productionUnchanged:true,actualGameContinued:true,notes:['Normal fresh test journey; no max shortcut, training, clock/camera edits or inventory grants.','Long-title screenshot changes only the Label string temporarily as an explicit layout stress fixture; actual item/equipment state is checked unchanged.'],results};fs.writeFileSync(path.join(output,'report.json'),JSON.stringify(report,null,2));if(results.some(r=>!r.pass))process.exitCode=1;
 }finally{await browser.close();server.close();}})().catch(error=>{console.error(error);server.close();process.exitCode=1;});
