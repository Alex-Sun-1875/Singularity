// Manual post-build asset/pose audit with the project's existing Playwright.
// No extra test scaffolding, dependencies, model calls or cloud image requests.
const {chromium}=require('../../../../src/cocos/node_modules/playwright');
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const {isDeepStrictEqual}=require('node:util');
const root=path.resolve(__dirname,'../../../..');
const actor=path.join(root,'src/cocos/assets/resources/flat2d/characters/raphael');
const digest=b=>crypto.createHash('sha256').update(b).digest('hex');
(async()=>{
 const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
 try{
  const context=await browser.newContext({viewport:{width:1280,height:720}}),page=await context.newPage(),errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  await page.goto('http://127.0.0.1:7469/?view=2d&revision=qwen21-unified-v3');
  await page.waitForFunction(()=>globalThis.System);
  await page.evaluate(async()=>{const cc=await System.import('cc');globalThis.__appearanceApp=()=>cc.director.getScene()?.getChildByName('ChapterGame')?.getComponent('ChapterGame');});
  await page.waitForFunction(()=>{const a=__appearanceApp();return a?.actors?.active.get('player')&&!a.loading&&!a.failure;},undefined,{timeout:60000});
  const source=JSON.parse(fs.readFileSync(path.join(actor,'manifest.json'),'utf8'));
  const live=await page.evaluate(()=>{const a=__appearanceApp(),asset=a.actors.active.get('player').asset;return{manifest:asset.manifest,urls:[...asset.textures].map(([n,t])=>[n,t.image?.nativeUrl])};});
  const manifestMatches=isDeepStrictEqual(live.manifest,source);
  const names=[...new Set(Object.values(source.actions).flatMap(a=>a.frameImages??[a.image]))];
  const textures=[];
  for(const name of names){
   const url=live.urls.find(([n])=>n===name.replace(/\.png$/,''))?.[1];
   if(!url)throw Error('Missing texture '+name);
   const response=await context.request.get(new URL(url,page.url()).href),bytes=await response.body();
   textures.push({name,sourceSHA256:digest(fs.readFileSync(path.join(actor,name))),runtimeSHA256:digest(bytes)});
  }
  const poses=await page.evaluate(()=>{
   const app=__appearanceApp(),h=app.actors.active.get('player'),m=h.asset.manifest;
   app.menu='qa';app.enabled=false;app.hud.root.active=false;app.camera.orthoHeight=2.2;
   const sample=(key,di,ordinal)=>{
    const dir=m.directions[di],r=app.camera.node.right,u=app.camera.node.up;
    const v=dir==='right'?[r.x,r.z]:dir==='left'?[-r.x,-r.z]:dir==='up'?[u.x,u.z]:[-u.x,-u.z];
    h.angle=Math.atan2(v[0],v[1]);
    const a=m.actions[key],count=a.frames??1,p=a.phaseStarts?.[ordinal]??(ordinal+.25)/count;
    app.actors.show(h,key,0,p,true,key);
    const name=(a.frameImages?.[ordinal]??a.image).replace(/\.png$/,'');
    return {key,direction:dir,ordinal,actualAction:h.sampledAction,actualOrdinal:h.ordinal,actualDirection:h.direction,textureMatches:h.material.getProperty('mainTexture')===h.asset.textures.get(name)};
   };
   globalThis.__appearanceSample=sample;
   const mismatches=[];let count=0;
   for(const [key,a] of Object.entries(m.actions))for(let di=0;di<m.directions.length;di++)for(let phase=0;phase<(a.frames??1);phase++){
    const s=sample(key,di,phase);count++;
    if(s.actualAction!==key||s.actualOrdinal!==phase||s.actualDirection!==di||!s.textureMatches)mismatches.push(s);
   }
   return{actions:Object.keys(m.actions).length,phaseSamples:count,mismatches};
  });
  for(const [name,key,phase] of [['standing','explore_idle_W01',0],['attack','attack_sword_W01',1],['run','explore_run_W01',4],['spell','spell',0]]){
   await page.evaluate(({key,phase})=>{__appearanceSample(key,1,phase);const a=__appearanceApp();a.positionCamera(1);a.flatWorld?.update(a.camera);},{key,phase});
   await page.waitForTimeout(120);await page.screenshot({path:path.join(__dirname,'game-'+name+'.png')});
  }
  const report={manifestMatches,textures,poses,errors,revision:live.manifest.localQwenInstall};
  fs.writeFileSync(path.join(__dirname,'runtime-audit.json'),JSON.stringify(report,null,2));
  const texturesMatch=textures.every(t=>t.sourceSHA256===t.runtimeSHA256);
  console.log(JSON.stringify({manifestMatches,texturesMatch,textures:textures.length,actions:poses.actions,phaseSamples:poses.phaseSamples,mismatches:poses.mismatches,errors},null,2));
  if(!manifestMatches||!texturesMatch||poses.mismatches.length||errors.length)process.exitCode=1;
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
