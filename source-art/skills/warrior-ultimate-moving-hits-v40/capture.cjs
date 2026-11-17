// Real production bundle only. The disposable fixture sets actor memory and advances its real clock.
// No preview.js, profile upload, custom effect, render callback override, or synthetic hit is injected.
const fs=require('node:fs'),path=require('node:path'),http=require('node:http'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'../../..'),cocos=path.join(root,'src/cocos');
const arg=(name,fallback)=>process.argv.includes(name)?process.argv[process.argv.indexOf(name)+1]:fallback;
const build=path.resolve(root,arg('--build','src/cocos/build/concept-2d'));
const cache=path.join(root,'src/.tmp/warrior-ultimate-moving-hits-v40');
const {chromium}=require(path.join(cocos,'node_modules/playwright'));
const main=path.join(build,'assets/main',fs.readdirSync(path.join(build,'assets/main')).find(n=>/^index\..+\.js$/.test(n)));
const gameHash=crypto.createHash('sha256').update(fs.readFileSync(main)).digest('hex');
const server=http.createServer((req,res)=>{const p=decodeURIComponent(new URL(req.url,'http://localhost').pathname),file=path.resolve(build,'.'+(p==='/'?'/index.html':p));if(!file.startsWith(build+path.sep)||!fs.existsSync(file)||!fs.statSync(file).isFile())return res.writeHead(404).end();const mime={'.js':'text/javascript','.json':'application/json','.html':'text/html','.wasm':'application/wasm','.css':'text/css','.png':'image/png','.jpg':'image/jpeg'}[path.extname(file)];if(mime)res.setHeader('Content-Type',mime);fs.createReadStream(file).pipe(res);});
async function run(){
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 const browser=await chromium.launch({headless:true,args:['--enable-webgl','--use-angle=d3d11','--ignore-gpu-blocklist','--mute-audio','--disable-background-timer-throttling','--disable-renderer-backgrounding']});
 try{
  for(const scene of (arg('--scene',null)?[arg('--scene')]:['training','field'])){
   const context=await browser.newContext({viewport:{width:480,height:235},deviceScaleFactor:1}),page=await context.newPage(),errors=[];
   page.on('pageerror',e=>{errors.push(e.message);console.error(e.message);});page.on('console',m=>{if(m.type()==='error'){errors.push(m.text());console.error(m.text().slice(0,220));}});
   await page.goto('http://127.0.0.1:'+server.address().port+'/?view=2d&player=3d');
   await page.waitForFunction(()=>globalThis.System,undefined,{timeout:45000});
   await page.evaluate(()=>{globalThis.findChapter=async()=>{const cc=await System.import('cc');function find(n){return n?.getComponent('ChapterGame')||n?.children.map(find).find(Boolean);}return {app:find(cc.director.getScene()),cc};};});
   const deadline=Date.now()+180000;
   while(true){const ready=await page.evaluate(async()=>{const {app,cc}=await findChapter();if(app?.session&&app?.actors&&app.loading){cc.game.resume();cc.director.tick(1/60);}return !!(app?.session&&app.actors&&!app.loading&&app.platform.auth.ready);});if(ready)break;if(Date.now()>deadline)throw Error('Game startup timeout');await new Promise(r=>setTimeout(r,250));}
   await page.setViewportSize({width:1280,height:624});await page.evaluate(async()=>{const {cc}=await findChapter();cc.view.resizeWithBrowserSize(true);cc.view.setFrameSize(1280,624);cc.game.resume();cc.director.tick(1/60);});
   await page.addScriptTag({content:fs.readFileSync(path.join(__dirname,'review-fixture.js'),'utf8')});await page.evaluate(scene=>installMotionStudy(scene==='training'?'training':'current'),scene);
   await page.evaluate(async()=>{const common=await System.import('chunks:///_virtual/WarriorUltimate.ts');const enemies=await System.import('chunks:///_virtual/EnemyCombat2.ts');globalThis.productionContact=common;globalThis.productionEnemyRadius=enemies.enemyHurtRadius;globalThis.integrationSnapshot=()=>{
    const {app,state,cc}=motionStudy,pool=app.effects.warrior,actor=(app.actors.player??app.actors).active.get('player'),clip=actor.clips[actor.state],animation=clip&&actor.animation.getState(clip.name);
    const main=pool.layers.filter(l=>l.node.active&&/:ultimate-downcut:wave:\d+$/.test(l.key));
    const waves=main.map(l=>{
     const index=Number(l.key.split(':').at(-1)),key=l.key.replace(/:ultimate-downcut:wave:\d+$/,''),cast=pool.ultimateOrigins.get(key);if(!cast)throw Error('Active production wave has no captured cast origin');
     const p=l.renderer.mesh.readAttribute(0,'a_position'),nx=128,nv=16,tipIndex=nx*(nv+1)*3;
     const forward=[Math.sin(cast.angle),0,Math.cos(cast.angle)],position=l.node.worldPosition,launch=cast.position;
     const elapsed=pool.time+1.52-cast.expires,age=elapsed-.018-index*.22;
     let minY=Infinity,maxY=-Infinity;for(let i=1;i<p.length;i+=3){minY=Math.min(minY,p[i]);maxY=Math.max(maxY,p[i]);}
     const vertex=(i,j)=>{const k=(i*(nv+1)+j)*3;return [p[k],p[k+1],p[k+2]];};
     const toWorld=a=>{const v=cc.Vec3.transformMat4(new cc.Vec3(),new cc.Vec3(...a),l.node.worldMatrix);return [v.x,v.y,v.z];};
     const width=(a,b)=>Math.hypot(...a.map((x,i)=>x-b[i])),normal=cc.Vec3.transformQuat(new cc.Vec3(),cc.Vec3.UNIT_X,l.node.worldRotation),scale=l.node.worldScale;
     const tipWorld=toWorld([p[tipIndex],p[tipIndex+1],p[tipIndex+2]]),tailWorld=toWorld(vertex(0,0));
     return {waveIndex:index,key,age,elapsed,position:[position.x,position.y,position.z],launchFoot:[launch.x,launch.y,launch.z],forward,distance:(position.x-launch.x)*forward[0]+(position.z-launch.z)*forward[2],castCount:cast.count,template:l.renderer.mesh.name,material:l.renderer.sharedMaterial.name,effect:l.renderer.sharedMaterial.effectAsset.name,worldScale:[scale.x,scale.y,scale.z],normal:[normal.x,normal.y,normal.z],localTipY:p[tipIndex+1],localHeightRange:[minY,maxY],localOutlineSamples:[0,16,32,48,64,80,96,112,128].flatMap(i=>[0,10].map(j=>vertex(i,j))),tipWidths:[width(vertex(0,0),vertex(0,nv)),width(vertex(nx,0),vertex(nx,nv))],tailWorld,tipWorld,mode:l.phase,flow:Array.from(Object.values(l.renderer.sharedMaterial.getProperty('flowState')??{}))};
    });
    const castOrigins=Array.from(pool.ultimateOrigins,([key,c])=>({key,count:c.count,angle:c.angle,expires:c.expires,position:[c.position.x,c.position.y,c.position.z]}));
    const waveTransforms=pool.layers.filter(l=>/:ultimate-downcut:wave:\d+$/.test(l.key)).map(l=>({key:l.key,position:[l.node.worldPosition.x,l.node.worldPosition.y,l.node.worldPosition.z]}));
    const targets=state.enemies.map(e=>({id:e.id,x:e.x,z:e.z,hp:e.hp,maxHp:e.maxHp,radius:productionEnemyRadius(e),groundHeight:app.world.height(e)}));const pending=state.combat.casts.filter(c=>c.ultimateWaves).map(c=>({castId:c.id,...c.ultimateWaves}));
    return {targets,pending,time:state.time,poolTime:pool.time,waves,sharedMeshForAll:main.every(l=>l.renderer.mesh===main[0].renderer.mesh),warrior:pool.inspect(),castOrigins,waveTransforms,castCacheSize:pool.ultimateOrigins.size,cueCount:app.effects.skills.cues.length,renderReady:pool.layers.filter(l=>l.node.active).every(l=>l.renderer.model?.subModels.length&&l.renderer.model?.worldBounds),pose:{state:actor.state,time:animation?.time,clipDuration:clip?.duration},action:state.action?{id:state.action.skillId,elapsed:state.action.elapsed,duration:state.action.duration}:null};
   };});
   const ranks=arg('--rank',null)?[Number(arg('--rank'))]:(scene==='training'?[1,2,3,4,5]:[5]);
   for(const skillRank of ranks){
    const def={id:'WAR_05',family:'WAR',skillRank,centre:5.5,height:6.9,targets:[[7,0],[9,0],[7,1.6],[-3,0]],seconds:3.6};
    const info=await page.evaluate(async def=>{const r=await motionStudy.select(def);return {...r,fixtureLevel:motionStudy.state.progression.level,skillRank:motionStudy.state.progression.learned.WAR_05};},def);
    const dir=path.join(cache,scene,'rank'+skillRank);fs.mkdirSync(dir,{recursive:true});const metrics=[];
    for(let frame=0;frame<108;frame++){
     const r=await page.evaluate(()=>{const image=motionStudy.next(true);return {image,...integrationSnapshot()};});
     fs.writeFileSync(path.join(dir,String(frame).padStart(3,'0')+'.jpg'),Buffer.from(r.image,'base64'));delete r.image;metrics.push({frame,...r});
     if(!r.renderReady||r.warrior.droppedLayers||!r.sharedMeshForAll)throw Error('Production renderer/pool/shared-mesh failure');
     if(r.waves.some(w=>w.mode!=='ultimate-crescent'||w.template!=='WarriorUltimateCrescentV38'||w.material!=='WarriorUltimateV38'||w.worldScale.some(s=>Math.abs(s-1)>1e-6)))throw Error('Unexpected production ultimate path: '+JSON.stringify(r.waves));
    }
    const report=await page.evaluate(()=>motionStudy.report());
    const naturalCleanup=await page.evaluate(()=>integrationSnapshot());
    const firstContact=metrics.find(m=>m.pending.length)?.pending[0];if(!firstContact)throw Error('Production cast has no ultimateWaves state');
    const contactOracle=await page.evaluate(({cast,targets,events})=>{
     const c=productionContact,settings=c.WARRIOR_ULTIMATE_CONTACT,fx=Math.sin(cast.angle),fz=Math.cos(cast.angle),originHeight=motionStudy.app.world.height(cast.origin);
     const solve=(point,radius)=>{
      const dx=point.x-cast.origin.x,dz=point.z-cast.origin.z,local={forward:dx*fx+dz*fz,side:dx*fz-dz*fx};
      const heightOffset=motionStudy.app.world.height(point)-originHeight;
      let lo=settings.startAge,hi=settings.endAge;const reachable=c.warriorUltimateTouches(local,lo,hi,radius,heightOffset);
      if(reachable)for(let i=0;i<45;i++){const mid=(lo+hi)/2;if(c.warriorUltimateTouches(local,settings.startAge,mid,radius,heightOffset))hi=mid;else lo=mid;}
      return {local,heightOffset,expectedFirstAge:reachable?hi:null};
     };
     return {settings,span:c.warriorUltimateContactSpan(),range:c.warriorUltimateContactRange(),origin:cast.origin,originHeight,angle:cast.angle,startedAt:cast.startedAt,targets:targets.map((t,index)=>({...t,index,role:['7m path','9m path','side control','behind control'][index],...solve(t,t.radius)})),hitContacts:events.filter(e=>e.type==='skill_hit'&&e.phase==='warriorWave').map(e=>{const t=targets.find(t=>t.id===e.target),contact=solve(e.to,t.radius);return {target:e.target,waveIndex:e.waveIndex,waveAge:e.waveAge,position:e.to,...contact,touchesSwept:c.warriorUltimateTouches(contact.local,e.waveAge-.020001,e.waveAge,t.radius,contact.heightOffset)};})};
    },{cast:firstContact,targets:metrics[0].targets,events:report.events});
    const frameStepProbes=await page.evaluate(async def=>{
     const probes=[];
     for(const dt of [1/60,.2]){
      await motionStudy.select(def);motionStudy.castNow();
      const samples=[];let elapsed=0;
      while(elapsed<3-1e-7){const step=Math.min(dt,3-elapsed);motionStudy.advanceOnce(step);elapsed+=step;samples.push({elapsed,...integrationSnapshot()});}
      probes.push({renderStep:dt,logicalSubstepLimit:.02,...motionStudy.report(),finalTargets:integrationSnapshot().targets,samples:samples.map(s=>({time:s.time,elapsed:s.elapsed,targets:s.targets,pending:s.pending}))});
     }
     return probes;
    },def);
    // Separate lifecycle replay. Media above stays uninterrupted and contains no probe edits.
    const lifecycle=await page.evaluate(async({def,scene})=>{
     await motionStudy.select(def);for(let i=0;i<54;i++)motionStudy.next(false);
     const {app,state,cc}=motionStudy,before=integrationSnapshot();
     if(!before.waves.length)throw Error('Lifecycle probe missed live final waves');
     let hudImage=null;
     if(def.skillRank===5){app.hud.root.active=true;app.positionCamera(1);app.update(0);cc.director.tick(0);hudImage=document.getElementById('GameCanvas').toDataURL('image/jpeg',.96).split(',')[1];app.hud.root.active=false;}
     const pauseMenu=scene==='training'?'training-range':'pause';
     app.open(pauseMenu);for(let i=0;i<6;i++)app.update(1/30);
     const paused=integrationSnapshot();
     app.click('close');app.update(0);const restored=integrationSnapshot();
     motionStudy.next(false);const advanced=integrationSnapshot();
     // Actual engine pause: no manual advance while the game is suspended.
     cc.game.pause();const engineBefore=integrationSnapshot();await new Promise(r=>setTimeout(r,150));const engineAfter=integrationSnapshot();
     cc.game.resume();cc.game.pause();motionStudy.next(false);const engineResumed=integrationSnapshot();
     const pool=app.effects.warrior,meshCount=pool.meshes.size,layerCount=pool.layers.length;
     app.session.resetCombatTransient();app.effects.clear();app.effects.update(app.session);app.effects.update(app.session);
     const cleared=integrationSnapshot();
     motionStudy.advanceOnce(.4);const clearedAdvanced=integrationSnapshot();
     return {before,paused,restored,advanced,engineBefore,engineAfter,engineResumed,cleared,clearedAdvanced,hudImage,pauseMenu,trainingPauseModalCovered:scene!=='training',poolCachesRetained:{meshCount,layerCount,meshesAfter:pool.meshes.size,layersAfter:pool.layers.length}};
    },{def,scene});
    if(lifecycle.hudImage)fs.writeFileSync(path.join(dir,'normal-hud.jpg'),Buffer.from(lifecycle.hudImage,'base64'));delete lifecycle.hudImage;
    const result={gameHash,build:path.relative(root,build),scene,skillRank,waveCount:[1,2,2,3,3][skillRank-1],errors,info,productionOnly:true,previewInjected:false,...report,metrics,contactOracle,frameStepProbes,naturalCleanup,lifecycle};
    fs.writeFileSync(path.join(dir,'capture.json'),JSON.stringify(result,null,2));
    console.log('Captured production',scene,'rank',skillRank,'waves',result.waveCount,report.frames,'frames','hits',report.events.filter(e=>e.type==='skill_hit').length);
   }
   if(scene==='training'&&ranks.includes(5)){
    const exitProbe=await page.evaluate(async()=>{
     const def={id:'WAR_05',family:'WAR',skillRank:5,centre:5.5,height:6.9,targets:[[7,0],[9,0],[7,1.6],[-3,0]],seconds:3.6};
     await motionStudy.select(def);for(let i=0;i<54;i++)motionStudy.next(false);
     const {app,cc,state}=motionStudy,oldPool=app.effects.warrior,before=integrationSnapshot(),oldHP=state.enemies.map(e=>[e.id,e.hp]);
     cc.game.resume();await app.leaveTrainingRange();app.enabled=false;cc.game.pause();for(let i=0;i<8;i++){app.update(1/30);cc.director.tick(1/30);}
     return {before,sessionChanged:app.session.state!==state,trainingRangeReleased:!app.trainingRange,oldHP,oldHPAfter:state.enemies.map(e=>[e.id,e.hp]),oldActiveAfter:oldPool.inspect().active.length,oldCastOriginsAfter:oldPool.ultimateOrigins.size,newActiveAfter:app.effects.warrior.inspect().active.length,newCastOriginsAfter:app.effects.warrior.ultimateOrigins.size,newGameplayCastsAfter:app.session.state.combat.casts.length};
    });
    fs.writeFileSync(path.join(cache,scene,'exit-transition.json'),JSON.stringify(exitProbe,null,2));
   }
   if(errors.length)throw Error('Production console errors');await context.close();
  }
 }finally{await browser.close();server.close();}
}
run().catch(e=>{console.error(e);process.exitCode=1;server.close();});
