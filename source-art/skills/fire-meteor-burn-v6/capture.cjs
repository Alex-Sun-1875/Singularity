// Real Cocos scene, animation and combat simulation. Isolated HTTP review overrides.
const fs=require('node:fs'),path=require('node:path'),http=require('node:http'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'../../..'),cocos=path.join(root,'src/cocos');
const {chromium}=require(path.join(cocos,'node_modules/playwright'));
const args=process.argv.slice(2),option=(key,fallback)=>args.includes(key)?args[args.indexOf(key)+1]:fallback;
const build=path.join(cocos,'build',option('--build','concept-2d-audio'));
const variant='design',selected=option('--shots','FIR_02').split(','),probe=args.includes('--probe');
const shots={
 FIR_01:{family:'FIR',centre:2.9,height:3.05,targets:[[5.8,.03],[6.15,.7]],seconds:4.2},
 FIR_02:{family:'FIR',centre:2.7,height:3.85,targets:[[4.7,.10],[5.85,-.85],[5.3,1.35]],seconds:6.5},
 FIR_04:{family:'FIR',centre:3.0,height:3.6,targets:[[4.7,.10],[5.85,-.85],[5.3,1.35]],seconds:7.4},
 FIR_05:{family:'FIR',centre:3.2,height:3.6,targets:[[4.9,.05],[6.4,-1.15],[5.65,1.4],[7.35,.42]],seconds:6.7},
};
const mainDir=path.join(build,'assets/main'),mainName=fs.readdirSync(mainDir).find(x=>/^index\..+\.js$/.test(x));
const mainURL='/assets/main/'+mainName,original=fs.readFileSync(path.join(mainDir,mainName));
const hash=buffer=>crypto.createHash('sha256').update(buffer).digest('hex');
const main=variant==='design'?Buffer.from(require('./refine-modules.cjs').replaceModules(original.toString('utf8'),cocos)):original;
const reviewInputs={};
for(const filename of ['refine-modules.cjs','ultimate-role.js','assets/fire-pyro-v7.png','assets/fire-low-rolls-v7.png','assets/fire-bolt-v9.png'])reviewInputs[filename]=hash(fs.readFileSync(path.join(__dirname,filename)));
for(const name of ['NativeSkillVfx','SkillFireSprites','Effects'])reviewInputs['source/'+name+'.ts']=hash(fs.readFileSync(path.join(cocos,'assets/scripts/features/combat/runtime',name+'.ts')));
const replacements=new Map();
if(variant==='design')for(const name of ['fire-pyro-v7','fire-low-rolls-v7','fire-bolt-v9']){
 const meta=JSON.parse(fs.readFileSync(path.join(cocos,'assets/resources/vfx/production',name+'.png.meta'),'utf8'));
 let found=false;
 for(const bundle of fs.readdirSync(path.join(build,'assets'))){
  const prefix='/assets/'+bundle+'/native/'+meta.uuid.slice(0,2)+'/',folder=path.join(build,prefix);
  if(!fs.existsSync(folder))continue;
  const file=fs.readdirSync(folder).find(x=>x.startsWith(meta.uuid+'.')&&x.endsWith('.png'));
  if(file){replacements.set(prefix+file,path.join(__dirname,'assets',name+'.png'));found=true;}
 }
 if(!found)throw Error('Missing built atlas '+name);
}
const mime={'.js':'text/javascript','.json':'application/json','.html':'text/html','.png':'image/png','.jpg':'image/jpeg','.css':'text/css','.bin':'application/octet-stream','.wasm':'application/wasm'};
const server=http.createServer((request,response)=>{
 const url=decodeURIComponent(new URL(request.url,'http://127.0.0.1').pathname);
 const file=path.resolve(build,'.'+(url==='/'?'/index.html':url));
 if(!file.startsWith(build+path.sep)||!fs.existsSync(file)||!fs.statSync(file).isFile()){response.writeHead(404).end();return;}
 response.setHeader('Content-Type',mime[path.extname(file)]||'application/octet-stream');
 if(url===mainURL)response.end(main);else fs.createReadStream(replacements.get(url)||file).pipe(response);
});
async function run(){
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 const browser=await chromium.launch({headless:true,args:['--enable-webgl','--enable-unsafe-swiftshader','--use-angle=swiftshader','--mute-audio']});
 try{
  const page=await browser.newPage({viewport:{width:960,height:470},deviceScaleFactor:1}),errors=[];
  page.on('pageerror',error=>{errors.push(error.message);console.error(error.message);});
  await page.goto('http://127.0.0.1:'+server.address().port+'/?view=3d&player=3d&test=max',{waitUntil:'load'});
  await page.waitForFunction(()=>globalThis.System,undefined,{timeout:45000});
  await page.evaluate(async()=>{
   const cc=await System.import('cc');
   globalThis.findCurrentChapter=()=>{function find(node){return node?.getComponent('ChapterGame')||node?.children.map(find).find(Boolean);}return find(cc.director.getScene());};
  });
  for(let attempt=0;attempt<3;attempt++){
   try{await page.waitForFunction(()=>{const app=findCurrentChapter();return app?.session&&app?.actors&&!app.loading&&app.platform.auth.ready;},undefined,{timeout:30000});break;}
   catch(error){
    const state=await page.evaluate(()=>{const a=findCurrentChapter();return{chapter:!!a,loading:a?.loading,session:!!a?.session,actors:!!a?.actors,auth:a?.platform?.auth?.ready,failure:a?.failure,text:document.body.innerText.slice(0,400)};});
    console.log('Loading state',attempt,state);if(attempt===2)throw error;
    // A new page avoids a stale native material/asset startup in the disposable preview.
    await page.reload({waitUntil:'load'});
    await page.evaluate(async()=>{const cc=await System.import('cc');globalThis.findCurrentChapter=()=>{function find(n){return n?.getComponent('ChapterGame')||n?.children.map(find).find(Boolean);}return find(cc.director.getScene());};});
   }
  }
  if(variant==='design')await page.addScriptTag({content:fs.readFileSync(path.join(__dirname,'ultimate-role.js'),'utf8')});
  let fixture=fs.readFileSync(path.join(__dirname,'../cocos-motion-study-v2/review-fixture.js'),'utf8');
  if(fixture.split('+.13;').length!==2)throw Error('Fixture camera facing changed');
  fixture=fixture.replace('+.13;','+.67;');
  if(variant==='design')fixture=fixture.replace("  app.enabled = false;",'  applyFireUltimateRole(COMBAT_SKILLS,COMBAT_LOADOUTS);\n  app.enabled = false;');
  await page.addScriptTag({content:fixture});await page.evaluate(()=>installMotionStudy('current'));
  console.log('Ready',variant,hash(original).slice(0,12));
  for(const take of ['previous','design'])for(const id of selected){
   const def=shots[id];if(!def)throw Error('Unknown shot '+id);
   const directory=path.join(root,'src/.tmp/fire-meteor-burn-v6',probe?'probe':'final',take,id);fs.mkdirSync(directory,{recursive:true});
   await page.evaluate(take=>{globalThis.fireLongBurnReview=take==='design';},take);
   const info=await page.evaluate(def=>motionStudy.select(def),{...def,id});
   const presentation=await page.evaluate(({variant,id})=>{
    const {app,cc}=motionStudy,camera=app.camera,canvas=cc.game.canvas;
    if(variant==='design')app.effects.fireSprites.camera=camera;
    const target=motionStudy.state.enemies[0],right=camera.node.right.clone(),far=camera.node.up.clone();
    right.y=0;right.normalize();far.y=0;far.normalize();const half=2.8/(460/512);
    const corners=[[-1,1],[1,1],[1,-1],[-1,-1]].map(([u,v])=>{
     const p={x:target.x+right.x*u*half+far.x*v*half,z:target.z+right.z*u*half+far.z*v*half};
     const s=camera.worldToScreen(new cc.Vec3(p.x,app.world.height(p)+.052,p.z));return[s.x,canvas.height-s.y];
    });
    return{camera:{position:camera.node.worldPosition,forward:camera.node.forward,orthoHeight:camera.orthoHeight},ringCorners:corners,fireUltimateReview:globalThis.fireUltimateReview};
   },{variant,id});
   console.log('Recording',take,id,info.loadout);
   const metrics=[];
   for(let frame=0;frame<Math.round(def.seconds*30);frame++){
    const save=!probe||[0,9,18,27,33,39,45,60,75,90,105,120,150,180,210].includes(frame);
    const result=await page.evaluate(save=>{
     const image=motionStudy.next(save),fire=motionStudy.app.effects.fireSprites.inspect();
     return{image,active:fire.active.map(x=>({key:x.key,phase:x.phase,width:x.width,height:x.height})),zones:motionStudy.state.fireZones.length,time:motionStudy.state.time};
    },save);
    if(result.image)fs.writeFileSync(path.join(directory,String(frame).padStart(3,'0')+'.jpg'),Buffer.from(result.image,'base64'));
    metrics.push({frame,time:result.time,zones:result.zones,active:result.active});
   }
   const report=await page.evaluate(()=>motionStudy.report());
   if(errors.length)throw Error(errors.join('\n'));
   if(!info.player?.skeletons?.length||!report.events.some(e=>e.type==='skill_release'))throw Error('Missing native cast '+id);
   if(variant==='design'&&info.loadout.ultimate!=='FIR_02')throw Error('Meteor is not the ultimate');
   fs.writeFileSync(path.join(directory,'capture.json'),JSON.stringify({variant:take,build:path.relative(root,build),info,presentation,gameHash:hash(original),reviewInputs,errors,...report,metrics},null,2));
   console.log('Captured',take,id,report.frames,'lastHit',report.events.filter(e=>e.type==='hit').at(-1)?.time);
  }
 }finally{await browser.close();}
}
run().catch(error=>{console.error(error);process.exitCode=1;}).finally(()=>server.close());
