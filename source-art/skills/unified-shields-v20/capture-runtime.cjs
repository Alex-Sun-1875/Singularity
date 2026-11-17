// Inspect the actual compiled Cocos implementation. No response/module/art overrides.
const fs=require('node:fs'),path=require('node:path'),http=require('node:http'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'../../..'),cocos=path.join(root,'src/cocos');
const {chromium}=require(path.join(cocos,'node_modules/playwright'));
const build=path.join(cocos,'build/concept-2d'),probe=process.argv.includes('--probe');
const hash=data=>crypto.createHash('sha256').update(data).digest('hex');
const mainDir=path.join(build,'assets/main'),mainName=fs.readdirSync(mainDir).find(x=>/^index\..+\.js$/.test(x));
const gameHash=hash(fs.readFileSync(path.join(mainDir,mainName)));
const mime={'.js':'text/javascript','.json':'application/json','.html':'text/html','.png':'image/png','.jpg':'image/jpeg','.css':'text/css','.bin':'application/octet-stream','.wasm':'application/wasm'};
const server=http.createServer((request,response)=>{
 const url=decodeURIComponent(new URL(request.url,'http://127.0.0.1').pathname),file=path.resolve(build,'.'+(url==='/'?'/index.html':url));
 if(!file.startsWith(build+path.sep)||!fs.existsSync(file)||!fs.statSync(file).isFile()){response.writeHead(404).end();return;}
 response.setHeader('Content-Type',mime[path.extname(file)]||'application/octet-stream');fs.createReadStream(file).pipe(response);
});
const scenarios=probe?[{family:'FIR',id:'FIR_03',label:'fire-active'}]:[
 {family:'FIR',id:'FIR_03',label:'fire-active'},
 {family:'WAR',id:'WAR_03',label:'war-active'},
 {family:'BOW',id:'STATE_ONLY',label:'bow-state-fixture'},
 {family:'THU',id:'STATE_ONLY',label:'thunder-state-fixture'},
 {family:'FIR',id:'FIR_03',label:'fire-break',break:true},
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
   catch(e){const diagnostic=await page.evaluate(()=>{const a=findCurrentChapter();return{failure:a?.failure,loading:a?.loading,text:document.body.innerText.slice(0,300)};});console.log('Startup',attempt,diagnostic);if(attempt===2)throw e;await page.reload({waitUntil:'load'});await finder();}
  }
  let fixture=fs.readFileSync(path.join(__dirname,'../cocos-motion-study-v2/review-fixture.js'),'utf8');fixture=fixture.replace('+.13;','+.67;');
  await page.addScriptTag({content:fixture});await page.evaluate(()=>installMotionStudy('current'));
  console.log('Ready native unified shield',gameHash.slice(0,12));
  for(const scenario of scenarios){
   const directory=path.join(root,'src/.tmp/unified-shields-v20',probe?'probe':'final',scenario.label);fs.mkdirSync(directory,{recursive:true});
   const def={...scenario,centre:1.1,height:2.35,targets:[[5.8,.03]],seconds:5.5,start:scenario.id==='STATE_ONLY'?999:.30};
   const info=await page.evaluate(def=>motionStudy.select(def),def),metrics=[];
   for(let frame=0;frame<165;frame++){
    const save=!probe||[0,14,22,30,36,55,57,60,64,85,115,126,132,140,153,164].includes(frame);
    const result=await page.evaluate(({scenario,frame,save})=>{
     const {app,state}=motionStudy,session=app.session;
     // The fixture grants the existing authoritative rule's shield to compare
     // BOW/THU skins; it does not pretend these are new active skills/triggers.
     if(scenario.id==='STATE_ONLY'&&frame===14)session.combatRules.shield(state.player.maxHp*.15,4);
     if(frame===55){state.player.hurtTime=0;session.hurt(scenario.break?state.player.shield*2+8:8,'study-target-0',false,'physical',true,'shield-review-impact');app.process(session.drain());}
     const image=motionStudy.next(save),shield=app.effects.shields.inspect();
     return{image,shield,hp:state.player.hp,amount:state.player.shield,time:state.time};
    },{scenario,frame,save});
    if(result.image)fs.writeFileSync(path.join(directory,String(frame).padStart(3,'0')+'.jpg'),Buffer.from(result.image,'base64'));
    delete result.image;metrics.push({frame,...result});
   }
   const report=await page.evaluate(()=>motionStudy.report());
   const active=metrics.filter(m=>m.shield.visible);
   if(!active.length||metrics.at(-1).shield.visible)throw Error('Shield missing or did not clear: '+scenario.label);
   if(!active.every(m=>m.shield.family===scenario.family))throw Error('Wrong skin: '+scenario.label);
   if(!info.player?.skeletons?.length)throw Error('Not a native skinned character');
   fs.writeFileSync(path.join(directory,'capture.json'),JSON.stringify({scenario,info,gameHash,errors,consoleErrors,...report,metrics},null,2));
   console.log('Captured',scenario.label,'visible',active.length,'last amount',metrics.at(-1).amount);
  }
  if(!probe){
   const lifecycle=await page.evaluate(async()=>{
    const {app,state}=motionStudy,cc=motionStudy.cc;
    await motionStudy.select({id:'FIR_03',family:'FIR',centre:1.1,height:2.35,targets:[[5.8,.03]],start:999});
    const p=state.player,start={x:p.x,z:p.z};app.session.combatRules.shield(20,4);motionStudy.next(false);
    const first=app.effects.shields.inspect();state.time+=.8;app.effects.update(app.session);app.effects.clear(true);app.effects.update(app.session);
    const resumed=app.effects.shields.inspect();p.x+=.6;p.z+=.3;app.effects.update(app.session);const moved=app.effects.shields.inspect();
    app.actors.update(app.session,0,false,false);app.effects.update(app.session);cc.director.tick(1/60);
    const movedFrame=cc.game.canvas.toDataURL('image/jpeg',.96).split(',')[1];
    const orientation=app.effects.shields.root.worldRotation;
    app.effects.clear();const cleared=app.effects.shields.inspect();
    return{first,resumed,moved,cleared,movedFrame,pausedStartUnchanged:first.start===resumed.start,followedMovement:Math.abs(moved.position.x-start.x-.6)<.001&&Math.abs(moved.position.z-start.z-.3)<.001,orientation};
   });
   if(!lifecycle.pausedStartUnchanged||!lifecycle.followedMovement||lifecycle.cleared.visible)throw Error('Lifecycle regression');
   fs.writeFileSync(path.join(__dirname,'media/runtime-movement.jpg'),Buffer.from(lifecycle.movedFrame,'base64'));delete lifecycle.movedFrame;
   fs.writeFileSync(path.join(__dirname,'runtime-lifecycle.json'),JSON.stringify(lifecycle,null,2));
  }
  const fatal=consoleErrors.filter(m=>/shader|compile|GL_INVALID|uniform|Effect.*(error|fail)|Error \d+/i.test(m));
  fs.writeFileSync(path.join(__dirname,probe?'runtime-probe-log.json':'runtime-log.json'),JSON.stringify({gameHash,errors,consoleErrors,fatal},null,2));
  if(errors.length||fatal.length)throw Error(JSON.stringify({errors,fatal}));
 }finally{await browser.close();}
}
run().catch(e=>{console.error(e);process.exitCode=1;}).finally(()=>server.close());
