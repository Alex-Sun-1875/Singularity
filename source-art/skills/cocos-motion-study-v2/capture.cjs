const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const crypto = require('node:crypto');
const {execFileSync}=require('node:child_process');
const root = path.resolve(__dirname,'../../..');
const cocos = path.join(root,'src/cocos');
const { chromium } = require(path.join(cocos,'node_modules/playwright'));
const build = path.join(cocos,'build/concept-2d');
const tmp = path.join(root,'src/.tmp/cocos-motion-study-v2');
const args = process.argv.slice(2);
const option = (name, fallback) => args.includes(name) ? args[args.indexOf(name)+1] : fallback;
const variant = option('--variant','current');
const mode = option('--world','shipped');
const ids = option('--shots','BASIC_WAR,WAR_01,WAR_05,BOW_01,BOW_05,FIR_02,THU_02,THU_05').split(',');
const probe = args.includes('--probe');
const skipWrite=new Set(option('--skip-write','').split(',').filter(Boolean));
const single = distance=>[[distance,.02]];
const formation=[[4.9,.05],[6.4,-1.15],[5.65,1.4],[7.35,.42]];
const shots = {
  BASIC_WAR:{family:'WAR',centre:1.05,height:2.26,targets:[[2.53,0],[1.17,1.13]],seconds:1.95},
  WAR_01:{family:'WAR',centre:1.45,height:2.36,targets:single(2.74),seconds:1.55},
  WAR_02:{family:'WAR',centre:1.65,height:2.58,targets:single(3.40),seconds:1.62},
  WAR_04:{family:'WAR',centre:2.1,height:2.70,targets:[[3.45,0],[4.26,.75]],seconds:1.87},
  WAR_05:{family:'WAR',centre:1.98,height:2.75,targets:[[3.6,.10],[4.1,-.80],[4.3,.90]],seconds:2.16},
  BOW_01:{family:'BOW',centre:2.8,height:2.80,targets:single(5.8),seconds:1.63},
  BOW_05:{family:'BOW',centre:3.4,height:3.18,targets:formation,seconds:2.48},
  BOW_06:{family:'BOW',centre:2.55,height:2.95,targets:[[4.6,.08],[5.45,-.90]],seconds:1.76},
  FIR_01:{family:'FIR',centre:2.8,height:2.85,targets:single(5.8),seconds:1.70},
  FIR_02:{family:'FIR',centre:2.75,height:3.70,targets:[[4.7,.10],[5.85,-.85],[5.3,1.35]],seconds:2.57},
  THU_02:{family:'THU',centre:3.1,height:3.10,targets:formation,seconds:1.87},
  THU_05:{family:'THU',centre:3.1,height:3.10,targets:formation,seconds:2.55},
};
const mainName = fs.readdirSync(path.join(build,'assets/main')).find(n=>/^index\..+\.js$/.test(n));
const mainRel='/assets/main/'+mainName;
let mainBuffer=fs.readFileSync(path.join(build,mainRel));
const builtHash=crypto.createHash('sha256').update(mainBuffer).digest('hex');
if(variant==='design') mainBuffer=Buffer.from(require('./candidate-modules.cjs').replaceModules(mainBuffer.toString('utf8'),cocos));
const reviewTextures=new Map();
if(variant==='design'&&ids.some(id=>id.startsWith('FIR'))){
  const edgeTool=path.join(__dirname,'pyro-edges.py'),cache=path.join(tmp,'review-textures');
  fs.mkdirSync(cache,{recursive:true});
  for(const [name,rows] of [['fire-pyro-v7',4],['fire-low-rolls-v7',8]]){
    const {uuid}=JSON.parse(fs.readFileSync(path.join(cocos,'assets/resources/vfx/production',name+'.png.meta'),'utf8'));
    const urlDir='/assets/resources/native/'+uuid.slice(0,2)+'/';
    const folder=path.join(build,urlDir);
    const filename=fs.readdirSync(folder).find(file=>file.startsWith(uuid+'.')&&file.endsWith('.png'));
    if(!filename)throw Error('Missing current exported fire atlas '+uuid);
    const source=path.join(folder,filename);
    const revision=crypto.createHash('sha256').update(fs.readFileSync(source)).update(fs.readFileSync(edgeTool)).digest('hex').slice(0,16);
    const cooked=path.join(cache,name+'-'+revision+'.png');
    if(!fs.existsSync(cooked)){
      const local=cooked+'.'+process.pid;
      execFileSync(process.env.MOTION_REVIEW_PYTHON||'python',['-X','utf8',edgeTool,source,local,String(rows)]);
      fs.renameSync(local,cooked);
    }
    reviewTextures.set(urlDir+filename,cooked);
  }
}
const mime={'.js':'text/javascript','.json':'application/json','.wasm':'application/wasm','.html':'text/html','.css':'text/css','.png':'image/png','.jpg':'image/jpeg','.webp':'image/webp','.mp3':'audio/mpeg','.ogg':'audio/ogg','.bin':'application/octet-stream'};
const server=http.createServer((req,res)=>{
  const pathname=decodeURIComponent(new URL(req.url,'http://127.0.0.1').pathname);
  const file=path.resolve(build,'.'+(pathname==='/'?'/index.html':pathname));
  if(!file.startsWith(build+path.sep)||!fs.existsSync(file)||!fs.statSync(file).isFile()){res.writeHead(404);res.end();return;}
  res.setHeader('Content-Type',mime[path.extname(file)]||'application/octet-stream');
  if(pathname===mainRel)res.end(mainBuffer);
  else fs.createReadStream(reviewTextures.get(pathname)??file).on('error',()=>res.destroy()).pipe(res);
});
async function run(){
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  const browser=await chromium.launch({headless:true,executablePath:fs.existsSync(chromium.executablePath())?chromium.executablePath():'C:/Program Files/Google/Chrome/Application/chrome.exe',args:['--enable-webgl','--enable-unsafe-swiftshader','--use-angle=swiftshader','--mute-audio']});
  try{
    const page=await browser.newPage({viewport:{width:960,height:470},deviceScaleFactor:1});
    const errors=[];page.on('pageerror',e=>{errors.push(String(e));console.error('Game:',e.message);});
    await page.goto('http://127.0.0.1:'+server.address().port+'/?view='+(mode==='native'?'3d':'2d')+'&player=3d&test=max',{waitUntil:'load'});
    await page.waitForFunction(()=>globalThis.System,undefined,{timeout:45000});
    await page.evaluate(async()=>{const cc=await System.import('cc');globalThis.studyChapter=()=>{function find(n){return n?.getComponent('ChapterGame')||n?.children.map(find).find(Boolean);}return find(cc.director.getScene());};});
    await page.waitForFunction(()=>{const a=studyChapter();return a?.session&&a?.actors&&!a.loading&&a.platform.auth.ready;},undefined,{timeout:120000});
    console.log(variant,mode,'current Cocos stage ready');
    if(variant==='design')await page.addScriptTag({path:path.join(__dirname,'dimensions.js')});
    await page.addScriptTag({path:path.join(__dirname,'review-fixture.js')});
    await page.evaluate(async variant=>{await installMotionStudy(variant);},variant);
    for(const id of ids){
      const def={...shots[id],id};if(!def.family)throw Error('Unknown shot: '+id);
      const dir=path.join(tmp,(probe?'probe-':'')+mode,variant,id);fs.mkdirSync(dir,{recursive:true});
      const info=await page.evaluate(s=>motionStudy.select(s),def);
      console.log('Loaded',id,info.renderer,info.geometry,info.origin);
      if(!info.player?.skeletons?.length)throw Error('Captured player has no skeleton');
      const frames=Math.round(def.seconds*30);
      for(let i=0;i<frames;i++){
        const save=!skipWrite.has(id)&&(!probe||[0,12,17,21,24,27,31,36,40].includes(i));
        const bytes=await page.evaluate(save=>motionStudy.next(save),save);
        if(bytes)fs.writeFileSync(path.join(dir,String(i).padStart(3,'0')+'.jpg'),Buffer.from(bytes,'base64'));
      }
      const report=await page.evaluate(()=>motionStudy.report());
      if(!skipWrite.has(id))fs.writeFileSync(path.join(dir,'capture.json'),JSON.stringify({variant,mode,sequence:ids.slice(0,ids.indexOf(id)+1),gameMain:mainRel,buildSHA256:builtHash,fps:30,rendererFPS:60,info,errors,...report},null,2));
      console.log('Captured',id,frames,report.stats,'hit IDs',report.events.filter(e=>e.type==='hit').map(e=>e.id),'casts',report.castResult,report.clips);
      if(errors.length)throw Error(errors[0]);
      if(id!=='BASIC_WAR'&&!report.events.some(e=>e.type==='skill_release'))throw Error('Missing actual skill release: '+id+' '+JSON.stringify(report.events));
    }
  }finally{await browser.close();}
}
run().catch(e=>{console.error(e);process.exitCode=1;}).finally(()=>server.close());
