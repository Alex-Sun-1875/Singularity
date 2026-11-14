// Manual verification against the built game, using the existing Playwright.
// Run only after installing the reviewed candidate and rebuilding its assets.
const {chromium}=require('../../../../src/cocos/node_modules/playwright');
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const {isDeepStrictEqual}=require('node:util');
const root=path.resolve(__dirname,'../../../..');
const actor=path.join(root,'src/cocos/assets/resources/flat2d/characters/raphael');
const digest=b=>crypto.createHash('sha256').update(b).digest('hex');
const imageName=name=>name.replace(/\\/g,'/').replace(/^\.\//,'').replace(/\.(png|webp|jpg|jpeg)$/i,'');
const capturesToMake=[
 ['standing','explore_idle_W01',0],
 ['held','idle_W01',0],
 ['attack-p0','attack_sword_W01',0],
 ['attack-p1','attack_sword_W01',1],
 ['attack-p3','attack_sword_W01',3],
 ['walk','walk_W01',1],
 ['run','explore_run_W01',4],
 ['spell','spell',1],
 ['death','death',1],
];

(async()=>{
 const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
 try{
  const context=await browser.newContext({viewport:{width:1280,height:720}}),page=await context.newPage(),errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  await page.goto('http://127.0.0.1:7469/?view=2d&revision=attack-identity-v5');
  await page.waitForFunction(()=>globalThis.System);
  await page.evaluate(async()=>{
   const cc=await System.import('cc');globalThis.__identityCC=cc;
   globalThis.__identityApp=()=>cc.director.getScene()?.getChildByName('ChapterGame')?.getComponent('ChapterGame');
  });
  await page.waitForFunction(()=>{const app=__identityApp();return app?.actors?.active.get('player')&&!app.loading&&!app.failure;},undefined,{timeout:60000});
  const sourceBytes=fs.readFileSync(path.join(actor,'manifest.json'));
  const source=JSON.parse(sourceBytes.toString('utf8'));
  const live=await page.evaluate(()=>{
   const asset=__identityApp().actors.active.get('player').asset;
   return{manifest:asset.manifest,urls:[...asset.textures].map(([name,texture])=>[name,texture.image?.nativeUrl])};
  });
  const manifestMatches=isDeepStrictEqual(live.manifest,source),textures=[];
  const manifestHashes={source:digest(sourceBytes),liveCanonical:digest(Buffer.from(JSON.stringify(live.manifest))),sourceCanonical:digest(Buffer.from(JSON.stringify(source)))};
  const names=[...new Set(Object.values(source.actions).flatMap(action=>action.frameImages??[action.image??source.image]))];
  for(const name of names){
   const url=live.urls.find(([n])=>n===imageName(name))?.[1];
   if(!url)throw Error('Missing texture '+name);
   const response=await context.request.get(new URL(url,page.url()).href);
   if(!response.ok())throw Error('Texture fetch failed '+name+' HTTP '+response.status());
   const sourceSHA256=digest(fs.readFileSync(path.join(actor,name))),liveSHA256=digest(await response.body());
   textures.push({name,sourceSHA256,liveSHA256,matches:sourceSHA256===liveSHA256});
  }
  const poses=await page.evaluate(()=>{
   const app=__identityApp(),holder=app.actors.active.get('player'),manifest=holder.asset.manifest;
   app.menu='qa';app.enabled=false;app.hud.root.active=false;app.camera.orthoHeight=2.0;app.positionCamera(1);app.flatWorld?.update(app.camera);
   const sample=(key,di,ordinal)=>{
    const direction=manifest.directions[di],right=app.camera.node.right,up=app.camera.node.up;
    const v=direction==='right'?[right.x,right.z]:direction==='left'?[-right.x,-right.z]:direction==='up'?[up.x,up.z]:[-up.x,-up.z];
    holder.angle=Math.atan2(v[0],v[1]);
    const action=manifest.actions[key],count=action.frameIndices?.length??action.frames??1;
    const progress=action.phaseStarts?.[ordinal]??(ordinal+.25)/count;
    app.actors.show(holder,key,0,progress,true,key);
    const name=(action.frameImages?.[ordinal]??action.image??manifest.image).replace(/\\/g,'/').replace(/^\.\//,'').replace(/\.(png|webp|jpg|jpeg)$/i,'');
    const factor=manifest.frameScaleFactors?.[name]?.[holder.frame]??1;
    const upp=(action.worldUnitsPerPixel??manifest.camera?.worldUnitsPerPixel??.008)*factor;
    const frame=app.actors.frame(holder.asset,action,di,ordinal),width=frame.frame.rect.width,height=frame.frame.rect.height,origin=frame.origin;
    const scaleError=Math.max(Math.abs(holder.sprite.scale.x-width*upp),Math.abs(holder.sprite.scale.y-height*upp));
    const anchorError=Math.max(Math.abs(holder.sprite.position.x-(width/2-origin[0])*upp),Math.abs(holder.sprite.position.y-(origin[1]-height/2)*upp));
    return{key,direction,ordinal,physicalIndex:holder.frame,image:name,
     actualAction:holder.sampledAction,actualOrdinal:holder.ordinal,actualDirection:holder.direction,
     factor,effectiveUPP:upp,origin,rect:[frame.frame.rect.x,frame.frame.rect.y,width,height],
     scaleError,anchorError,textureMatches:holder.material.getProperty('mainTexture')===holder.asset.textures.get(name)};
   };
   globalThis.__identitySample=sample;
   const mismatches=[],samples=[];
   for(const[key,action]of Object.entries(manifest.actions))for(let di=0;di<manifest.directions.length;di++)for(let phase=0;phase<(action.frameIndices?.length??action.frames??1);phase++){
    const result=sample(key,di,phase);samples.push(result);
    if(result.actualAction!==key||result.actualOrdinal!==phase||result.actualDirection!==di||!result.textureMatches||!Number.isFinite(result.effectiveUPP)||result.effectiveUPP<=0||result.scaleError>1e-5||result.anchorError>1e-5)mismatches.push(result);
   }
   return{actions:Object.keys(manifest.actions).length,phaseSamples:samples.length,mismatches,samples};
  });
  const captures=[];
  for(const[label,key,phase]of capturesToMake)for(let di=0;di<source.directions.length;di++){
   if(!source.actions[key])throw Error('Missing required capture action '+key);
   const info=await page.evaluate(({key,phase,di})=>{
    const sample=__identitySample(key,di,phase),app=__identityApp(),holder=app.actors.active.get('player');
    app.positionCamera(1);app.flatWorld?.update(app.camera);
    const projected=new __identityCC.Vec3();app.camera.worldToScreen(holder.root.worldPosition,projected);
    if(!(projected.x>0&&projected.x<1280&&projected.y>0&&projected.y<720))throw Error('Ground anchor outside capture viewport');
    return{sample,anchor:[projected.x,720-projected.y],orthoHeight:app.camera.orthoHeight};
   },{key,phase,di});
   await page.waitForTimeout(80);
   // Keep the same world scale and ground anchor across captures. A wide
   // native rectangle preserves lying/death and horizontal sword silhouettes.
   const clip={x:Math.max(0,Math.min(680,Math.round(info.anchor[0]-300))),y:Math.max(0,Math.min(270,Math.round(info.anchor[1]-380))),width:600,height:450};
   const name=`game-${label}-${source.directions[di]}.png`;
   await page.screenshot({path:path.join(__dirname,name),clip});
   captures.push({name,label,key,phase,direction:source.directions[di],...info,clip});
  }
  const expected={actions:88,phaseSamples:1364,textures:69};
  const coverageMatches=poses.actions===expected.actions&&poses.phaseSamples===expected.phaseSamples&&textures.length===expected.textures;
  const report={revision:live.manifest.revision,appearanceAuthority:live.manifest.appearanceAuthority,
   identityReference:live.manifest.identityReference,packing:live.manifest.attackIdentityPacking,
   expected,coverageMatches,manifestMatches,manifestHashes,textures,poses,captures,errors,
   artApproval:'Runtime correctness checked separately from visual art acceptance'};
  fs.writeFileSync(path.join(__dirname,'runtime-audit.json'),JSON.stringify(report,null,2));
  const texturesMatch=textures.every(texture=>texture.matches);
  console.log(JSON.stringify({manifestMatches,texturesMatch,coverageMatches,textures:textures.length,
   actions:poses.actions,phaseSamples:poses.phaseSamples,mismatches:poses.mismatches,errors,captures:captures.length}));
  if(!manifestMatches||!texturesMatch||!coverageMatches||poses.mismatches.length||errors.length)process.exitCode=1;
 }finally{await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
