const fs=require('node:fs'),path=require('node:path'),http=require('node:http'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'../../..'),cocos=path.join(root,'src/cocos'),build=path.join(cocos,'build/concept-2d');
const {chromium}=require(path.join(cocos,'node_modules/playwright'));
const cache=path.join(root,'src/.tmp/archer-polish-v5');
const args=process.argv.slice(2),integrated=args.includes('--integrated'),variant=integrated?'integrated':args.includes('--refined')?'refined':'current',probe=args.includes('--probe');
const formation=[[4.9,.05],[6.4,-1.15],[5.65,1.4],[7.35,.42]];
const shots={
 BASIC_BOW:{id:'BASIC_WAR',family:'BOW',centre:2.7,height:2.90,targets:[[5.4,.05]],seconds:2.1,rank:1},
 BOW_02_R1:{id:'BOW_02',family:'BOW',centre:3.15,height:3.10,targets:formation,seconds:2.1,rank:1},
 BOW_02_R3:{id:'BOW_02',family:'BOW',centre:3.15,height:3.10,targets:formation,seconds:2.4,rank:3},
};
const selected=args.includes('--shots')?args[args.indexOf('--shots')+1].split(','):Object.keys(shots);
const frozen=path.join(cache,'inputs'),manifestFile=path.join(frozen,'manifest.json');
const manifest=!integrated&&fs.existsSync(manifestFile)?JSON.parse(fs.readFileSync(manifestFile)):null;
const mainName=manifest?path.basename(manifest.mainURL):fs.readdirSync(path.join(build,'assets/main')).find(n=>/^index\..+\.js$/.test(n));
const mainURL='/assets/main/'+mainName,original=fs.readFileSync(manifest?path.join(frozen,'main.js'):path.join(build,'assets/main',mainName),'utf8');
const hash=x=>crypto.createHash('sha256').update(x).digest('hex');
const main=integrated?original:require('./refine-modules.cjs').replaceModules(original,cocos,variant==='refined',manifest?frozen:undefined);
const inputs=manifest?manifest.sourceHashes:Object.fromEntries(['Effects','NativeSkillVfx','SkillEnergyStrokes'].map(n=>[n,hash(fs.readFileSync(path.join(cocos,'assets/scripts/features/combat/runtime',n+'.ts')))]));
const mime={'.js':'text/javascript','.json':'application/json','.html':'text/html','.png':'image/png','.jpg':'image/jpeg','.css':'text/css','.wasm':'application/wasm'};
let mainRequests=0;
const server=http.createServer((request,response)=>{
 const url=decodeURIComponent(new URL(request.url,'http://127.0.0.1').pathname),file=path.resolve(build,'.'+(url==='/'?'/index.html':url));
 if(!file.startsWith(build+path.sep)||!fs.existsSync(file)||!fs.statSync(file).isFile()){response.writeHead(404).end();return;}
 response.setHeader('Content-Type',mime[path.extname(file)]||'application/octet-stream');
 if(url===mainURL){mainRequests++;response.end(main);}else fs.createReadStream(file).pipe(response);
});
function edit(s,a,b){if(s.split(a).length!==2)throw Error('Fixture changed '+a);return s.replace(a,b);}
async function run(){
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 const graphics=args.includes('--hardware')?['--ignore-gpu-blocklist','--use-angle=d3d11']:['--enable-unsafe-swiftshader','--use-angle=swiftshader'];
 const browser=await chromium.launch({headless:true,args:['--enable-webgl',...graphics,'--mute-audio']});
 try{
  const page=await browser.newPage({viewport:{width:960,height:470},deviceScaleFactor:1}),errors=[],messages=[];
  page.on('pageerror',e=>{errors.push(e.message);console.error(e.message);});
  page.on('console',m=>{if(['warning','error'].includes(m.type()))messages.push(m.text());});
  await page.goto('http://127.0.0.1:'+server.address().port+'/?view=3d&player=3d&test=max',{waitUntil:'load'});
  await page.waitForFunction(()=>globalThis.System,undefined,{timeout:45000});
  await page.evaluate(async()=>{const cc=await System.import('cc');globalThis.findCurrentChapter=()=>{function find(n){return n?.getComponent('ChapterGame')||n?.children.map(find).find(Boolean);}return find(cc.director.getScene());};});
  if(args.includes('--pump'))await page.evaluate(async()=>{
   const cc=await System.import('cc');cc.game.pause();
   // Reuse the existing native review warmup clock. Gameplay recording retains 60 Hz.
   globalThis.archerBootPump=setInterval(()=>{if(cc.director.root)cc.director.tick(1/60);},100);
  });
  if(args.includes('--diagnose')){
   try{await page.waitForFunction(()=>{const a=findCurrentChapter();return a?.session&&a?.actors&&!a.loading&&a.platform.auth.ready;},undefined,{timeout:15000});}catch{}
   const diagnostic=path.join(cache,'diagnostic');fs.mkdirSync(diagnostic,{recursive:true});
   await page.screenshot({path:path.join(diagnostic,'screen.png')});
   const status=await page.evaluate(async()=>{const a=findCurrentChapter(),cc=await System.import('cc');return {chapter:!!a,session:!!a?.session,actors:!!a?.actors,loading:a?.loading,authReady:a?.platform?.auth?.ready,failure:a?.failure,background:a?.background,hidden:document.hidden,paused:cc.game.isPaused(),frames:cc.director.getTotalFrames(),effects:a?.effects?.preparedFamily,warmup:!!a?.world?.root?.getChildByName('CombatShaderWarmup'),glyphs:a?.enemyFeedback?.texts?.length,preparation:a?.preparationResources?.inspect(),text:document.body.innerText};});
   console.log('Console',JSON.stringify(messages.slice(-12)));
   console.log('Diagnostic',JSON.stringify(status,null,2));
   return;
  }
  await page.waitForFunction(()=>{const a=findCurrentChapter();return a?.session&&a?.actors&&!a.loading&&a.platform.auth.ready;},undefined,{timeout:180000});
  let fixture=fs.readFileSync(path.join(__dirname,'../cocos-motion-study-v2/review-fixture.js'),'utf8');
  fixture=edit(fixture,'+.13;','+.67;');
  fixture=edit(fixture,"attack:shot.id==='BASIC_WAR'&&time>=start&&time<start+.92","attack:shot.id==='BASIC_WAR'&&((time>=start&&time<start+.14)||(time>=start+.66&&time<start+.80))");
  fixture=edit(fixture,'skill:e.skillId,id:e.id','skill:e.skillId,rank:e.rank,phase:e.phase,projectileId:e.projectileId,id:e.id');
  fixture=edit(fixture,'COMBAT_SKILLS[def.id]?.ranks[0]?.geometry','COMBAT_SKILLS[def.id]?.ranks[(def.rank??1)-1]?.geometry');
  await page.addScriptTag({content:fixture});await page.evaluate(()=>installMotionStudy('current'));
  if(args.includes('--pump'))await page.evaluate(()=>{clearInterval(globalThis.archerBootPump);globalThis.archerBootPump=undefined;});
  if(!mainRequests)throw Error('Capture did not load the selected Cocos bundle');
  if(integrated&&!await page.evaluate(()=>Array.isArray(motionStudy.app.effects.skills.arrowLegs)))throw Error('Native build is missing integrated arrow effects');
  console.log('Ready',variant,hash(original).slice(0,12));
  for(const name of selected){
   const shot=shots[name];if(!shot)throw Error('Unknown shot '+name);
   await page.evaluate(rank=>{motionStudy.state.progression.learned.BOW_02=rank;},shot.rank);
   const info=await page.evaluate(def=>motionStudy.select(def),shot);
   const presentation=await page.evaluate(()=>{const a=motionStudy.app;return {camera:{position:a.camera.node.worldPosition,forward:a.camera.node.forward,orthoHeight:a.camera.orthoHeight},actorCount:a.actors.inspect().length};});
   const directory=path.join(cache,probe?'probe':'final',variant,name);fs.mkdirSync(directory,{recursive:true});
   console.log('Recording',variant,name,info.renderer,JSON.stringify(info.origin));
   let maxArrowLegs=0;
   for(let i=0;i<Math.round(shot.seconds*30);i++){
    const save=!probe||[0,12,16,19,22,25,28,31,34,38,45,54,65].includes(i);
    const sample=await page.evaluate(save=>({jpg:motionStudy.next(save),legs:motionStudy.app.effects.skills.arrowLegs?.length??0}),save);
    const jpg=sample.jpg;maxArrowLegs=Math.max(maxArrowLegs,sample.legs);
    if(jpg)fs.writeFileSync(path.join(directory,String(i).padStart(3,'0')+'.jpg'),Buffer.from(jpg,'base64'));
   }
   const report=await page.evaluate(()=>motionStudy.report());
   if(errors.length)throw Error(errors.join('\n'));
   if(!info.player?.skeletons?.length)throw Error('Missing native skeleton');
   if(shot.id==='BOW_02'&&!report.events.some(e=>e.type==='skill_segment'&&e.phase==='redirect'))throw Error('Missing real chain redirect');
   let cleanup;
   if(integrated){
    if(shot.id==='BOW_02'&&maxArrowLegs!==(shot.rank===3?3:1))throw Error('Missing completed arrow legs '+name+': '+maxArrowLegs);
    cleanup=await page.evaluate(()=>{const skills=motionStudy.app.effects.skills;skills.clear(true);return {legs:skills.arrowLegs.length,trails:skills.trails.size};});
    if(cleanup.legs||cleanup.trails)throw Error('Transient arrow effects survived clear');
   }
   fs.writeFileSync(path.join(directory,'capture.json'),JSON.stringify({variant,name,info,presentation,gameHash:hash(original),sourceHashes:inputs,reviewHash:hash(fs.readFileSync(path.join(__dirname,'refine-modules.cjs'))),mainURL,integrated,mainRequests,maxArrowLegs,cleanup,errors,...report},null,2));
   console.log('Captured',variant,name,report.frames,JSON.stringify(report.stats),'redirects',report.events.filter(e=>e.phase==='redirect').length,'ranks',JSON.stringify([...new Set(report.events.map(e=>e.rank).filter(Boolean))]));
  }
 }finally{await browser.close();}
}
run().catch(e=>{console.error(e);process.exitCode=1;}).finally(()=>server.close());
