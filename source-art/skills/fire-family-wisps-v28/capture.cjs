// Records the actual Cocos canvas. No replacement VFX, scene fixture, or camera edits.
const fs=require('node:fs'),path=require('node:path'),http=require('node:http'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'../../..'),cocos=path.join(root,'src/cocos'),build=path.join(cocos,'build/concept-2d');
const {chromium}=require(path.join(cocos,'node_modules/playwright'));
const args=process.argv.slice(2),option=(name,fallback)=>{const i=args.indexOf('--'+name);return i<0?fallback:args[i+1];};
const stage=option('stage','after'),rank=Number(option('rank','1')),only=option('only',''),emptyGround=args.includes('--empty');
if(!/^[a-z0-9-]+$/i.test(stage)||!Number.isInteger(rank)||rank<1||rank>5)throw Error('Invalid stage/rank');
const shots=[
 {id:'FIR_01',name:'赤焰枪',slot:0,seconds:6},
 {id:'FIR_05',name:'焚焰火域',slot:3,seconds:8},
 {id:'FIR_02',name:'陨星天坠',ultimate:true,seconds:9},
 {id:'FIR_04',name:'烈焰喷流',slot:1,seconds:8},
 {id:'FIR_03',name:'焰心护盾',slot:2,seconds:7}
].filter(s=>only?s.id===only:!emptyGround||['FIR_01','FIR_05','FIR_02'].includes(s.id));
if(!shots.length)throw Error('Unknown --only skill');
const recording=stage+(emptyGround?'-empty':'')+'-r'+rank;
const output=path.join(root,'src/.tmp/fire-family-wisps-v28',recording),reports=path.join(__dirname,recording);
fs.mkdirSync(output,{recursive:true});fs.mkdirSync(reports,{recursive:true});
const sha=file=>crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const mainFile=()=>{const dir=path.join(build,'assets/main');return path.join(dir,fs.readdirSync(dir).find(n=>/^index\..+\.js$/.test(n)));};
const gameHash=sha(mainFile()),sourceHashes={};
for(const file of ['SkillFireSprites.ts','SkillMeteorBody.ts','FireGroundEffects.ts','NativeSkillVfx.ts','Effects.ts'])sourceHashes[file]=sha(path.join(cocos,'assets/scripts/features/combat/runtime',file));
const mime={'.js':'text/javascript','.json':'application/json','.html':'text/html','.png':'image/png','.jpg':'image/jpeg','.css':'text/css','.bin':'application/octet-stream','.wasm':'application/wasm'};
const server=http.createServer((req,res)=>{const url=decodeURIComponent(new URL(req.url,'http://127.0.0.1').pathname),file=path.resolve(build,'.'+(url==='/'?'/index.html':url));if(!file.startsWith(build+path.sep)||!fs.existsSync(file)||!fs.statSync(file).isFile()){res.writeHead(404).end();return;}res.setHeader('Content-Type',mime[path.extname(file)]||'application/octet-stream');fs.createReadStream(file).pipe(res);});

