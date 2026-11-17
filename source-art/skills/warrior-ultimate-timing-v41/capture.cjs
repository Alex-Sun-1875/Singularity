// One native production timing recording. No preview, effect, profile or damage overrides.
const fs=require('node:fs'),path=require('node:path'),http=require('node:http'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'../../..'),build=path.join(root,'src/cocos/build/concept-2d');
const out=path.join(root,'src/.tmp/warrior-ultimate-timing-v41/training/rank5');fs.mkdirSync(out,{recursive:true});
const {chromium}=require(path.join(root,'src/cocos/node_modules/playwright'));
const main=path.join(build,'assets/main',fs.readdirSync(path.join(build,'assets/main')).find(n=>/^index\..+\.js$/.test(n))),gameHash=crypto.createHash('sha256').update(fs.readFileSync(main)).digest('hex');
const server=http.createServer((req,res)=>{const p=decodeURIComponent(new URL(req.url,'http://localhost').pathname),file=path.resolve(build,'.'+(p==='/'?'/index.html':p));if(!file.startsWith(build+path.sep)||!fs.existsSync(file)||!fs.statSync(file).isFile())return res.writeHead(404).end();const mime={'.js':'text/javascript','.json':'application/json','.html':'text/html','.wasm':'application/wasm','.css':'text/css','.png':'image/png','.jpg':'image/jpeg'}[path.extname(file)];if(mime)res.setHeader('Content-Type',mime);fs.createReadStream(file).pipe(res);});
async function run(){
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 const browser=await chromium.launch({headless:true,args:['--enable-webgl','--use-angle=d3d11','--ignore-gpu-blocklist','--mute-audio','--disable-background-timer-throttling','--disable-renderer-backgrounding']});
 try{
  const page=await browser.newPage({viewport:{width:480,height:235},deviceScaleFactor:1}),errors=[];
  page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
  await page.goto('http://127.0.0.1:'+server.address().port+'/?view=2d&player=3d');
  await page.waitForFunction(()=>globalThis.System,undefined,{timeout:45000});
  await page.evaluate(()=>{globalThis.findChapter=async()=>{const cc=await System.import('cc');function find(n){return n?.getComponent('ChapterGame')||n?.children.map(find).find(Boolean);}return {app:find(cc.director.getScene()),cc};};});
  const deadline=Date.now()+180000;
  while(true){const ready=await page.evaluate(async()=>{const {app,cc}=await findChapter();if(app?.session&&app?.actors&&app.loading){cc.game.resume();cc.director.tick(1/60);}return !!(app?.session&&app.actors&&!app.loading&&app.platform.auth.ready);});if(ready)break;if(Date.now()>deadline)throw Error('Startup timed out');await new Promise(r=>setTimeout(r,250));}
  await page.setViewportSize({width:1280,height:624});await page.evaluate(async()=>{const {cc}=await findChapter();cc.view.resizeWithBrowserSize(true);cc.view.setFrameSize(1280,624);cc.game.resume();cc.director.tick(1/60);});
  await page.addScriptTag({content:fs.readFileSync(path.join(__dirname,'review-fixture.js'),'utf8')});await page.evaluate(()=>installMotionStudy('training'));
  const parameters=await page.evaluate(async()=>{const p=await System.import('chunks:///_virtual/WarriorUltimate.ts');globalThis.nativeTiming=p.WARRIOR_ULTIMATE;return {pulseInterval:nativeTiming.pulseInterval,launchDelay:nativeTiming.launchDelay,visualDuration:nativeTiming.visualDuration,waveLife:nativeTiming.waveLife,rankWaveCounts:nativeTiming.rankWaveCounts};});
  const info=await page.evaluate(async()=>motionStudy.select({id:'WAR_05',family:'WAR',skillRank:5,centre:5.5,height:6.9,targets:[[7,0],[9,0],[7,1.6],[-3,0]],seconds:2.8}));
  const metrics=[];
  for(let frame=0;frame<84;frame++){
   const r=await page.evaluate(()=>{
    const image=motionStudy.next(true),{app,state}=motionStudy,pool=app.effects.warrior,p=nativeTiming;
    const layers=pool.layers.filter(l=>l.node.active&&/:ultimate-downcut:wave:\d+$/.test(l.key));
    const waves=layers.map(l=>{const waveIndex=Number(l.key.split(':').at(-1)),key=l.key.replace(/:ultimate-downcut:wave:\d+$/,''),cast=pool.ultimateOrigins.get(key),elapsed=pool.time+p.visualDuration-cast.expires,age=elapsed-p.launchDelay-waveIndex*p.pulseInterval,q=l.node.worldPosition;return {waveIndex,age,time:state.time,estimatedLaunch:state.time-age,position:[q.x,q.y,q.z],scale:[l.node.worldScale.x,l.node.worldScale.y,l.node.worldScale.z],template:l.renderer.mesh.name,material:l.renderer.sharedMaterial.name};});
    return {image,time:state.time,waves,sharedMeshForAll:layers.every(l=>l.renderer.mesh===layers[0].renderer.mesh),renderReady:pool.layers.filter(l=>l.node.active).every(l=>l.renderer.model?.subModels.length&&l.renderer.model?.worldBounds),pool:pool.inspect(),targets:state.enemies.map(t=>({id:t.id,hp:t.hp,maxHp:t.maxHp}))};
   });
   fs.writeFileSync(path.join(out,String(frame).padStart(3,'0')+'.jpg'),Buffer.from(r.image,'base64'));delete r.image;metrics.push({frame,...r});
   if(!r.renderReady||r.pool.droppedLayers||!r.sharedMeshForAll)throw Error('Production render failure');
  }
  const report=await page.evaluate(()=>motionStudy.report()),firsts=[];
  for(let i=0;i<3;i++){const m=metrics.find(m=>m.waves.some(w=>w.waveIndex===i));if(!m)throw Error('Missing wave '+i);firsts.push({waveIndex:i,frame:m.frame,...m.waves.find(w=>w.waveIndex===i)});}
  const launches=firsts.map(w=>w.estimatedLaunch),intervals=launches.slice(1).map((t,i)=>t-launches[i]);
  if(intervals.some(t=>Math.abs(t-parameters.pulseInterval)>1e-6))throw Error('Wave spacing differs from production shared constant');
  const hits=report.events.filter(e=>e.type==='skill_hit'&&e.phase==='warriorWave'),keys=hits.map(e=>e.waveIndex+':'+e.target);
  if(hits.length!==6||new Set(keys).size!==6||errors.length)throw Error('Unexpected native hits/errors');
  const representative=metrics.find(m=>m.frame===54&&m.waves.length===3)??metrics.find(m=>m.waves.length===3);
  fs.copyFileSync(path.join(out,String(representative.frame).padStart(3,'0')+'.jpg'),path.join(__dirname,'representative.jpg'));
  const result={gameHash,build:path.relative(root,build),productionOnly:true,previewInjected:false,skillRank:5,parameters,info,...report,errors,metrics,firstAppearances:firsts,estimatedLaunchIntervals:intervals,hitCount:hits.length,representativeFrame:representative.frame};
  fs.writeFileSync(path.join(out,'capture.json'),JSON.stringify(result,null,2));
  fs.writeFileSync(path.join(__dirname,'provenance.json'),JSON.stringify({status:'production timing verified; root visual review pending',gameHash,productionOnly:true,parameters,frames:84,fps:30,firstAppearances:firsts,estimatedLaunchIntervals:intervals,realWaveHitCount:hits.length,realHits:hits,representativeFrame:representative.frame,errors,scope:'single training rank5 timing check only; v40 geometry/damage/lifecycle validation not repeated'},null,2));
  console.log(JSON.stringify({gameHash,parameters,firstAppearances:firsts.map(w=>({waveIndex:w.waveIndex,frame:w.frame,time:w.time,estimatedLaunch:w.estimatedLaunch})),estimatedLaunchIntervals:intervals,realWaveHitCount:hits.length,representativeFrame:representative.frame}));
 }finally{await browser.close();server.close();}
}
run().catch(e=>{console.error(e);process.exitCode=1;server.close();});
