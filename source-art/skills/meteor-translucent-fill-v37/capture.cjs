// Records the actual Cocos canvas. No replacement VFX, scene fixture, or camera edits.
const fs=require('node:fs'),path=require('node:path'),http=require('node:http'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'../../..'),cocos=path.join(root,'src/cocos'),sourceBuild=path.join(cocos,'build/concept-2d');
const {chromium}=require(path.join(cocos,'node_modules/playwright'));
const args=process.argv.slice(2),option=(name,fallback)=>{const i=args.indexOf('--'+name);return i<0?fallback:args[i+1];};
const buildOption=option('build-dir',''),build=buildOption?path.resolve(root,buildOption):sourceBuild;
const sourceBuildLockPresentAtCaptureStart=fs.existsSync(path.join(cocos,'temp/taptap-build.lock'));
if(build===sourceBuild&&sourceBuildLockPresentAtCaptureStart)throw Error('A Cocos build is active; wait for build-ready before recording from the live output');
const buildProvenance={sourceBuild:path.relative(root,sourceBuild).replaceAll('\\','/'),servedBuild:path.relative(root,build).replaceAll('\\','/'),snapshotPath:build===sourceBuild?null:path.relative(root,build).replaceAll('\\','/'),mode:build===sourceBuild?'live-source-build':'frozen-build-snapshot',sourceBuildLockPresentAtCaptureStart,sourceHashSampling:'Current workspace files at recorder launch; compiled snapshot provenance is the root copy proof plus served main/resource hashes.'};
const stage=option('stage','final'),rank=Number(option('rank','1')),only=option('only',''),emptyGround=args.includes('--empty'),singleTarget=args.includes('--single');
if(!/^[a-z0-9-]+$/i.test(stage)||!Number.isInteger(rank)||rank<1||rank>5)throw Error('Invalid stage/rank');
if(emptyGround&&singleTarget)throw Error('--empty and --single are separate views');
const kitShots=[
 {id:'FIR_02',name:'陨石终极',ultimate:true,seconds:9}
];
const shots=kitShots.filter(s=>only?only.split(',').includes(s.id):singleTarget?s.id==='FIR_01':s.id==='FIR_02');
if(!shots.length)throw Error('Unknown --only skill');
const recording=stage+(emptyGround?'-empty':singleTarget?'-single':'')+'-r'+rank;
const output=path.join(root,'src/.tmp/meteor-translucent-fill-v37',recording),reports=path.join(__dirname,recording);
if(fs.existsSync(path.join(reports,'capture.json')))throw Error('This recording label is already complete; choose a new --stage to preserve its evidence');
fs.mkdirSync(output,{recursive:true});fs.mkdirSync(reports,{recursive:true});
const sha=file=>crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const mainFile=()=>{const dir=path.join(build,'assets/main'),files=fs.readdirSync(dir).filter(n=>/^index(?:\..+)?\.js$/.test(n));if(files.length!==1)throw Error('Expected one unambiguous compiled main');return path.join(dir,files[0]);};
const gameHash=sha(mainFile()),sourceHashes={};
if(build!==sourceBuild){
 const index=path.join(__dirname,'snapshot.json');if(!fs.existsSync(index))throw Error('Frozen recording requires the completed bitwise-copy proof');
 const proof=JSON.parse(fs.readFileSync(index,'utf8'));if(path.resolve(root,proof.servedSnapshot??'')!==build)throw Error('Frozen snapshot proof points to a different served build');
 if(proof.compiledSha256!==gameHash)throw Error('Frozen snapshot proof main SHA does not match the served main');
 const manifest=proof.copyManifest&&path.resolve(root,proof.copyManifest);if(!manifest||!fs.existsSync(manifest)||sha(manifest)!==proof.copyManifestSha256)throw Error('Frozen snapshot copy-manifest proof is missing or changed');
 const preserved=path.join(reports,'served-build-snapshot.json');fs.copyFileSync(index,preserved);buildProvenance.snapshotProofIndex=path.relative(root,preserved).replaceAll('\\','/');buildProvenance.snapshotProofIndexSha256=sha(preserved);buildProvenance.copyManifest=path.relative(root,manifest).replaceAll('\\','/');buildProvenance.copyManifestSha256=sha(manifest);
}
for(const file of ['SkillFireSprites.ts','FireImpactEffects.ts','FireFieldEffects.ts','SkillMeteorBody.ts','FireGroundEffects.ts','NativeSkillVfx.ts','Effects.ts']){const source=path.join(cocos,'assets/scripts/features/combat/runtime',file);if(fs.existsSync(source))sourceHashes[file]=sha(source);}
// Read-only evidence for concurrent balance changes; never set the seed or alter combat rules.
for(const file of ['core/GameSession.ts','core/Contracts.ts','features/combat/data/PureSkills.ts','features/combat/common/PureCombat.ts','features/combat/common/CombatAccuracy.ts','features/equipment/common/EquipmentDice.ts','features/debug/common/TrainingRange.ts','features/progression/data/CampaignProgression.ts','features/progression/data/CampaignExperience.ts','features/progression/common/Progression.ts','shared/BuildProfile.ts','features/combat/common/PlayerMotionContracts.ts']){const source=path.join(cocos,'assets/scripts',file);if(fs.existsSync(source))sourceHashes[file]=sha(source);}
const production=path.join(cocos,'assets/resources/vfx/production'),assetFiles=[],assetBindings=[];
for(const name of fs.readdirSync(production).filter(name=>/^(fire-.*v3[01234567](?:r[0-9]+)?(?:-[a-z0-9]+)*|meteor-.*v(?:9|28|32|33|34|35|36|37)(?:r[0-9]+)?(?:-[a-z0-9]+)*)\.(?:png|effect|json)$/.test(name))){
 const file=path.join(production,name);assetFiles.push(file);const meta=file+'.meta';if(!fs.existsSync(meta))continue;assetFiles.push(meta);const uuid=JSON.parse(fs.readFileSync(meta,'utf8')).uuid;if(!uuid)continue;
 const binding={source:path.relative(root,file).replaceAll('\\','/'),uuid,servedAssets:[]};
 for(const kind of ['import','native']){const folder=path.join(build,'assets/resources',kind,uuid.slice(0,2));if(!fs.existsSync(folder))continue;for(const exported of fs.readdirSync(folder))if(exported.startsWith(uuid+'.')){const exportedFile=path.join(folder,exported);assetFiles.push(exportedFile);binding.servedAssets.push(path.relative(root,exportedFile).replaceAll('\\','/'));}}
 assetBindings.push(binding);
}
const assetEvidence={purpose:'Read-only source/export shader and roll asset hashes; no runtime override.',buildProvenance,assetBindings,files:assetFiles.filter(f=>fs.existsSync(f)).map(file=>({path:path.relative(root,file).replaceAll('\\','/'),sha256:sha(file),bytes:fs.statSync(file).size,servedBuildAsset:file.startsWith(build+path.sep)}))};
fs.writeFileSync(path.join(reports,'shader-asset-evidence.json'),JSON.stringify(assetEvidence,null,2));
const artSourceFolder=path.join(root,'source-art/skills/meteor-complete-sigil-v35/seal'),materialProvenanceOption=option('seal-provenance',''),materialProvenancePath=materialProvenanceOption?path.resolve(root,materialProvenanceOption):path.join(__dirname,'assets/provenance.json'),artSourceEvidence={declaration:'V37 deterministically adds a faint orange interior fill and adjusts texture translucency. The V35 cloud source/prompt are reused without generation. Texture alpha may change; renderer draw opacity is recorded separately. Calculated material samples and native captures remain separate evidence categories.',newGenerationThisRound:false,processingThisRound:'deterministic translucent orange fill and texture alpha adjustment',materialProvenancePath:path.relative(root,materialProvenancePath).replaceAll('\\','/'),files:[]};
for(const [name,kind] of [['cloud-complete-fire-sigil.png','cloud-generated-source-not-native'],['cloud-generation.json','cloud-generation-provenance'],['cloud-refinement-prompt.txt','cloud-generation-prompt']]){const file=path.join(artSourceFolder,name);if(fs.existsSync(file))artSourceEvidence.files.push({path:path.relative(root,file).replaceAll('\\','/'),sha256:sha(file),bytes:fs.statSync(file).size,kind});}
if(!fs.existsSync(materialProvenancePath))throw Error('Final engineering material provenance is missing');
artSourceEvidence.files.push({path:path.relative(root,materialProvenancePath).replaceAll('\\','/'),sha256:sha(materialProvenancePath),bytes:fs.statSync(materialProvenancePath).size,kind:'engineering-material-provenance'});
if(fs.existsSync(path.join(artSourceFolder,'cloud-generation.json'))){const generation=JSON.parse(fs.readFileSync(path.join(artSourceFolder,'cloud-generation.json'),'utf8'));const generated=artSourceEvidence.files.find(file=>file.kind==='cloud-generated-source-not-native');if(!generated||generation.result?.sha256!==generated.sha256)throw Error('Cloud-generated source bytes do not match the recorded generation provenance');artSourceEvidence.reusedSourceGenerationTool=generation.generation?.tool;artSourceEvidence.reusedSourceLocalInference=generation.generation?.localInference;}
fs.writeFileSync(path.join(reports,'art-source-evidence.json'),JSON.stringify(artSourceEvidence,null,2));
const mime={'.js':'text/javascript','.json':'application/json','.html':'text/html','.png':'image/png','.jpg':'image/jpeg','.css':'text/css','.bin':'application/octet-stream','.wasm':'application/wasm'};
const server=http.createServer((req,res)=>{const url=decodeURIComponent(new URL(req.url,'http://127.0.0.1').pathname),file=path.resolve(build,'.'+(url==='/'?'/index.html':url));if(!file.startsWith(build+path.sep)||!fs.existsSync(file)||!fs.statSync(file).isFile()){res.writeHead(404).end();return;}res.setHeader('Content-Type',mime[path.extname(file)]||'application/octet-stream');fs.createReadStream(file).pipe(res);});

