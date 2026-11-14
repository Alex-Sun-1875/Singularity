// Manual art/input verification in an isolated local browser profile.
// Reuses the project's Playwright/Cocos release inspection workflow.
const {chromium}=require('../../../../src/cocos/node_modules/playwright');
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const assert=require('node:assert/strict');
const root=path.resolve(__dirname,'../../../..'),out=path.join(__dirname,'runtime');fs.mkdirSync(out,{recursive:true});
const actorDir=path.join(root,'src/cocos/assets/resources/flat2d/characters/raphael');
const sha=value=>crypto.createHash('sha256').update(value).digest('hex');
const url=process.env.CHAPTER_URL||'http://127.0.0.1:7469/?view=2d&test=max&revision=locomotion-v3';
const nameOf=name=>name.replace(/\.(png|webp|jpe?g)$/i,'');

(async()=>{
 const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true,args:['--enable-unsafe-swiftshader']});
 try{
  const context=await browser.newContext({viewport:{width:1280,height:720}}),page=await context.newPage(),errors=[];
  page.on('pageerror',error=>errors.push(error.message));
  await page.goto(url,{waitUntil:'domcontentloaded'});await page.waitForFunction(()=>globalThis.System);
  await page.evaluate(async()=>{globalThis.__motionCC=await System.import('cc');globalThis.__motionApp=()=>__motionCC.director.getScene()?.getChildByName('ChapterGame')?.getComponent('ChapterGame');});
  await page.waitForFunction(()=>__motionApp()?.actors?.active.get('player')&&!__motionApp().loading||__motionApp()?.failure,undefined,{timeout:90000});
  assert.equal(await page.evaluate(()=>__motionApp().failure),'');
  await page.evaluate(async()=>{globalThis.__motionAreas=(await System.import('chunks:///_virtual/WorldData.ts')).AREAS;});
  const source=JSON.parse(fs.readFileSync(path.join(actorDir,'manifest.json'),'utf8'));
  const live=await page.evaluate(()=>{const asset=__motionApp().actors.active.get('player').asset;return {manifest:asset.manifest,urls:[...asset.textures].map(([name,texture])=>[name,texture.image?.nativeUrl])};});
  assert.deepEqual(live.manifest,source,'compiled manifest must match installed source');
  const textures=[];
  for(const name of ['locomotion-v3/body-walk-0.png','locomotion-v3/body-run-0.png','locomotion-v3/body-run-1.png','locomotion-v3/equipment.png']){
   const entry=live.urls.find(([key])=>key===nameOf(name));assert.ok(entry,'loaded '+name);
   const response=await context.request.get(new URL(entry[1],page.url()).href);assert.ok(response.ok());
   const expected=sha(fs.readFileSync(path.join(actorDir,name))),actual=sha(await response.body());assert.equal(actual,expected);textures.push({name,sha256:actual});
  }
  const samples=await page.evaluate(()=>{
   const app=__motionApp(),player=app.actors.active.get('player'),m=player.asset.manifest;
   app.menu='qa';app.enabled=false;app.hud.root.active=false;app.manualCameraHeight=2;app.positionCamera(1);app.camera.orthoHeight=2;app.flatWorld?.update(app.camera,app.session);
   globalThis.__sampleMotion=(key,direction,ordinal,weapon)=>{
    const di=m.directions.indexOf(direction),right=app.camera.node.right,up=app.camera.node.up;
    const v=direction==='right'?[right.x,right.z]:direction==='left'?[-right.x,-right.z]:direction==='up'?[up.x,up.z]:[-up.x,-up.z];
    player.angle=Math.atan2(v[0],v[1]);player.renderedWeaponId=weapon;
    const a=m.actions[key],state=key.includes('run')?'run':key.includes('walk')?'walk':'idle';
    app.actors.show(player,state,0,(ordinal+.25)/a.frames,true,key);
    const image=(a.frameImages?.[ordinal]??a.image).replace(/\.png$/,'');
    const sample=app.actors.frame(player.asset,a,di,ordinal),gear=player.equipment;
    const anchor=a.equipmentAnchors?.[a.equipmentLayer]?.[direction]?.[ordinal];
    return {key,direction,ordinal,actualOrdinal:player.ordinal,actualDirection:player.direction,image,sharedBody:a.sharedBody,
     textureMatches:player.material.getProperty('mainTexture')===player.asset.textures.get(image),
     weaponVisible:!!gear?.root.active,handVisible:!!gear?.handSprite.active,quiverVisible:!!gear?.backRoot.active,
     socketError:anchor?Math.max(Math.abs(gear.root.position.x-anchor.x),Math.abs(gear.root.position.y-anchor.y)):0,
     scaleError:Math.max(Math.abs(player.sprite.scale.x-sample.frame.rect.width*.004),Math.abs(player.sprite.scale.y-sample.frame.rect.height*.004))};
   };
   const result=[];
   for(const[key,a]of Object.entries(m.actions))if(a.sharedBody){
    const match=key.match(/_(W\d+|L\d+)$/),weapon=match?.[1]??(key.includes('bow')?'W07':key.includes('staff')?'W11':'W01');
    for(const direction of m.directions)for(let p=0;p<a.frames;p++)result.push(__sampleMotion(key,direction,p,weapon));
   }
   return result;
  });
  assert.ok(samples.length>600);
  assert.ok(samples.every(s=>s.textureMatches&&s.weaponVisible&&s.handVisible&&s.ordinal===s.actualOrdinal&&s.scaleError<1e-5&&s.socketError<1e-5),'every movement alias/phase must render the shared body and matching weapon socket');
  const captures=[];
  for(const state of ['walk','run'])for(const direction of source.directions){
   const count=state==='walk'?4:8;
   for(let ordinal=0;ordinal<count;ordinal++){
    const info=await page.evaluate(({state,direction,ordinal})=>{const sample=__sampleMotion('explore_'+state+'_W07',direction,ordinal,'W07'),app=__motionApp(),point=new __motionCC.Vec3();app.camera.worldToScreen(app.actors.active.get('player').root.worldPosition,point);return {sample,clip:{x:Math.max(0,Math.min(800,point.x-240)),y:Math.max(0,Math.min(170,720-point.y-470)),width:480,height:550}};},{state,direction,ordinal});
    await page.waitForTimeout(35);const file=`${state}-${direction}-${ordinal}.jpg`;await page.screenshot({path:path.join(out,file),type:'jpeg',quality:92,clip:info.clip});captures.push({file,...info.sample});
   }
  }
  for(const weapon of ['W01','W07','W11'])for(const direction of source.directions){
   const info=await page.evaluate(({weapon,direction})=>{const sample=__sampleMotion('run_'+weapon,direction,0,weapon),app=__motionApp(),point=new __motionCC.Vec3();app.camera.worldToScreen(app.actors.active.get('player').root.worldPosition,point);return {sample,clip:{x:Math.max(0,Math.min(800,point.x-240)),y:Math.max(0,Math.min(170,720-point.y-470)),width:480,height:550}};},{weapon,direction});
   await page.waitForTimeout(35);const file=`held-${weapon}-${direction}.jpg`;await page.screenshot({path:path.join(out,file),type:'jpeg',quality:92,clip:info.clip});captures.push({file,...info.sample});
  }
  const motion=await page.evaluate(async()=>{
   const app=__motionApp(),reports=[];
   const selected=['S01-T1','S01','S02','H01','G01','U1-04'].filter(id=>__motionAreas[id]);
   for(const id of selected){
    const area=__motionAreas[id];app.enabled=true;app.menu='qa';app.session.enter(area,area.spawn);await app.rebuild();app.enabled=false;app.menu='qa';app.hud.root.active=false;
    const g=app.session,player=app.actors.active.get('player'),right=app.camera.node.right,up=app.camera.node.up;
    const frames=[];
    for(const slow of [false,true]){
     const magnitude=slow?.48:1;
     // Normal commands and capsule/world movement, changing heading each segment.
     for(let segment=0;segment<4;segment++)for(let i=0;i<30;i++){
      const v=segment===0?[right.x,right.z]:segment===1?[up.x,up.z]:segment===2?[-right.x,-right.z]:[-up.x,-up.z],norm=Math.hypot(...v);
      const input={x:v[0]/norm*magnitude,z:v[1]/norm*magnitude};g.advance(1/30,input);app.actors.update(g,1/30,true,false,magnitude);app.effects.update(g);app.positionCamera(1);app.flatWorld?.update(app.camera,g);
      if(!g.state.action&&g.state.player.hurtTime<=.33&&player.speed>.08)frames.push({slow,state:player.state,speed:player.speed,ordinal:player.ordinal,texture:player.sampledAction,shared:!!player.asset.manifest.actions[player.sampledAction]?.sharedBody});
      if(i%10===0)await new Promise(r=>setTimeout(r,16));
     }
    }
    reports.push({area:id,name:area.name,frames,runFrames:frames.filter(f=>!f.slow&&f.state==='run').length,walkFrames:frames.filter(f=>f.slow&&f.state==='walk').length,lowSpeedRunFrames:frames.filter(f=>!f.slow&&f.speed<2.5).length,mismatches:frames.filter(f=>f.state!==(f.slow?'walk':'run')||!f.shared)});
   }
   return reports;
  });
  assert.ok(motion.length>=4,'multiple real scene types must be checked');assert.ok(motion.every(r=>r.runFrames>0&&r.walkFrames>0&&r.mismatches.length===0));assert.deepEqual(errors,[]);
  const report={url,manifestSHA256:sha(fs.readFileSync(path.join(actorDir,'manifest.json'))),loadedHeroTextures:live.urls.length,textures,movementPhaseSamples:samples.length,samples,captures,motion,errors};
  fs.writeFileSync(path.join(out,'report.json'),JSON.stringify(report,null,2));console.log(JSON.stringify({phaseSamples:samples.length,textures:textures.length,scenes:motion.map(r=>({area:r.area,run:r.runFrames,walk:r.walkFrames,partialSpeedRuns:r.lowSpeedRunFrames,mismatches:r.mismatches.length})),errors}));
 }finally{await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