async function run(){
 await new Promise(r=>server.listen(0,'127.0.0.1',r));
 const browser=await chromium.launch({headless:true,args:['--enable-webgl','--enable-unsafe-swiftshader','--use-angle=swiftshader','--mute-audio']});
 try{
  const page=await browser.newPage({viewport:{width:1280,height:636},deviceScaleFactor:2}),errors=[],consoleErrors=[];
  page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')consoleErrors.push(m.text());});
  await page.goto('http://127.0.0.1:'+server.address().port+'/?view=2d&player=3d&test=max',{waitUntil:'load'});
  await page.waitForFunction(()=>globalThis.System,undefined,{timeout:60000});
  await page.evaluate(async()=>{const cc=await System.import('cc');globalThis.findRangeApp=()=>{function find(n){return n?.getComponent('ChapterGame')||n?.children.map(find).find(Boolean);}return find(cc.director.getScene());};});
  await page.waitForFunction(()=>{const a=findRangeApp();return a?.session&&a?.actors&&!a.loading&&a.platform.auth.ready;},undefined,{timeout:90000});
  console.log('Opening actual training range',stage,'rank',rank,'bundle',gameHash.slice(0,12));
  await page.evaluate(async(rank)=>{
   const app=findRangeApp();await app.enterTrainingRange();
   if(!app.trainingRange)throw Error('Range entry refused: '+JSON.stringify({failure:app.failure,portrait:!!app.hud.portrait,dialogue:!!app.session.state.dialogue}));
   // Use the existing debug menu action and its resource preparation, exactly
   // as the training menu does. No direct combat-slot or rank mutation.
   app.click('skill-effect-debug');app.click('debug:rank:'+rank);
  },rank);
  await page.waitForFunction(()=>!findRangeApp().loading,undefined,{timeout:90000});
  await page.evaluate(()=>{const app=findRangeApp();app.click('debug:family-rank');});
  await page.waitForFunction(()=>!findRangeApp().loading,undefined,{timeout:90000});
  await page.evaluate(()=>{const app=findRangeApp();app.click('debug:loadout');});
  await page.waitForFunction(()=>!findRangeApp().loading,undefined,{timeout:90000});
  const info=await page.evaluate(async(emptyGround)=>{
   const cc=await System.import('cc'),app=findRangeApp();
   if(emptyGround){
    app.click('training:formation:single');
    while(app.trainingRange.distance!==12)app.click('training:distance');
   }else{app.trainingRange.formation='cluster';app.trainingRange.distance=4;app.resetTrainingRange();}
   app.menu='';app.hud.clearModal();app.hud.root.active=true;app.clearInput(false);app.enabled=false;cc.game.pause();
   const events=[],original=app.process.bind(app);
   app.process=function(batch,...rest){for(const e of batch)if(e.type.startsWith('skill_')||['hit','miss','block'].includes(e.type))events.push({time:app.session.state.time,...JSON.parse(JSON.stringify(e))});return original(batch,...rest);};
   const inspect=()=>{
    const e=app.effects,s=app.session.state;
    return{time:s.time,cameraHeight:app.camera.orthoHeight,ground:e.fireGround.inspect(),fire:e.fireSprites.inspect(),meteor:e.meteor.inspect(),shield:e.shields.inspect(),
     native:{cues:e.skills.cues.map(c=>({kind:c.kind,skillId:c.event.skillId,castId:c.event.castId,start:c.start,duration:c.duration,coolingAt:c.coolingAt})),particles:{allocated:e.emitters.length,active:e.emitters.filter(p=>p.node.active).length},linePool:e.lines.length,bodyPool:e.bodies.length},
     hits:app.trainingRange.hits,damage:app.trainingRange.damage,misses:app.trainingRange.misses,criticalHits:app.trainingRange.criticalHits,
     cooldowns:{...s.combat.cooldowns},ultimateLock:s.combat.ultimateLock,casts:s.combat.casts.map(c=>({id:c.id,skillId:c.skillId,elapsed:c.elapsed,released:c.released,targets:c.targets,hits:c.hits})),projectiles:s.projectiles.filter(p=>p.owner==='player').map(p=>({id:p.id,skillId:p.skillId,x:p.x,z:p.z,age:p.age}))};
   };
   globalThis.familyReview={cc,app,events,inspect,emptyGround,tick(){app.update(1/60);cc.director.tick(1/60);},cast(shot){const p=app.session.state.player,t=this.emptyGround?{x:p.x,z:p.z+4}:app.session.state.enemies.find(e=>e.hp>0);app.pulse={...(shot.ultimate?{ultimate:true}:{combatSlot:shot.slot}),aim:Math.atan2(t.x-p.x,t.z-p.z),target:{x:t.x,z:t.z}};}};
   const player=app.actors.player??app.actors;
   return{area:app.session.state.area,formation:app.trainingRange.formation,distance:app.trainingRange.distance,emptyGround,aimDistance:4,unlimitedResource:app.trainingRange.unlimitedResource,ranks:{...app.session.state.progression.learned},activeSlots:app.session.state.combat.activeSlots,ultimate:app.session.state.combat.ultimate,viewport:[cc.game.canvas.width,cc.game.canvas.height],cameraHeight:app.camera.orthoHeight,player:player.inspect().find(p=>p.id==='player'),cameraBound:app.effects.fireGround.camera===app.camera,loadoutFlow:'ChapterGame.click debug:rank / debug:family-rank / debug:loadout with prepareSkillDebugEffects'};
  },emptyGround);
  const captures=[];
  for(const shot of shots){
   const folder=path.join(output,shot.id);fs.mkdirSync(folder,{recursive:true});
   const start=await page.evaluate(()=>{const r=familyReview,a=r.app;a.resetTrainingRange();a.menu='';a.hud.clearModal();a.hud.root.active=true;a.effects.reducedMotion=false;for(let i=0;i<12;i++)r.tick();r.events.length=0;return r.inspect();});
   const metrics=[],frames=shot.seconds*30;
   for(let frame=0;frame<frames;frame++){
    const data=await page.evaluate(({frame,shot})=>{const r=familyReview;if(frame===12)r.cast(shot);r.tick();r.tick();return{image:r.cc.game.canvas.toDataURL('image/jpeg',.95).split(',')[1],...r.inspect()};},{frame,shot});
    fs.writeFileSync(path.join(folder,String(frame).padStart(3,'0')+'.jpg'),Buffer.from(data.image,'base64'));delete data.image;metrics.push({frame,...data});
   }
   const events=await page.evaluate(()=>familyReview.events),capture={...shot,start,frames,events,metrics};captures.push(capture);
   fs.writeFileSync(path.join(reports,shot.id+'.json'),JSON.stringify(capture,null,2));
   console.log('Recorded',shot.id,shot.seconds+'s',JSON.stringify({hits:metrics.at(-1).hits,damage:metrics.at(-1).damage,release:events.find(e=>e.type==='skill_release')?.time,hitEvents:events.filter(e=>e.type==='hit').length,clearGround:!metrics.at(-1).ground.active.length,clearFire:!metrics.at(-1).fire.active.length}));
  }
  const lifecycle=[];
  for(const shot of emptyGround?[]:shots){
   lifecycle.push(await page.evaluate(shot=>{
    const r=familyReview,a=r.app,s=a.session.state,tick=n=>{for(let i=0;i<n;i++)r.tick();};
    a.resetTrainingRange();a.menu='';a.hud.clearModal();a.effects.reducedMotion=false;r.cast(shot);tick(65);
    const before=r.inspect(),authoritative=()=>JSON.stringify({time:s.time,casts:s.combat.casts,projectiles:s.projectiles,cooldowns:s.combat.cooldowns,shield:s.player.shield});
    const core=authoritative();a.click('training:settings');tick(12);const paused=r.inspect(),pauseStable=core===authoritative();
    a.click('close');tick(1);const resumed=r.inspect();
    a.effects.reducedMotion=true;tick(12);const lowOne=r.inspect();tick(12);const lowTwo=r.inspect();
    a.resetTrainingRange();a.effects.reducedMotion=false;const reset=r.inspect();
    return{id:shot.id,before,paused,pauseStable,resumed,reducedMotionFirst:lowOne,reducedMotionSecond:lowTwo,reset};
   },shot));
   fs.writeFileSync(path.join(reports,'lifecycle.json'),JSON.stringify(lifecycle,null,2));
   console.log('Lifecycle',shot.id,'pauseStable',lifecycle.at(-1).pauseStable);
  }
  // Exercise the existing family buttons, including a same-weapon staff switch
  // and a weapon switch. Do not mutate family, loadouts, or renderer state.
  const switches=[];
  for(const family of emptyGround?[]:['THU','WAR','FIR']){
   const before=await page.evaluate(()=>{const r=familyReview,a=r.app;a.resetTrainingRange();a.menu='';a.hud.clearModal();if(a.session.state.combat.family==='FIR'){r.cast({slot:1});for(let i=0;i<65;i++)r.tick();}return r.inspect();});
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
  const stableBuild=gameHash===sha(mainFile());
  const report={stage,rank,emptyGround,gameHash,sourceHashes,stableBuild,info,errors,consoleErrors,lifecycle,switches,cache:path.relative(root,output),shots:captures.map(({metrics,...s})=>({...s,summary:{hits:metrics.at(-1).hits,damage:metrics.at(-1).damage,misses:metrics.at(-1).misses,criticalHits:metrics.at(-1).criticalHits,last:metrics.at(-1),peakFire:Math.max(...metrics.map(m=>m.fire.active.length)),peakGround:Math.max(...metrics.map(m=>m.ground.active.length))}}))};
  fs.writeFileSync(path.join(reports,'capture.json'),JSON.stringify(report,null,2));
  if(!stableBuild||errors.length||consoleErrors.length)throw Error(JSON.stringify({stableBuild,errors,consoleErrors}));
 }finally{await browser.close();}
}
run().catch(e=>{console.error(e);process.exitCode=1;}).finally(()=>server.close());
