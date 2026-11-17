// Capture the current Cocos scene with the same actors, simulation and camera in both variants.
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const crypto = require('node:crypto');

const root = path.resolve(__dirname, '../../..');
const cocos = path.join(root, 'src/cocos');
const cache = path.join(root, 'src/.tmp/warrior-silvercyan-v10');
const liveBuild=path.join(cocos,'build/concept-2d');
const frozenBuild=path.join(root,'src/.tmp/warrior-cross-v5/frozen-build');
const build=fs.existsSync(path.join(frozenBuild,'index.html'))?frozenBuild:liveBuild;
const {chromium} = require(path.join(cocos, 'node_modules/playwright'));
const options = process.argv.slice(2);
function option(name, fallback) {
  const index = options.indexOf(name);
  return index < 0 ? fallback : options[index + 1];
}
const variant = option('--variant', 'previous');
const probe = options.includes('--probe');
const nativeGpu=true;
const skipWrite = new Set(option('--skip-write','').split(',').filter(Boolean));
const selected = option('--shots', 'BASIC_WAR,WAR_01,WAR_02,WAR_03,WAR_04,WAR_05,WAR_P1,WAR_P2').split(',');
const shots = {
  BASIC_WAR: {family:'WAR', centre:1.05, height:2.65, targets:[[1.65,.04],[2.50,.20]], seconds:1.95},
  WAR_01: {family:'WAR', centre:1.5, height:2.6, targets:[[2.74,.02]], seconds:2.4},
  WAR_02: {family:'WAR', centre:1.8, height:3.0, targets:[[3.40,.38]], seconds:1.80},
  WAR_03: {family:'WAR', centre:.75, height:2.4, targets:[[1.20,.0]], seconds:3.6, retaliate:true},
  WAR_P1: {family:'WAR', centre:1.4, height:2.6, targets:[[2.74,.02]], seconds:2.25, castSkill:'WAR_01', passive:'WAR_P1'},
  WAR_P2: {family:'WAR', centre:.75, height:2.4, targets:[[1.20,.0]], seconds:3.6, castSkill:'WAR_03', passive:'WAR_P2',retaliate:true},
  WAR_04: {family:'WAR', centre:2.3, height:3.6, targets:[[3.45,0],[4.26,.75]], seconds:1.87},
  WAR_05: {family:'WAR', centre:2.2, height:3.8, targets:[[3.6,.10],[4.1,-.80],[4.3,.90]], seconds:2.25},
};
const mainDirectory = path.join(build, 'assets/main');
const mainName = fs.readdirSync(mainDirectory).find(name => /^index\..+\.js$/.test(name));
const mainURL = '/assets/main/' + mainName;
const original = fs.readFileSync(path.join(mainDirectory, mainName));
const gameHash = crypto.createHash('sha256').update(original).digest('hex');
const liveMain=path.join(liveBuild,'assets/main',mainName);
const sameLive=fs.existsSync(liveMain)&&crypto.createHash('sha256').update(fs.readFileSync(liveMain)).digest('hex')===gameHash;
const frozenMain=path.join(frozenBuild,'assets/main',mainName);
fs.mkdirSync(path.dirname(frozenMain),{recursive:true});
if(!fs.existsSync(frozenMain))fs.writeFileSync(frozenMain,original);
const sources=path.join(root,'src/.tmp/warrior-cross-v5/sources');
for(const relative of ['actors/runtime/MeleeBladeSurfaces','combat/runtime/MeleeSkillEffects','combat/runtime/Effects','combat/runtime/NativeSkillVfx']){
  const target=path.join(sources,relative+'.ts');
  fs.mkdirSync(path.dirname(target),{recursive:true});
  if(!fs.existsSync(target))fs.copyFileSync(path.join(cocos,'assets/scripts/features',relative+'.ts'),target);
}
const reviewInputs = {};
for (const name of ['refine-modules.cjs','WarriorKitStudy.ts','blade.png','guard.png']) {
  const file=path.join(__dirname,name);
  if(fs.existsSync(file))reviewInputs[name]=crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
}
const main=Buffer.from(require('./refine-modules.cjs').replaceModules(original.toString('utf8'),cocos,variant,sources));
const mime = {'.js':'text/javascript', '.json':'application/json', '.html':'text/html', '.png':'image/png', '.jpg':'image/jpeg', '.css':'text/css', '.bin':'application/octet-stream', '.wasm':'application/wasm'};
const server = http.createServer((request,response) => {
  const url = decodeURIComponent(new URL(request.url,'http://127.0.0.1').pathname);
  if(url==='/review/blade.png'||url==='/review/guard.png'){response.setHeader('Content-Type','image/png');response.end(fs.readFileSync(path.join(__dirname,url.endsWith('/blade.png')?'blade.png':'guard.png')));return;}
  let filename = path.resolve(build, '.'+(url==='/'?'/index.html':url));
  if(filename.startsWith(build+path.sep)&&!fs.existsSync(filename)&&sameLive)filename=path.join(liveBuild,path.relative(build,filename));
  if(filename.startsWith(build+path.sep)&&!fs.existsSync(filename)&&/^\/assets\/[^/]+\/(?:native|import)\/.+\.[0-9a-f]{5}\.[a-z0-9]+$/i.test(url)){
    for(const directory of [liveBuild,path.join(cocos,'build/concept-2d-dev'),path.join(cocos,'build/concept-2d-melee-reach-v14')]){
      const hashed=path.resolve(directory,'.'+url);
      if(hashed.startsWith(directory+path.sep)&&fs.existsSync(hashed)){
        fs.mkdirSync(path.dirname(filename),{recursive:true});fs.copyFileSync(hashed,filename);break;
      }
    }
  }
  if ((!filename.startsWith(build+path.sep)&&!filename.startsWith(liveBuild+path.sep)) || !fs.existsSync(filename) || !fs.statSync(filename).isFile()) {
    console.error('Missing asset',url);
    response.writeHead(404).end();
    return;
  }
  response.setHeader('Content-Type', mime[path.extname(filename)] || 'application/octet-stream');
  if (url === mainURL) response.end(main);
  else {
    const bytes=fs.readFileSync(filename);
    if(filename.startsWith(liveBuild+path.sep)){
      const frozen=path.join(frozenBuild,path.relative(liveBuild,filename));
      fs.mkdirSync(path.dirname(frozen),{recursive:true});
      if(!fs.existsSync(frozen))fs.writeFileSync(frozen,bytes);
    }
    response.end(bytes);
  }
});

