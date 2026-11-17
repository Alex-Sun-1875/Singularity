// Normal training-range update, normal HUD/camera, real skill input. No VFX overrides.
const fs=require('node:fs'),path=require('node:path'),http=require('node:http'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'../../..'),cocos=path.join(root,'src/cocos'),build=path.join(cocos,'build/concept-2d');
const {chromium}=require(path.join(cocos,'node_modules/playwright'));
const output=path.join(root,'src/.tmp/fire-seal-original-pixels-v25');fs.mkdirSync(output,{recursive:true});
const mainDir=path.join(build,'assets/main'),main=fs.readdirSync(mainDir).find(n=>/^index\..+\.js$/.test(n)),gameHash=crypto.createHash('sha256').update(fs.readFileSync(path.join(mainDir,main))).digest('hex');
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
  console.log('Opening normal training range',gameHash.slice(0,12));
  const info=await page.evaluate(async()=>{
   const cc=await System.import('cc'),app=findRangeApp();
   await app.enterTrainingRange();if(!app.trainingRange)throw Error('Range entry refused: '+JSON.stringify({failure:app.failure,portrait:!!app.hud.portrait,dialogue:!!app.session.state.dialogue,campaign:app.campaignView?.active}));
   app.trainingRange.formation='cluster';app.trainingRange.distance=4;app.resetTrainingRange();
   app.menu='';app.hud.clearModal();app.hud.root.active=true;app.clearInput(false);app.enabled=false;
   cc.game.pause();const events=[],original=app.process.bind(app);
   app.process=function(batch,...rest){for(const e of batch)if(['skill_cast','skill_release','skill_hit','skill_zone','skill_end'].includes(e.type))events.push({time:app.session.state.time,type:e.type,skill:e.skillId,target:e.targetId,segment:e.segment});return original(batch,...rest);};
   globalThis.rangeReview={cc,app,events,tick(){app.update(1/60);cc.director.tick(1/60);},cast(){const p=app.session.state.player,t=app.session.state.enemies.find(e=>e.hp>0);app.pulse={combatSlot:1,aim:Math.atan2(t.x-p.x,t.z-p.z),target:{x:t.x,z:t.z}};}};
   for(let i=0;i<12;i++)rangeReview.tick();
   const player=app.actors.player??app.actors;
   return{area:app.session.state.area,formation:app.trainingRange.formation,rank:app.session.state.progression.learned.FIR_04,activeSlots:app.session.state.combat.activeSlots,viewport:[cc.game.canvas.width,cc.game.canvas.height],cameraHeight:app.camera.orthoHeight,player:player.inspect().find(p=>p.id==='player'),cameraBound:app.effects.fireGround.camera===app.camera};
  });
  const metrics=[];for(let frame=0;frame<240;frame++){
   const data=await page.evaluate(frame=>{const r=rangeReview;if(frame===12)r.cast();r.tick();r.tick();return{image:r.cc.game.canvas.toDataURL('image/jpeg',.95).split(',')[1],time:r.app.session.state.time,cameraHeight:r.app.camera.orthoHeight,ground:r.app.effects.fireGround.inspect(),flowTime:r.app.effects.fireGround.surfaces.filter(s=>s.kind==='jets'&&s.node.active).map(s=>s.material.getProperty('surfaceState').y),hits:r.app.trainingRange.hits,damage:r.app.trainingRange.damage};},frame);
   fs.writeFileSync(path.join(output,String(frame).padStart(3,'0')+'.jpg'),Buffer.from(data.image,'base64'));delete data.image;metrics.push({frame,...data});
   if(frame===36&&process.argv.includes('--study')){
    for(const transfer of [0,.5,1]){
     const image=await page.evaluate(transfer=>{const r=rangeReview;for(const s of r.app.effects.fireGround.surfaces.filter(s=>s.node.active&&s.kind!=='meteorSeal')){const state=s.material.getProperty('surfaceState').clone();state.w=transfer;s.material.setProperty('surfaceState',state);}r.cc.director.tick(0);return r.cc.game.canvas.toDataURL('image/jpeg',.95).split(',')[1];},transfer);
     fs.writeFileSync(path.join(output,'transfer-'+transfer+'.jpg'),Buffer.from(image,'base64'));
    }
    await page.evaluate(()=>{for(const s of rangeReview.app.effects.fireGround.surfaces.filter(s=>s.node.active&&s.kind!=='meteorSeal')){const state=s.material.getProperty('surfaceState').clone();state.w=0;s.material.setProperty('surfaceState',state);}rangeReview.cc.director.tick(0);});
   }
  }
  const events=await page.evaluate(()=>rangeReview.events);
  const lifecycle=await page.evaluate(()=>{const r=rangeReview,a=r.app,s=a.session.state;function tick(n){for(let i=0;i<n;i++)r.tick();}a.resetTrainingRange();a.menu='';a.hud.clearModal();r.cast();tick(65);const before=JSON.stringify(s.combat.casts),time=s.time;a.effects.clear(true);a.effects.update(a.session);const pauseRestored=a.effects.fireGround.inspect();const unchanged=before===JSON.stringify(s.combat.casts)&&time===s.time;a.effects.reducedMotion=true;tick(12);const first=a.effects.fireGround.inspect();tick(12);const second=a.effects.fireGround.inspect();a.effects.clear();return{unchanged,pauseRestored,reducedMotionFirst:first,reducedMotionSecond:second,cleared:a.effects.fireGround.inspect()};});
  fs.writeFileSync(path.join(__dirname,'capture.json'),JSON.stringify({gameHash,info,errors,consoleErrors,events,metrics,lifecycle},null,2));
  if(errors.length||consoleErrors.length)throw Error(JSON.stringify({errors,consoleErrors}));
  console.log('Recorded normal range',JSON.stringify({frames:metrics.length,hits:metrics.at(-1).hits,damage:metrics.at(-1).damage,cameraBound:info.cameraBound}));
 }finally{await browser.close();}
}
run().catch(e=>{console.error(e);process.exitCode=1;}).finally(()=>server.close());
