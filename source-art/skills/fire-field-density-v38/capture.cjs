// Reuses the native training range and the v30 recorder's fixed-step canvas capture.
// Fresh browser storage; no campaign progression, camera, damage or VFX overrides.
const fs=require('node:fs'),path=require('node:path'),http=require('node:http'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'../../..'),cocos=path.join(root,'src/cocos'),build=process.argv[3]?path.resolve(root,process.argv[3]):path.join(cocos,'build/concept-2d');
const stage=process.argv[2]||'before';if(!/^[a-z0-9-]+$/i.test(stage))throw Error('Invalid stage');
const out=path.join(root,'src/.tmp/fire-field-density-v38',stage),reportDir=path.join(__dirname,stage);
fs.mkdirSync(out,{recursive:true});fs.mkdirSync(reportDir,{recursive:true});
const {chromium}=require(path.join(cocos,'node_modules/playwright'));
const sha=file=>crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const mainDir=path.join(build,'assets/main'),main=path.join(mainDir,fs.readdirSync(mainDir).find(n=>/^index\..+\.js$/.test(n))),mainHash=sha(main);
const sourceFiles=['assets/scripts/features/combat/runtime/FireFieldEffects.ts','assets/resources/vfx/production/fire-field-v30.effect','assets/resources/vfx/production/fire-field-flow-v30.png'];
const sources=Object.fromEntries(sourceFiles.map(f=>[f,sha(path.join(cocos,f))]));
const server=http.createServer((req,res)=>{const p=decodeURIComponent(new URL(req.url,'http://localhost').pathname),file=path.resolve(build,'.'+(p==='/'?'/index.html':p));if(!file.startsWith(build+path.sep)||!fs.existsSync(file)||!fs.statSync(file).isFile())return res.writeHead(404).end();const mime={'.js':'text/javascript','.json':'application/json','.html':'text/html','.wasm':'application/wasm','.css':'text/css','.png':'image/png','.jpg':'image/jpeg'}[path.extname(file)];if(mime)res.setHeader('Content-Type',mime);fs.createReadStream(file).pipe(res);});
async function run(){
 await new Promise(r=>server.listen(0,'127.0.0.1',r));
 const browser=await chromium.launch({headless:true,args:['--enable-webgl','--use-angle=d3d11','--ignore-gpu-blocklist','--mute-audio','--disable-background-timer-throttling','--disable-renderer-backgrounding']});
 try{
  const page=await browser.newPage({viewport:{width:960,height:448},deviceScaleFactor:1.5}),errors=[];
  page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
  await page.goto('http://127.0.0.1:'+server.address().port+'/?view=2d&player=3d');
  await page.waitForFunction(()=>globalThis.System,undefined,{timeout:45000});
  await page.evaluate(async()=>{const cc=await System.import('cc');globalThis.findRangeApp=()=>{function find(n){return n?.getComponent('ChapterGame')||n?.children.map(find).find(Boolean);}return find(cc.director.getScene());};});
  const waitReady=async(predicate)=>{const end=Date.now()+120000;while(true){const ready=await page.evaluate(predicate);if(ready)return;if(Date.now()>end)throw Error('Scene load timed out');await new Promise(r=>setTimeout(r,150));}};
  await waitReady(async()=>{const cc=await System.import('cc'),a=findRangeApp();if(a?.session&&a?.actors&&a.loading){cc.game.resume();cc.director.tick(1/60);}return !!(a?.session&&a?.actors&&!a.loading&&a.platform.auth.ready);});
  const journey=await page.evaluate(()=>{const a=findRangeApp();globalThis.originalJourney={session:a.session,progression:JSON.stringify(a.session.state.progression)};return {level:a.session.state.progression.level,temporaryMax:a.temporaryMax,menu:a.menu};});
  if(journey.level!==1||journey.temporaryMax)throw Error('Expected normal fresh level-1 test journey');
  await page.evaluate(()=>findRangeApp().click('training:enter'));
  await waitReady(async()=>{const cc=await System.import('cc'),a=findRangeApp();cc.game.resume();cc.director.tick(1/60);return !!a.trainingRange&&!a.loading;});
  await page.evaluate(()=>{const a=findRangeApp();a.click('skill-effect-debug');a.click('debug:rank:1');a.click('debug:family-rank');a.click('debug:loadout');});
  await waitReady(async()=>{const cc=await System.import('cc'),a=findRangeApp();cc.game.resume();cc.director.tick(1/60);return !a.loading;});
  await page.evaluate(async()=>{
   const cc=await System.import('cc'),a=findRangeApp(),events=[],original=a.process.bind(a);
   a.process=function(batch,...rest){events.push(...batch.filter(e=>e.type.startsWith('skill_')||['hit','miss','block'].includes(e.type)).map(e=>({time:a.session.state.time,...JSON.parse(JSON.stringify(e))})));return original(batch,...rest);};
   globalThis.fieldReview={cc,a,events,tick(){a.update(1/60);cc.director.tick(1/60);}};
  });
  const captures=[];
  for(const mode of ['empty','targets','reduced']){
   const setup=await page.evaluate(mode=>{
    const r=fieldReview,{a,cc}=r;cc.game.resume();a.click('training:formation:'+ (mode==='targets'?'cluster':'single'));
    const distance=mode==='targets'?4:12;for(let i=0;a.trainingRange.distance!==distance&&i<10;i++)a.click('training:distance');
    a.click('training:reset');a.click('close');a.enabled=false;a.effects.reducedMotion=mode==='reduced';a.clearInput(false);
    for(let i=0;i<12;i++)r.tick();r.events.length=0;cc.game.pause();
    return {area:a.session.state.area,level:a.session.state.progression.level,rank:a.session.state.progression.learned.FIR_05,cameraHeight:a.camera.orthoHeight,slots:a.session.state.combat.activeSlots,separateSession:a.session!==originalJourney.session,viewport:[cc.game.canvas.width,cc.game.canvas.height]};
   },mode);
   const folder=path.join(out,mode);fs.mkdirSync(folder,{recursive:true});const metrics=[];
   for(let frame=0;frame<210;frame++){
    const data=await page.evaluate(({frame,mode})=>{
     const r=fieldReview,{a,cc}=r;cc.game.resume();
     if(frame===12){const p=a.session.state.player,angle=-Math.PI/6,t=mode==='targets'?a.session.state.enemies.find(e=>e.hp>0):{x:p.x+Math.sin(angle)*4,z:p.z+Math.cos(angle)*4};a.pulse={combatSlot:3,aim:Math.atan2(t.x-p.x,t.z-p.z),target:{x:t.x,z:t.z}};}
     r.tick();r.tick();const field=a.effects.fireSprites.inspect().field;
     const fields=field.active.map(f=>{const cue=a.effects.skills.cues.find(c=>c.event.skillId==='FIR_05'),angle=cue?.event.angle??0,corners=[];for(const side of [-1,1])for(const front of [-1,1]){const x=f.position.x+Math.cos(angle)*side*f.width/2+Math.sin(angle)*front*f.depth/2,z=f.position.z-Math.sin(angle)*side*f.width/2+Math.cos(angle)*front*f.depth/2,v=a.camera.worldToScreen(new cc.Vec3(x,a.world.height({x,z})+.1,z));corners.push({x:v.x,y:cc.game.canvas.height-v.y});}return {...f,corners,renderReady:a.effects.fireSprites.field.fields.some(n=>n.key===f.key&&!!n.renderer.model?.subModels?.length)};});
     const device=cc.director.root.device,s=a.session.state,image=frame%3===0?cc.game.canvas.toDataURL('image/png').split(',')[1]:null;cc.game.pause();
     return {image,frame,time:s.time,fields,drawCalls:device.numDrawCalls,triangles:device.numTris,hits:a.trainingRange.hits,damage:a.trainingRange.damage,cooldown:s.combat.cooldowns.FIR_05??0};
    },{frame,mode});
    if(data.image)fs.writeFileSync(path.join(folder,String(frame).padStart(3,'0')+'.png'),Buffer.from(data.image,'base64'));delete data.image;metrics.push(data);
   }
   const events=await page.evaluate(()=>fieldReview.events),capture={mode,setup,events,metrics};captures.push(capture);
   fs.writeFileSync(path.join(reportDir,mode+'.json'),JSON.stringify(capture,null,2));
   console.log(JSON.stringify({stage,mode,hits:metrics.at(-1).hits,damage:metrics.at(-1).damage,activeFrames:metrics.filter(m=>m.fields.length).length,finalFields:metrics.at(-1).fields.length}));
  }
  const journeyPreserved=await page.evaluate(()=>JSON.stringify(originalJourney.session.state.progression)===originalJourney.progression),stableBuild=sha(main)===mainHash;
  fs.writeFileSync(path.join(reportDir,'capture.json'),JSON.stringify({stage,servedBuild:path.relative(root,build),mainHash,sources,journey,journeyPreserved,stableBuild,errors,cache:path.relative(root,out),captures:captures.map(({metrics,...c})=>({...c,last:metrics.at(-1)}))},null,2));
  if(errors.length||!stableBuild||!journeyPreserved||captures.some(c=>!c.metrics.some(m=>m.fields.some(f=>f.renderReady))||c.metrics.at(-1).fields.length))throw Error('Capture validation failed: '+JSON.stringify(errors));
 }finally{await browser.close();server.close();}
}
run().catch(e=>{console.error(e);process.exitCode=1;server.close();});
