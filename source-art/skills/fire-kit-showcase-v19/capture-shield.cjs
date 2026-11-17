// Read-only recording of the existing native Cocos shield. No source/build mutation.
const fs=require('node:fs'),path=require('node:path'),http=require('node:http'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'../../..'),cocos=path.join(root,'src/cocos');
const {chromium}=require(path.join(cocos,'node_modules/playwright'));
const build=path.join(cocos,'build/concept-2d-audio');
const mainDir=path.join(build,'assets/main'),mainName=fs.readdirSync(mainDir).find(x=>/^index\..+\.js$/.test(x));
const original=fs.readFileSync(path.join(mainDir,mainName));
const hash=buffer=>crypto.createHash('sha256').update(buffer).digest('hex');
const mime={'.js':'text/javascript','.json':'application/json','.html':'text/html','.png':'image/png','.jpg':'image/jpeg','.css':'text/css','.bin':'application/octet-stream','.wasm':'application/wasm'};
const server=http.createServer((request,response)=>{
 const url=decodeURIComponent(new URL(request.url,'http://127.0.0.1').pathname);
 const file=path.resolve(build,'.'+(url==='/'?'/index.html':url));
 if(!file.startsWith(build+path.sep)||!fs.existsSync(file)||!fs.statSync(file).isFile()){response.writeHead(404).end();return;}
 response.setHeader('Content-Type',mime[path.extname(file)]||'application/octet-stream');
 fs.createReadStream(file).pipe(response);
});
async function run(){
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 const browser=await chromium.launch({headless:true,args:['--enable-webgl','--enable-unsafe-swiftshader','--use-angle=swiftshader','--mute-audio']});
 try{
  const page=await browser.newPage({viewport:{width:960,height:470},deviceScaleFactor:1}),errors=[];
  page.on('pageerror',e=>{errors.push(e.message);console.error(e.message);});
  await page.goto('http://127.0.0.1:'+server.address().port+'/?view=3d&player=3d&test=max',{waitUntil:'load'});
  await page.waitForFunction(()=>globalThis.System,undefined,{timeout:45000});
  const finder=async()=>page.evaluate(async()=>{
   const cc=await System.import('cc');
   globalThis.findCurrentChapter=()=>{function find(n){return n?.getComponent('ChapterGame')||n?.children.map(find).find(Boolean);}return find(cc.director.getScene());};
  });
  await finder();
  for(let attempt=0;attempt<3;attempt++){
   try{await page.waitForFunction(()=>{const a=findCurrentChapter();return a?.session&&a?.actors&&!a.loading&&a.platform.auth.ready;},undefined,{timeout:30000});break;}
   catch(error){
    console.log('Startup retry',attempt+1);if(attempt===2)throw error;
    await page.reload({waitUntil:'load'});await finder();
   }
  }
  let fixture=fs.readFileSync(path.join(__dirname,'../cocos-motion-study-v2/review-fixture.js'),'utf8');
  if(fixture.split('+.13;').length!==2)throw Error('Fixture camera facing changed');
  fixture=fixture.replace('+.13;','+.67;');
  await page.addScriptTag({content:fixture});await page.evaluate(()=>installMotionStudy('current'));
  console.log('Ready existing shield',hash(original).slice(0,12));
  const shot={id:'FIR_03',family:'FIR',centre:1.15,height:2.35,targets:[[5.8,.03]],seconds:5.4};
  const directory=path.join(root,'src/.tmp/fire-kit-showcase-v19/current/FIR_03');fs.mkdirSync(directory,{recursive:true});
  const info=await page.evaluate(def=>motionStudy.select(def),shot);
  const samples=[];
  for(let frame=0;frame<Math.round(shot.seconds*30);frame++){
   const result=await page.evaluate(()=>({image:motionStudy.next(true),shield:motionStudy.state.player.shield,time:motionStudy.state.time}));
   fs.writeFileSync(path.join(directory,String(frame).padStart(3,'0')+'.jpg'),Buffer.from(result.image,'base64'));
   samples.push({frame,shield:result.shield,time:result.time});
  }
  const report=await page.evaluate(()=>motionStudy.report());
  if(errors.length)throw Error(errors.join('\n'));
  if(!info.player?.skeletons?.length||!report.events.some(e=>e.type==='skill_release'))throw Error('Missing native shield cast');
  if(!samples.some(s=>s.shield>0))throw Error('Shield never became active');
  fs.writeFileSync(path.join(directory,'capture.json'),JSON.stringify({variant:'current',build:path.relative(root,build),gameHash:hash(original),fixtureHash:hash(Buffer.from(fixture)),info,errors,...report,samples},null,2));
  console.log('Captured existing shield',report.frames,'maxShield',Math.max(...samples.map(s=>s.shield??0)),'errors',errors.length);
 }finally{await browser.close();}
}
run().catch(error=>{console.error(error);process.exitCode=1;}).finally(()=>server.close());