async function run(){
 await new Promise(r=>server.listen(0,'127.0.0.1',r));
 const browser=await chromium.launch({headless:true,args:['--enable-webgl','--enable-unsafe-swiftshader','--use-angle=swiftshader','--mute-audio']});
 try{
  const page=await browser.newPage({viewport:{width:1280,height:636},deviceScaleFactor:2}),errors=[],consoleErrors=[];
  page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')consoleErrors.push(m.text());});
  await page.goto('http://127.0.0.1:'+server.address().port+'/?view=2d&player=3d',{waitUntil:'load'});
  await page.waitForFunction(()=>globalThis.System,undefined,{timeout:60000});
  await page.evaluate(async()=>{const cc=await System.import('cc');globalThis.findRangeApp=()=>{function find(n){return n?.getComponent('ChapterGame')||n?.children.map(find).find(Boolean);}return find(cc.director.getScene());};});
  await page.waitForFunction(()=>{const a=findRangeApp();return a?.session&&a?.actors&&!a.loading&&a.platform.auth.ready;},undefined,{timeout:90000});
  console.log('Opening actual training range',stage,'rank',rank,'bundle',gameHash.slice(0,12));
  const journeyStart=await page.evaluate(()=>{
   const app=findRangeApp(),s=app.session.state;
   if(s.progression.level!==1||app.temporaryMax)throw Error('Expected a fresh normal test level-1 journey; no max-level preview shortcut is allowed');
   globalThis.recordingOriginalJourney={session:app.session,progression:JSON.stringify(s.progression),equipment:JSON.stringify(s.equipment)};
   return{level:s.progression.level,totalXp:s.progression.totalXp,area:s.area,seed:s.seed,sequence:s.sequence,temporaryMax:app.temporaryMax,freshBrowserContext:true,menu:app.menu};
  });
  await page.evaluate(()=>findRangeApp().click('training:enter'));
  await page.waitForFunction(()=>{const app=findRangeApp();return!!app.trainingRange&&!app.loading;},undefined,{timeout:90000});
  await page.evaluate(rank=>{
   const app=findRangeApp();
   // Use the existing debug menu action and its resource preparation, exactly
   // as the training menu does. No direct combat-slot or rank mutation.
   app.click('skill-effect-debug');app.click('debug:rank:'+rank);
  },rank);
  await page.waitForFunction(()=>!findRangeApp().loading,undefined,{timeout:90000});
  await page.evaluate(()=>{const app=findRangeApp();app.click('debug:family-rank');});
  await page.waitForFunction(()=>!findRangeApp().loading,undefined,{timeout:90000});
  await page.evaluate(()=>{const app=findRangeApp();app.click('debug:loadout');});
  await page.waitForFunction(()=>!findRangeApp().loading,undefined,{timeout:90000});
  const info=await page.evaluate(async({emptyGround,singleTarget})=>{
   const cc=await System.import('cc'),app=findRangeApp();
   if(emptyGround){
    app.click('training:formation:single');
    while(app.trainingRange.distance!==12)app.click('training:distance');
   }else if(singleTarget){app.click('training:formation:single');}
   else{app.click('training:formation:cluster');while(app.trainingRange.distance!==4)app.click('training:distance');}
   app.click('close');app.hud.root.active=true;app.clearInput(false);app.enabled=false;cc.game.pause();
   const events=[],original=app.process.bind(app);
   app.process=function(batch,...rest){for(const e of batch)if(e.type.startsWith('skill_')||['hit','miss','block'].includes(e.type))events.push({time:app.session.state.time,...JSON.parse(JSON.stringify(e))});return original(batch,...rest);};
   const inspect=()=>{
    const e=app.effects,s=app.session.state;
    const impact=e.skills.cues.find(c=>c.kind==='blast'&&c.event.skillId==='FIR_02'),drop=e.skills.cues.find(c=>c.kind==='drop'&&c.event.skillId==='FIR_02'),meteor=e.meteor.inspect();
    for(const body of meteor.active){const nose=body.nose??body.position,target=body.target;if(!nose||!target)continue;const screenNose=app.camera.worldToScreen(new cc.Vec3(nose.x,nose.y,nose.z)),screenTarget=app.camera.worldToScreen(new cc.Vec3(target.x,target.y,target.z));body.screen={nose:{x:screenNose.x,y:screenNose.y},target:{x:screenTarget.x,y:screenTarget.y},projectedDescentAngleDegrees:Math.atan2(Math.abs(screenNose.y-screenTarget.y),Math.abs(screenNose.x-screenTarget.x))*180/Math.PI};}
    return{time:s.time,seed:s.seed,sequence:s.sequence,revision:s.revision,cameraHeight:app.camera.orthoHeight,cameraGroundVerticalFactor:Math.hypot(app.camera.node.up.x,app.camera.node.up.z),castAge:drop?s.time-drop.start:null,impactAge:impact?s.time-impact.start:null,ground:e.fireGround.inspect(),fire:e.fireSprites.inspect(),meteor,shield:e.shields.inspect(),
     native:{cues:e.skills.cues.map(c=>({kind:c.kind,skillId:c.event.skillId,castId:c.event.castId,eventType:c.event.type,start:c.start,age:s.time-c.start,duration:c.duration,coolingAt:c.coolingAt,target:c.event.at??c.event.to??c.event.from,from:c.event.from,to:c.event.to,geometry:c.event.geometry})),particles:{allocated:e.emitters.length,active:e.emitters.filter(p=>p.node.active).length},linePool:e.lines.length,bodyPool:e.bodies.length},
     hits:app.trainingRange.hits,damage:app.trainingRange.damage,misses:app.trainingRange.misses,criticalHits:app.trainingRange.criticalHits,
     cooldowns:{...s.combat.cooldowns},ultimateLock:s.combat.ultimateLock,casts:s.combat.casts.map(c=>({id:c.id,skillId:c.skillId,elapsed:c.elapsed,released:c.released,targets:c.targets,hits:c.hits})),projectiles:s.projectiles.filter(p=>p.owner==='player').map(p=>({id:p.id,skillId:p.skillId,x:p.x,z:p.z,age:p.age}))};
   };
   globalThis.familyReview={cc,app,events,inspect,emptyGround,tick(){app.update(1/60);cc.director.tick(1/60);},cast(shot){const p=app.session.state.player,a=-Math.PI/6,t=this.emptyGround?{x:p.x+Math.sin(a)*4,z:p.z+Math.cos(a)*4}:app.session.state.enemies.find(e=>e.hp>0);app.pulse={...(shot.ultimate?{ultimate:true}:{combatSlot:shot.slot}),aim:Math.atan2(t.x-p.x,t.z-p.z),target:{x:t.x,z:t.z}};}};
   const player=app.actors.player??app.actors;
   const gameplaySnapshot=JSON.parse(JSON.stringify({seed:app.session.state.seed,sequence:app.session.state.sequence,equipment:app.session.state.equipment,progression:app.session.state.progression,combat:app.session.state.combat,player:app.session.state.player}));
   return{area:app.session.state.area,rangeCharacterLevel:app.session.state.progression.level,rangeMaxLevel:app.session.progressionView().maxLevel,rangeSessionIsSeparate:app.session!==recordingOriginalJourney.session,formation:app.trainingRange.formation,distance:app.trainingRange.distance,emptyGround,singleTarget,aimDistance:4,emptyAimAngle:emptyGround?-Math.PI/6:null,enemies:app.session.state.enemies.filter(e=>e.hp>0).map(e=>({id:e.id,x:e.x,z:e.z})),unlimitedResource:app.trainingRange.unlimitedResource,ranks:{...app.session.state.progression.learned},activeSlots:app.session.state.combat.activeSlots,ultimate:app.session.state.combat.ultimate,viewport:[cc.game.canvas.width,cc.game.canvas.height],cameraHeight:app.camera.orthoHeight,cameraGroundVerticalFactor:Math.hypot(app.camera.node.up.x,app.camera.node.up.z),player:player.inspect().find(p=>p.id==='player'),gameplaySnapshot,cameraBound:app.effects.fireGround.camera===app.camera,loadoutFlow:'Formal click training:enter, then debug:rank / debug:family-rank / debug:loadout with prepareSkillDebugEffects'};
  },{emptyGround,singleTarget});
  const captures=[];
  for(const shot of shots){
   const folder=path.join(output,shot.id);fs.mkdirSync(folder,{recursive:true});
   const start=await page.evaluate(()=>{const r=familyReview,a=r.app;a.resetTrainingRange();a.menu='';a.hud.clearModal();a.hud.root.active=true;a.effects.reducedMotion=false;for(let i=0;i<12;i++)r.tick();r.events.length=0;return r.inspect();});
   const metrics=[],frames=shot.seconds*30,early=new Set();
   for(let frame=0;frame<frames;frame++){
    const data=await page.evaluate(({frame,shot})=>{const r=familyReview;if(frame===12)r.cast(shot);r.tick();r.tick();return{image:r.cc.game.canvas.toDataURL('image/jpeg',.95).split(',')[1],...r.inspect()};},{frame,shot});
    fs.writeFileSync(path.join(folder,String(frame).padStart(3,'0')+'.jpg'),Buffer.from(data.image,'base64'));delete data.image;metrics.push({frame,...data});
    const saveEarly=(name,metric,request={})=>{if(early.has(name))return;early.add(name);const directory=path.join(reports,'early');fs.mkdirSync(directory,{recursive:true});fs.copyFileSync(path.join(folder,String(metric.frame).padStart(3,'0')+'.jpg'),path.join(directory,shot.id+'-'+name+'.jpg'));fs.writeFileSync(path.join(directory,shot.id+'-'+name+'.json'),JSON.stringify({...metric,...request},null,2));console.log('Native early frame',shot.id,name,'frame',metric.frame,'actualImpactAge',metric.impactAge,'path',path.join(directory,shot.id+'-'+name+'.jpg'));};
    const current=metrics.at(-1),previous=metrics.at(-2),fall=current.meteor.active[0];
    if(current.castAge!==null&&current.castAge>=.2-1e-8)saveEarly('seal-preview',previous?.castAge!==null&&previous?.castAge!==undefined&&Math.abs(previous.castAge-.2)<Math.abs(current.castAge-.2)?previous:current);
    if(fall&&typeof fall.progress==='number'&&fall.progress>=.6){const old=previous?.meteor.active[0];saveEarly('flight-60',old&&typeof old.progress==='number'&&Math.abs(old.progress-.6)<Math.abs(fall.progress-.6)?previous:current);}
    if(current.impactAge!==null&&current.impactAge>=-1e-8)saveEarly('impact-0000ms',current);
    if(current.impactAge!==null&&current.impactAge>=.25-1e-8)saveEarly('impact-0250ms',previous?.impactAge!==null&&previous?.impactAge!==undefined&&Math.abs(previous.impactAge-.25)<Math.abs(current.impactAge-.25)?previous:current);
    for(const age of [0,.033,.066,.1,.15,.2,.3,.45,.65])if(current.impactAge!==null&&current.impactAge>=age-1e-8)saveEarly('ignition-'+String(Math.round(age*1000)).padStart(4,'0')+'ms',previous?.impactAge!==null&&previous?.impactAge!==undefined&&previous.impactAge>=0&&Math.abs(previous.impactAge-age)<Math.abs(current.impactAge-age)?previous:current,{requestedImpactAge:age,samplingQualification:'Nearest actual exported30fps frame; requested ages can share a frame. No interpolation or retiming.'});
    for(const age of [1.2,1.4,1.6,1.8,2.2,2.8,3.5])if(current.impactAge!==null&&current.impactAge>=age-1e-8)saveEarly('cooling-'+String(Math.round(age*1000)).padStart(4,'0')+'ms',previous?.impactAge!==null&&previous?.impactAge!==undefined&&Math.abs(previous.impactAge-age)<Math.abs(current.impactAge-age)?previous:current);
    const released=metrics.find(m=>m.impactAge!==null&&m.impactAge>=0),resolvedImpactTime=released?released.time-released.impactAge:null;
    if(resolvedImpactTime!==null)for(const age of [.25,.65,1.2,1.6,2.2,2.8,3.5,4.3,4.62])if(current.time-resolvedImpactTime>=age-1e-8){const sample=previous&&Math.abs(previous.time-resolvedImpactTime-age)<Math.abs(current.time-resolvedImpactTime-age)?previous:current;saveEarly('seal-held-'+String(Math.round(age*1000)).padStart(4,'0')+'ms',sample,{requestedImpactAge:age,actualImpactAge:sample.time-resolvedImpactTime,samplingQualification:'Nearest actual exported30fps frame. Ground.inspect is retained even after the native blast cue has expired.'});}
    if(shot.id==='FIR_01'){
     if(current.fire.active.some(s=>s.kind==='lance'&&s.width>.6))saveEarly('projectile-native',current);
     const cue=current.native.cues.find(c=>c.kind==='blast'&&c.skillId===shot.id);if(cue&&cue.age>=.08)saveEarly('contact-native',current);
    }
    if(shot.id==='FIR_05'){const cue=current.native.cues.find(c=>c.kind==='field'&&c.skillId===shot.id);if(cue&&cue.age>=.65)saveEarly('field-native',current);}
   }
   const events=await page.evaluate(()=>familyReview.events),capture={...shot,start,frames,events,metrics};captures.push(capture);
   fs.writeFileSync(path.join(reports,shot.id+'.json'),JSON.stringify(capture,null,2));
   console.log('Recorded',shot.id,shot.seconds+'s',JSON.stringify({hits:metrics.at(-1).hits,damage:metrics.at(-1).damage,release:events.find(e=>e.type==='skill_release')?.time,hitEvents:events.filter(e=>e.type==='hit').length,clearGround:!metrics.at(-1).ground.active.length,clearFire:!metrics.at(-1).fire.active.length}));
  }
  const lifecycle=[];
  for(const shot of emptyGround||singleTarget?[]:shots){
   lifecycle.push(await page.evaluate(shot=>{
    const r=familyReview,a=r.app,s=a.session.state,tick=n=>{for(let i=0;i<n;i++)r.tick();};
    const reducedTicks=12;
    a.click('training:reset');a.menu='';a.hud.clearModal();a.effects.reducedMotion=false;r.cast(shot);
    let pauseTicks=0;
    while(pauseTicks<600){const snapshot=r.inspect(),seal=snapshot.ground.active.find(surface=>surface.kind==='meteorSeal');if(snapshot.impactAge>=3.7&&snapshot.impactAge<3.9&&seal&&seal.opacity>0&&seal.opacity<.9)break;r.tick();pauseTicks++;}
    if(pauseTicks===600)throw Error('Did not reach the actual active post-impact meteor seal fade phase');
    const cachedSeal=()=>a.effects.fireGround.surfaces.map((surface,slot)=>({slot,kind:surface.kind,opacity:surface.opacity,active:surface.node.active,key:surface.key})).filter(surface=>surface.kind==='meteorSeal');
    const activeSealOpacity=snapshot=>snapshot.ground.active.find(surface=>surface.kind==='meteorSeal')?.opacity??null;
    const before=r.inspect(),authoritative=()=>JSON.stringify({time:s.time,casts:s.combat.casts,projectiles:s.projectiles,cooldowns:s.combat.cooldowns,shield:s.player.shield});
    const beforeCache=cachedSeal(),core=authoritative();a.click('training:settings');tick(12);const paused=r.inspect(),pausedCache=cachedSeal(),pauseStable=core===authoritative();
    const cachedAlpha=values=>JSON.stringify(values.map(({slot,opacity})=>({slot,opacity})));
    const opacityStableWhilePaused=cachedAlpha(beforeCache)===cachedAlpha(pausedCache);
    a.click('close');tick(1);const resumed=r.inspect(),resumedCache=cachedSeal();
    a.effects.reducedMotion=true;tick(reducedTicks);const lowOne=r.inspect();tick(reducedTicks);const lowTwo=r.inspect();
    const resetWhileSealActive=lowTwo.ground.active.some(surface=>surface.kind==='meteorSeal');
    a.click('training:reset');a.effects.reducedMotion=false;const reset=r.inspect();
    const sealFade={beforeAge:before.impactAge,beforeOpacity:activeSealOpacity(before),pausedActiveOpacity:activeSealOpacity(paused),resumedAge:resumed.impactAge,resumedOpacity:activeSealOpacity(resumed),laterOpacity:activeSealOpacity(lowTwo),beforeCache,pausedCache,resumedCache,opacityStableWhilePaused,resetWhileSealActive,
     qualification:'Pause intentionally hides and clears active VFX. Cached opacity is the actual last-draw surface property, not a visible paused seal or a newly simulated alpha. The authoritative clock stays frozen; active ground.inspect opacity resumes from that clock.'};
    return{id:shot.id,pauseTicks,reducedTicks,before,paused,pauseStable,resumed,reducedMotionFirst:lowOne,reducedMotionSecond:lowTwo,reset,sealFade};
   },shot));
   fs.writeFileSync(path.join(reports,'lifecycle.json'),JSON.stringify(lifecycle,null,2));
   console.log('Lifecycle',shot.id,'pauseStable',lifecycle.at(-1).pauseStable);
  }
  // Exercise the existing family buttons, including a same-weapon staff switch
  // and a weapon switch. Do not mutate family, loadouts, or renderer state.
  const switches=[];
  for(const family of emptyGround||singleTarget?[]:['THU','WAR','FIR']){
   const before=await page.evaluate(()=>{const r=familyReview,a=r.app;a.click('training:reset');a.menu='';a.hud.clearModal();const family=a.session.state.combat.family;if(family==='FIR'){r.cast({ultimate:true});let ticks=0;while(ticks<600){const snapshot=r.inspect();if(snapshot.impactAge>=3.7&&snapshot.ground.active.some(surface=>surface.kind==='meteorSeal'&&surface.opacity>0))break;r.tick();ticks++;}if(ticks===600)throw Error('Did not reach an active meteor seal before the real family button');}const snapshot=r.inspect();return{family,exercisedActiveSeal:snapshot.ground.active.some(surface=>surface.kind==='meteorSeal'),...snapshot};});
   await page.evaluate(family=>{
    const r=familyReview,a=r.app;a.click('skill-effect-debug');
    const find=n=>n?.name==='DebugFamily:'+family?n:n?.children.map(find).find(Boolean),button=find(a.hud.root);
    if(!button)throw Error('Missing real debug family button '+family);
    r.cc.game.resume();button.emit(r.cc.Button.EventType.CLICK,button.getComponent(r.cc.Button));
   },family);
   await page.waitForFunction(()=>!findRangeApp().loading,undefined,{timeout:90000});
   const after=await page.evaluate(()=>{const r=familyReview,a=r.app;r.cc.game.pause();a.click('close');for(let i=0;i<2;i++)r.tick();return{family:a.session.state.combat.family,weapon:a.session.state.equipment.weapon,slots:a.session.state.combat.activeSlots,...r.inspect()};});
   switches.push({family,before,after});
   fs.writeFileSync(path.join(reports,'switches.json'),JSON.stringify(switches,null,2));
   console.log('Family switch',family,'loaded',after.family,'fire',after.fire.active.length,'ground',after.ground.active.length);
  }
  await page.evaluate(()=>{familyReview.cc.game.resume();findRangeApp().click('training:exit');});
  await page.waitForFunction(()=>{const app=findRangeApp();return!app.trainingRange&&!app.loading;},undefined,{timeout:90000});
  const journeyRestoration=await page.evaluate(()=>{const app=findRangeApp(),s=app.session.state,original=recordingOriginalJourney;familyReview.cc.game.pause();return{sessionRestored:app.session===original.session,level:s.progression.level,progressionUnchanged:JSON.stringify(s.progression)===original.progression,equipmentUnchanged:JSON.stringify(s.equipment)===original.equipment,trainingRangeAbsent:!app.trainingRange};});
  if(!journeyRestoration.sessionRestored||journeyRestoration.level!==journeyStart.level||!journeyRestoration.progressionUnchanged||!journeyRestoration.equipmentUnchanged||!journeyRestoration.trainingRangeAbsent)throw Error('Training range did not restore the original level-1 journey unchanged');
  const servedAssets=assetEvidence.files.filter(f=>f.servedBuildAsset);if(!servedAssets.length)throw Error('No served shader/texture assets were identified for provenance');
  assetEvidence.compiledAssetsStable=servedAssets.every(f=>fs.existsSync(path.join(root,f.path))&&sha(path.join(root,f.path))===f.sha256);
  fs.writeFileSync(path.join(reports,'shader-asset-evidence.json'),JSON.stringify(assetEvidence,null,2));
  const stableBuild=gameHash===sha(mainFile())&&assetEvidence.compiledAssetsStable;
  const report={recorderRevision:7,stage,rank,emptyGround,singleTarget,gameHash,sourceHashes,buildProvenance,artSourceEvidence,stableBuild,journeyStart,journeyRestoration,info,errors,consoleErrors,lifecycle,switches,cache:path.relative(root,output),shots:captures.map(({metrics,...s})=>({...s,summary:{hits:metrics.at(-1).hits,damage:metrics.at(-1).damage,misses:metrics.at(-1).misses,criticalHits:metrics.at(-1).criticalHits,last:metrics.at(-1),peakFire:Math.max(...metrics.map(m=>m.fire.active.length)),peakGround:Math.max(...metrics.map(m=>m.ground.active.length))}}))};
  fs.writeFileSync(path.join(reports,'capture.json'),JSON.stringify(report,null,2));
  if(!stableBuild||errors.length||consoleErrors.length)throw Error(JSON.stringify({stableBuild,errors,consoleErrors}));
 }finally{await browser.close();}
}
run().catch(e=>{console.error(e);process.exitCode=1;}).finally(()=>server.close());
