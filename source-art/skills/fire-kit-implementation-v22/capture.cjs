// Actual freshly compiled Cocos game. No module/texture HTTP overrides.
const fs=require('node:fs'),path=require('node:path'),http=require('node:http'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'../../..'),cocos=path.join(root,'src/cocos'),build=path.join(cocos,'build/concept-2d');
const {chromium}=require(path.join(cocos,'node_modules/playwright'));
const probe=process.argv.includes('--probe'),hash=v=>crypto.createHash('sha256').update(v).digest('hex');
const mainDir=path.join(build,'assets/main'),mainName=fs.readdirSync(mainDir).find(x=>/^index\..+\.js$/.test(x)),gameHash=hash(fs.readFileSync(path.join(mainDir,mainName)));
const mime={'.js':'text/javascript','.json':'application/json','.html':'text/html','.png':'image/png','.jpg':'image/jpeg','.css':'text/css','.bin':'application/octet-stream','.wasm':'application/wasm'};
const server=http.createServer((request,response)=>{
 const url=decodeURIComponent(new URL(request.url,'http://127.0.0.1').pathname),file=path.resolve(build,'.'+(url==='/'?'/index.html':url));
 if(!file.startsWith(build+path.sep)||!fs.existsSync(file)||!fs.statSync(file).isFile()){response.writeHead(404).end();return;}
 response.setHeader('Content-Type',mime[path.extname(file)]||'application/octet-stream');fs.createReadStream(file).pipe(response);
});
const shots=[
 {id:'FIR_04',centre:3.3,height:3.4,targets:[[2,.03],[4.5,.1],[6.1,-.3],[5,1.6]],seconds:7},
 {id:'FIR_02',centre:3.1,height:4.5,targets:[[4.7,.1],[5.85,-.85],[5.3,1.35],[7.35,.42]],seconds:6.5},
 {id:'FIR_05',centre:3.1,height:3.75,targets:[[4.9,.05],[6.4,-1.15],[5.65,1.4],[7.35,.42]],seconds:7.2},
 {id:'FIR_01',centre:2.9,height:3.05,targets:[[5.8,.03],[6.15,.7]],seconds:4.5},
 {id:'FIR_03',centre:1.1,height:2.35,targets:[[5.8,.03]],seconds:5.4},
];
async function run(){
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 const browser=await chromium.launch({headless:true,args:['--enable-webgl','--enable-unsafe-swiftshader','--use-angle=swiftshader','--mute-audio']});
 try{
  const page=await browser.newPage({viewport:{width:960,height:470},deviceScaleFactor:1}),errors=[],consoleErrors=[];
  page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')consoleErrors.push(m.text());});
  await page.goto('http://127.0.0.1:'+server.address().port+'/?view=2d&player=3d&test=max',{waitUntil:'load'});
  await page.waitForFunction(()=>globalThis.System,undefined,{timeout:45000});
  const finder=async()=>page.evaluate(async()=>{
   const cc=await System.import('cc');globalThis.findCurrentChapter=()=>{function find(n){return n?.getComponent('ChapterGame')||n?.children.map(find).find(Boolean);}return find(cc.director.getScene());};
  });await finder();
  for(let attempt=0;attempt<3;attempt++){
   try{await page.waitForFunction(()=>{const a=findCurrentChapter();return a?.session&&a?.actors&&!a.loading&&a.platform.auth.ready;},undefined,{timeout:30000});break;}
   catch(e){console.log('Startup retry',attempt+1,await page.evaluate(()=>({failure:findCurrentChapter()?.failure,loading:findCurrentChapter()?.loading})));if(attempt===2)throw e;await page.reload({waitUntil:'load'});await finder();}
  }
  let fixture=fs.readFileSync(path.join(__dirname,'../cocos-motion-study-v2/review-fixture.js'),'utf8').replace('+.13;','+.67;');
  await page.addScriptTag({content:fixture});await page.evaluate(()=>installMotionStudy('current'));
  console.log('Ready actual fire kit',gameHash.slice(0,12));
  for(const def of shots){
   const directory=path.join(root,'src/.tmp/fire-kit-implementation-v22',probe?'probe':'final',def.id);fs.mkdirSync(directory,{recursive:true});
   const info=await page.evaluate(def=>motionStudy.select({...def,family:'FIR'}),def);
   info.activeSlots=await page.evaluate(()=>[...motionStudy.state.combat.activeSlots]);
   if(info.loadout.ultimate!=='FIR_02')throw Error('Meteor did not enter the ultimate slot');
   const metrics=[];
   for(let frame=0;frame<Math.round(def.seconds*30);frame++){
    const save=!probe||[0,9,14,18,21,25,30,36,45,55,65,80,100,125,145,170,190,209].includes(frame);
    const result=await page.evaluate(save=>{
     const image=motionStudy.next(save),{app,state}=motionStudy;
     return{image,time:state.time,ground:app.effects.fireGround.inspect(),fire:app.effects.fireSprites.inspect(),shield:app.effects.shields.inspect(),slows:Object.entries(state.combat.statuses).map(([id,s])=>({id,until:s.slowUntil,percent:s.slowPercent})),casts:state.combat.casts.map(c=>({skill:c.skillId,hits:c.hits.length,zoneUntil:c.zoneUntil}))};
    },save);
    if(result.image)fs.writeFileSync(path.join(directory,String(frame).padStart(3,'0')+'.jpg'),Buffer.from(result.image,'base64'));
    delete result.image;metrics.push({frame,...result});
   }
   const report=await page.evaluate(()=>motionStudy.report());
   if(!report.events.some(e=>e.type==='skill_release')||!info.player?.skeletons?.length)throw Error('Missing native cast '+def.id);
   fs.writeFileSync(path.join(directory,'capture.json'),JSON.stringify({info,gameHash,errors,consoleErrors,...report,metrics},null,2));
   console.log('Captured',def.id,'frames',report.frames,'hits',report.events.filter(e=>e.type==='hit').length,'ground surfaces',Math.max(...metrics.map(m=>m.ground.active.length)));
  }
  const lifecycle=await page.evaluate(async()=>{
   const results=[];
   for(const id of ['FIR_04','FIR_05']){
    await motionStudy.select({id,family:'FIR',centre:3.1,height:3.75,targets:[[4.9,.05]],seconds:7});
    for(let i=0;i<60;i++)motionStudy.next(false);
    const {app,state}=motionStudy,before=app.effects.fireGround.inspect(),casts=JSON.stringify(state.combat.casts);
    app.effects.clear(true);app.effects.update(app.session);
    const after=app.effects.fireGround.inspect(),fire=app.effects.fireSprites.inspect();
    results.push({id,coreUnchanged:casts===JSON.stringify(state.combat.casts),groundBefore:before,groundAfter:after,fireAfter:fire.active.length});
    app.effects.clear();
    if(app.effects.fireGround.inspect().active.length)throw Error('Fire ground survived clear');
   }
   return results;
  });
  if(lifecycle.some(r=>!r.coreUnchanged||r.id==='FIR_04'&&r.groundAfter.active.filter(s=>s.kind==='jets'&&s.emitters===5).length!==1||r.id==='FIR_05'&&!r.fireAfter))throw Error('Pause/resume lost a fire field');
  fs.writeFileSync(path.join(__dirname,'runtime-lifecycle.json'),JSON.stringify(lifecycle,null,2));
  fs.writeFileSync(path.join(__dirname,'runtime-log.json'),JSON.stringify({gameHash,errors,consoleErrors},null,2));
  if(errors.length||consoleErrors.length)throw Error(JSON.stringify({errors,consoleErrors}));
 }finally{await browser.close();}
}
run().catch(e=>{console.error(e);process.exitCode=1;}).finally(()=>server.close());