async function run() {
  await new Promise(resolve => server.listen(0,'127.0.0.1',resolve));
  const browser = await chromium.launch({headless:true,args:['--enable-webgl',...(nativeGpu?['--use-angle=d3d11','--ignore-gpu-blocklist']:['--enable-unsafe-swiftshader','--use-angle=swiftshader']),'--mute-audio','--disable-background-timer-throttling','--disable-renderer-backgrounding','--disable-backgrounding-occluded-windows']});
  try {
    const page = await browser.newPage({viewport:{width:480,height:235},deviceScaleFactor:1});
    await page.bringToFront();
    const errors = [];
    page.on('pageerror', error => { errors.push(error.message); console.error(error.message); });
    page.on('console',message=>{if(message.type()==='error')console.error('Browser',message.text().slice(0,600));});
    await page.goto('http://127.0.0.1:'+server.address().port+'/?view=3d&player=3d&test=max',{waitUntil:'load'});
    await page.waitForFunction(() => globalThis.System,undefined,{timeout:45000});
    await page.evaluate(async () => {
      const cc = await System.import('cc');
      globalThis.findCurrentChapter = () => {
        function find(node) { return node?.getComponent('ChapterGame') || node?.children.map(find).find(Boolean); }
        return find(cc.director.getScene());
      };
    });
    try{
      const deadline=Date.now()+180000;
      for(let n=0;;n++){
        const state=await page.evaluate(async()=>{
          const app=findCurrentChapter(),cc=await System.import('cc');
          const ready=!!(app?.session&&app?.actors&&!app.loading&&app.platform.auth.ready);
          if(!ready&&app?.session&&app?.actors&&app.loading){cc.game.resume();cc.director.tick(1/60);}
          return {ready,loading:app?.loading,session:!!app?.session,actors:!!app?.actors,paused:cc.game.isPaused?.()};
        });
        if(state.ready)break;
        if(n%20===0)console.log('Boot',state);
        if(Date.now()>deadline)throw Error('Current scene boot timeout');
        await new Promise(resolve=>setTimeout(resolve,500));
      }
    }catch(error){
      console.error('Startup state',await page.evaluate(()=>{const a=findCurrentChapter();return {app:!!a,session:!!a?.session,actors:!!a?.actors,loading:a?.loading,failure:a?.failure,authReady:a?.platform?.auth?.ready,text:document.body.innerText.slice(0,350)};}));
      await page.screenshot({path:path.join(cache,'startup.png')});throw error;
    }
    await page.setViewportSize({width:960,height:470});
    await page.evaluate(async()=>{const cc=await System.import('cc');cc.view.resizeWithBrowserSize(true);cc.view.setFrameSize(960,470);cc.game.resume();cc.director.tick(1/60);});
    await page.waitForFunction(()=>document.getElementById('GameCanvas')?.width===960,undefined,{timeout:30000});
    const fixturePath = path.join(__dirname,'review-fixture.js');
    const fixture = fs.readFileSync(fixturePath,'utf8');
    if (fixture.split('+.13;').length !== 2) throw Error('Recording fixture facing changed');
    await page.addScriptTag({content:fixture.replace('+.13;','+.67;')});
    await page.evaluate(() => installMotionStudy('current'));
    await page.evaluate(async()=>{globalThis.qiOpacity=(await System.import('chunks:///_virtual/MeleeBladeSurfaces.ts')).MeleeBladeSurfaces;qiOpacity.setOpacityScale(.55);});
    console.log('Ready silver-cyan kit',variant,gameHash.slice(0,12));
    for (const id of selected) {
      if (!shots[id]) throw Error('Unknown shot '+id);
      const directory = path.join(cache,probe?'probe':'final',variant,id);
      fs.mkdirSync(directory,{recursive:true});
      const info = await page.evaluate(shot => motionStudy.select(shot),{...shots[id],id});
      const presentation = await page.evaluate(variant => {
        const app=motionStudy.app;
        app.effects.blades.camera=app.camera;
        return {camera:{position:app.camera.node.worldPosition,forward:app.camera.node.forward,orthoHeight:app.camera.orthoHeight},actorCount:app.actors.inspect().length};
      },variant);
      const frames = Math.round(shots[id].seconds*30);
      const overlapFrames=[];
      console.log('Recording',variant,id,info.renderer,info.origin);
      for (let index=0;index<frames;index++) {
        const save = !skipWrite.has(id) && (!probe || [0,9,12,14,16,18,20,22,25,28,32,36,40,45,50,58,66,78].includes(index));
        const sample=await page.evaluate(({save,compare})=>{
          const jpg=motionStudy.next(save);
          const keys=motionStudy.app.effects.blades.inspect().active.map(cut=>cut.key);
          const horizontal=keys.some(key=>key.includes(':horizontal')||key.includes(':crossbar:'));
          const vertical=keys.some(key=>key.includes(':vertical')||key.startsWith('cleave:')&&!key.includes(':crossbar:'));
          let before;
          return {jpg,before,overlap:horizontal&&vertical};
        },{save,compare:false});
        if(sample.overlap)overlapFrames.push(index);
        if(sample.before){const folder=path.join(cache,'opacity-before',id);fs.mkdirSync(folder,{recursive:true});fs.writeFileSync(path.join(folder,String(index).padStart(3,'0')+'.jpg'),Buffer.from(sample.before,'base64'));}
        if (sample.jpg) fs.writeFileSync(path.join(directory,String(index).padStart(3,'0')+'.jpg'),Buffer.from(sample.jpg,'base64'));
      }
      const report = await page.evaluate(() => ({...motionStudy.report(),style:motionStudy.app.effects.blades.inspect(),fire:motionStudy.app.effects.fireSprites.inspect()}));
      if (errors.length) throw Error(errors.join('\n'));
      if (!info.player?.skeletons?.length) throw Error('Missing native player skeleton');
      if (id!=='BASIC_WAR' && !report.events.some(event=>event.type==='skill_release')) throw Error('Missing real release '+id);
      if(id==='WAR_P1'||id==='WAR_P2'){if(!report.events.some(event=>event.type==='skill_status'&&event.skill===id))throw Error('Missing real passive trigger '+id);}
      if(id==='WAR_03'&&!report.events.some(event=>event.type==='skill_status'&&event.skill===id&&event.status==='shieldHit'))throw Error('Missing actual barrier contact');
      if(['WAR_01','WAR_02','WAR_04','WAR_05'].includes(id)&&!report.events.some(event=>event.type==='hit'&&event.skill===id))throw Error('Missing actual skill contact '+id);
      if(!skipWrite.has(id))fs.writeFileSync(path.join(directory,'capture.json'),JSON.stringify({variant,info,presentation,gameHash,reviewInputs,mainURL,graphics:nativeGpu?'ANGLE D3D11':'ANGLE SwiftShader',errors,overlapFrames,...report},null,2));
      console.log('Captured',variant,id,report.frames,report.stats);
    }
  } finally {
    await browser.close();
  }
}
run().catch(error => {console.error(error);process.exitCode=1;}).finally(()=>server.close());
