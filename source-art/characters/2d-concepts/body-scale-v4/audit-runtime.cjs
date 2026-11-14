// Focused manual verification against the built game, using existing Playwright.
const {chromium}=require('../../../../src/cocos/node_modules/playwright');
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const {isDeepStrictEqual}=require('node:util');
const root=path.resolve(__dirname,'../../../..'),actor=path.join(root,'src/cocos/assets/resources/flat2d/characters/raphael');
const digest=b=>crypto.createHash('sha256').update(b).digest('hex');
(async()=>{
 const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
 try{
  const context=await browser.newContext({viewport:{width:1280,height:720}}),page=await context.newPage(),errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  await page.goto('http://127.0.0.1:7469/?view=2d&revision=body-scale-v4');
  await page.waitForFunction(()=>globalThis.System);
  await page.evaluate(async()=>{const cc=await System.import('cc');globalThis.__scaleCC=cc;globalThis.__scaleApp=()=>cc.director.getScene()?.getChildByName('ChapterGame')?.getComponent('ChapterGame');});
  await page.waitForFunction(()=>{const a=__scaleApp();return a?.actors?.active.get('player')&&!a.loading&&!a.failure;},undefined,{timeout:60000});
  const source=JSON.parse(fs.readFileSync(path.join(actor,'manifest.json'),'utf8'));
  const live=await page.evaluate(()=>{const asset=__scaleApp().actors.active.get('player').asset;return{manifest:asset.manifest,urls:[...asset.textures].map(([n,t])=>[n,t.image?.nativeUrl])};});
  const manifestMatches=isDeepStrictEqual(live.manifest,source),textures=[];
  for(const name of [...new Set(Object.values(source.actions).flatMap(a=>a.frameImages??[a.image]))]){
   const url=live.urls.find(([n])=>n===name.replace(/\.png$/,''))?.[1];
   if(!url)throw Error('Missing texture '+name);
   const response=await context.request.get(new URL(url,page.url()).href);
   textures.push({name,matches:digest(fs.readFileSync(path.join(actor,name)))===digest(await response.body())});
  }
  const poses=await page.evaluate(()=>{
   const app=__scaleApp(),h=app.actors.active.get('player'),m=h.asset.manifest;
   app.menu='qa';app.enabled=false;app.hud.root.active=false;app.camera.orthoHeight=2.0;app.positionCamera(1);app.flatWorld?.update(app.camera);
   const sample=(key,di,ordinal)=>{
    const dir=m.directions[di],r=app.camera.node.right,u=app.camera.node.up;
    const v=dir==='right'?[r.x,r.z]:dir==='left'?[-r.x,-r.z]:dir==='up'?[u.x,u.z]:[-u.x,-u.z];h.angle=Math.atan2(v[0],v[1]);
    const a=m.actions[key],count=a.frames??1,p=a.phaseStarts?.[ordinal]??(ordinal+.25)/count;
    app.actors.show(h,key,0,p,true,key);
    const name=(a.frameImages?.[ordinal]??a.image).replace(/\.png$/,'');
    const f=m.frameScaleFactors?.[name]?.[h.frame]??1,upp=(a.worldUnitsPerPixel??m.camera?.worldUnitsPerPixel??.008)*f;
    const frame=app.actors.frame(h.asset,a,di,ordinal),w=frame.frame.rect.width,hh=frame.frame.rect.height,o=frame.origin;
    const scaleError=Math.max(Math.abs(h.sprite.scale.x-w*upp),Math.abs(h.sprite.scale.y-hh*upp));
    const anchorError=Math.max(Math.abs(h.sprite.position.x-(w/2-o[0])*upp),Math.abs(h.sprite.position.y-(o[1]-hh/2)*upp));
    return{key,direction:dir,ordinal,actualAction:h.sampledAction,actualOrdinal:h.ordinal,actualDirection:h.direction,factor:f,effectiveUPP:upp,scaleError,anchorError,textureMatches:h.material.getProperty('mainTexture')===h.asset.textures.get(name)};
   };
   globalThis.__scaleSample=sample;
   const mismatches=[],samples=[];
   for(const[key,a]of Object.entries(m.actions))for(let di=0;di<m.directions.length;di++)for(let phase=0;phase<(a.frames??1);phase++){
    const s=sample(key,di,phase);samples.push(s);
    if(s.actualAction!==key||s.actualOrdinal!==phase||s.actualDirection!==di||!s.textureMatches||s.scaleError>1e-5||s.anchorError>1e-5)mismatches.push(s);
   }
   return{actions:Object.keys(m.actions).length,phaseSamples:samples.length,mismatches,samples};
  });
  const captures=[];
  for(const [label,key,phase]of [['standing','explore_idle_W01',0],['held','idle_W01',0],['run','explore_run_W01',4],['attack','attack_sword_W01',1]])for(let di=0;di<4;di++){
   const info=await page.evaluate(({key,phase,di})=>{
    const sample=__scaleSample(key,di,phase),a=__scaleApp(),h=a.actors.active.get('player');a.positionCamera(1);a.flatWorld?.update(a.camera);
    const p=new __scaleCC.Vec3();a.camera.worldToScreen(h.root.worldPosition,p);
    if(!(p.x>0&&p.x<1280&&p.y>0&&p.y<720))throw Error('Ground anchor outside capture viewport');
    return{sample,anchor:[p.x,720-p.y],orthoHeight:a.camera.orthoHeight};
   },{key,phase,di});
   await page.waitForTimeout(80);
   const clip={x:Math.max(0,Math.min(880,Math.round(info.anchor[0]-200))),y:Math.max(0,Math.min(310,Math.round(info.anchor[1]-350))),width:400,height:410};
   const name=`game-${label}-${source.directions[di]}.png`;
   await page.screenshot({path:path.join(__dirname,name),clip});captures.push({name,label,direction:source.directions[di],...info,clip});
  }
  const report={revision:live.manifest.bodyScaleCalibration,manifestMatches,textures,poses,captures,errors};
  fs.writeFileSync(path.join(__dirname,'runtime-audit.json'),JSON.stringify(report,null,2));
  const texturesMatch=textures.every(t=>t.matches);
  console.log(JSON.stringify({manifestMatches,texturesMatch,textures:textures.length,actions:poses.actions,phaseSamples:poses.phaseSamples,mismatches:poses.mismatches,errors,captures:captures.length}));
  if(!manifestMatches||!texturesMatch||poses.mismatches.length||errors.length)process.exitCode=1;
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
