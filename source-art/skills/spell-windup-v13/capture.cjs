// Capture the current Cocos scene with the same actors, simulation and camera in both variants.
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const crypto = require('node:crypto');

const root = path.resolve(__dirname, '../../..');
const cocos = path.join(root, 'src/cocos');
const cache = path.join(root, 'src/.tmp/spell-windup-v13');
const before=process.argv.includes('--before');
const build = before?path.join(root,'src/.tmp/thunder-family-v12/web'):path.join(cocos,'build/spell-windup-v13');
const {chromium} = require(path.join(cocos, 'node_modules/playwright'));
const options = process.argv.slice(2);
function option(name, fallback) {
  const index = options.indexOf(name);
  return index < 0 ? fallback : options[index + 1];
}
const variant = before?'before':'after';
const probe = options.includes('--probe');
const take = option('--take','final');
const seconds = Number(option('--seconds','0'));
if(!/^[a-z0-9-]+$/i.test(take)||!Number.isFinite(seconds)||seconds!==0&&(seconds<1.6||seconds>10))throw Error('Invalid review capture options');
const skipWrite = new Set(option('--skip-write','').split(',').filter(Boolean));
const selected = option('--shots', 'FIR_01,FIR_02,THU_01,THU_05,THU_06').split(',');
const shots={
 ...Object.fromEntries(['FIR_01','FIR_02','FIR_03','FIR_04','FIR_05','THU_01','THU_02','THU_04','THU_05','THU_06'].map(id=>[id,{family:id.slice(0,3),rank:5,centre:2.3,height:2.65,targets:[[4.6,0]],seconds:2.2}])),
};
const formation=Array.from(new Map(Object.values(shots).flatMap(s=>s.targets).map(p=>[JSON.stringify(p),p])).values());
const mainDirectory = path.join(build, 'assets/main');
const mainName = fs.readdirSync(mainDirectory).find(name => /^index\..+\.js$/.test(name));
const mainURL = '/assets/main/' + mainName;
const original = fs.readFileSync(path.join(mainDirectory, mainName));
const gameHash = crypto.createHash('sha256').update(original).digest('hex');
const reviewInputs = {};
for (const name of ['capture.cjs','fixture-patches.cjs','../thunder-implementation-v11/crowd-fixture.js']) {
  const file=path.join(__dirname,name);
  if(fs.existsSync(file))reviewInputs[name]=crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
}
// Serve the actual new build without injecting replacement gameplay or VFX.
const main=original;
const mime = {'.js':'text/javascript', '.json':'application/json', '.html':'text/html', '.png':'image/png', '.jpg':'image/jpeg', '.css':'text/css', '.bin':'application/octet-stream', '.wasm':'application/wasm'};
const server = http.createServer((request,response) => {
  const url = decodeURIComponent(new URL(request.url,'http://127.0.0.1').pathname);
  const filename = path.resolve(build, '.'+(url==='/'?'/index.html':url));
  if (!filename.startsWith(build+path.sep) || !fs.existsSync(filename) || !fs.statSync(filename).isFile()) {
    response.writeHead(404).end();
    return;
  }
  response.setHeader('Content-Type', mime[path.extname(filename)] || 'application/octet-stream');
  if (url === mainURL) response.end(main);
  else fs.createReadStream(filename).pipe(response);
});

async function run() {
  await new Promise(resolve => server.listen(0,'127.0.0.1',resolve));
  const browser = await chromium.launch({headless:true,args:['--enable-webgl','--ignore-gpu-blocklist','--use-angle=d3d11','--mute-audio','--remote-debugging-port=9237']});
  try {
    const page = await browser.newPage({viewport:{width:1280,height:626},deviceScaleFactor:1});
    const errors = [],pending=new Set();
    page.on('request',r=>{if(r.url().startsWith('http://127.0.0.1:'))pending.add(r);});
    page.on('requestfinished',r=>pending.delete(r));page.on('requestfailed',r=>{pending.delete(r);console.error('Request failed',new URL(r.url()).pathname);});
    page.on('console', message=>{if(message.type()==='error')console.error('Browser:',message.text().slice(0,1000));});
    page.on('pageerror', error => { errors.push(error.message); console.error(error.message); });
    console.log('Opening actual build',gameHash.slice(0,12));
    await page.goto('http://127.0.0.1:'+server.address().port+'/?view=3d&player=3d&test=max',{waitUntil:'load'});
    await page.bringToFront();
    console.log('Page loaded');
    await page.waitForFunction(() => globalThis.System,undefined,{timeout:45000});
    await page.evaluate(async () => {
      const cc = await System.import('cc');
      globalThis.findCurrentChapter = () => {
        function find(node) { return node?.getComponent('ChapterGame') || node?.children.map(find).find(Boolean); }
        return find(cc.director.getScene());
      };
      globalThis.thunderBootCC=cc;
      cc.game.pause();
      globalThis.thunderBootPump=setInterval(()=>{if(cc.director.root)cc.director.tick(1/60);},100);
    });
    console.log('Engine imported, manual warmup clock');
    const startupLog=setInterval(async()=>{console.log('Pending assets',Array.from(pending).slice(-5).map(r=>new URL(r.url()).pathname));try{console.log('Startup progress',await page.evaluate(()=>{const a=findCurrentChapter();return{loading:a?.loading,status:a?.loadingScreen?.status,progress:a?.loadingScreen?.progress,actors:a?.actors?.inspect?.().length,failure:a?.failure,fx:a?.effects?.preparedFamily,prewarm:a?.preparationResources?.inspect(),paused:typeof globalThis.thunderBootCC.game.isPaused==='function'?globalThis.thunderBootCC.game.isPaused():globalThis.thunderBootCC.game.isPaused};}));}catch{}},20000);
    await page.waitForFunction(() => {
      const app=findCurrentChapter();
      return app?.session && app?.actors && !app.loading && app.platform.auth.ready;
    },undefined,{timeout:1200000,polling:100}).catch(async error=>{
      console.error('Startup state',await page.evaluate(()=>{const app=findCurrentChapter();return{chapter:!!app,session:!!app?.session,actors:!!app?.actors,loading:app?.loading,failure:app?.failure,auth:app?.platform?.auth?.ready,body:document.body.innerText.slice(0,800)};}));
      throw error;
    }).finally(()=>clearInterval(startupLog));
    const fixturePath=path.join(__dirname,'../thunder-implementation-v11/crowd-fixture.js');
    const fixture=require('./fixture-patches.cjs').prepare(fs.readFileSync(fixturePath,'utf8'));
    await page.addScriptTag({content:fixture});
    await page.evaluate(()=>{
      globalThis.thunderFamilyDrive=(shot,t,sub,player,state)=>{
        const target=state.enemies[0],aim=target?Math.atan2(target.x-player.x,target.z-player.z):player.angle;
        const side=globalThis.thunderFamilySide;
        if(shot.id==='THU_03'){
          if(t<(shot.start??.3))return{x:side.x*.16,z:side.z*.16,aim};
          return{aim,attack:t>2.55&&(state.combat.buffs.thunderCharges??0)>0};
        }
        if(shot.id==='THU_06'){
          if(t>.75&&(state.combat.buffs.stormWardUntil??0)>state.time)state.enemies[0].trainingAttacks=true;
          if((state.combat.buffs.stormWardUntil??0)>state.time&&state.combat.buffs.stormWardReduction===0&&globalThis.thunderFamilyGuardAt===null)globalThis.thunderFamilyGuardAt=t;
          const since=t-(globalThis.thunderFamilyGuardAt??-100);
          if(since>=.05&&since<.60)return{x:side.x*.50,z:side.z*.50,aim};
        }
        return{aim};
      };
    });
    await page.evaluate(positions=>{globalThis.reviewCrowdPositions=positions;},formation);
    console.log('Preparing native fixture');
    await page.evaluate(() => installMotionStudy('current'));
    await page.evaluate(()=>{clearInterval(globalThis.thunderBootPump);globalThis.thunderBootPump=undefined;});
    console.log('Ready',variant,gameHash.slice(0,12));
    for (const id of selected) {
      if (!shots[id]) throw Error('Unknown shot '+id);
      const directory = path.join(cache,probe?'probe':take,variant,id);
      fs.mkdirSync(directory,{recursive:true});
      const info = await page.evaluate(shot => motionStudy.select(shot),{...shots[id],id:shots[id].skillId??id});
      await page.evaluate(info=>{const dx=info.aim.x-info.origin.x,dz=info.aim.z-info.origin.z,length=Math.hypot(dx,dz);globalThis.thunderFamilySide={x:dz/length,z:-dx/length};globalThis.thunderFamilyGuardAt=null;},info);
      const presentation = await page.evaluate(async variant => {
        const app=motionStudy.app;
        const targets=app.session.state.enemies.map((enemy,i)=>{const p=app.camera.worldToScreen(new motionStudy.cc.Vec3(enemy.x,app.world.height(enemy)+1.05,enemy.z));const label=app.camera.worldToScreen(new motionStudy.cc.Vec3(enemy.x,app.world.height(enemy)+2.2,enemy.z));return{number:i+1,id:enemy.id,x:enemy.x,z:enemy.z,screen:[p.x,motionStudy.cc.game.canvas.height-p.y],label:[label.x,motionStudy.cc.game.canvas.height-label.y]};});
        return {camera:{position:app.camera.node.worldPosition,forward:app.camera.node.forward,orthoHeight:app.camera.orthoHeight},actorCount:app.actors.inspect().length,targets};
      },variant);
      const frames = Math.round((seconds||shots[id].seconds)*30);
      const nativeAudit=[];
      console.log('Recording',variant,id,info.renderer,info.origin);
      for (let index=0;index<frames;index++) {
        const save = !skipWrite.has(id) && (!probe || [0,9,12,14,16,18,20,22,25,28,32,36,40,45,50,58,66,78].includes(index));
        const {jpg,audit}=await page.evaluate(({save,index})=>{
          const jpg=motionStudy.next(save),app=motionStudy.app;
          const draws=app.effects.thunderField.inspectBeams(),hand=app.effects.playerSource?.()?.hand;
          const screen=p=>{const q=app.camera.worldToScreen(new motionStudy.cc.Vec3(...p));return[q.x,motionStudy.cc.game.canvas.height-q.y];};
          const presentation=app.effects.playerSource?.(),actor=(app.actors.player??app.actors).active.get('player'),clip=actor.clips[actor.state],anim=clip&&actor.animation.getState(clip.name);
          const castHand=presentation?.castHand;
          return{jpg,audit:{frame:index,draws:draws.map(draw=>({...draw,screenFrom:screen(draw.renderFrom),screenTo:screen(draw.renderTo),screenMid:screen(draw.renderMid),screenPath:draw.renderPath.map(screen)})),field:app.effects.thunderField.inspect(),fire:app.effects.fireSprites.inspect(),ground:app.effects.groundThunder.inspect(),patterns:app.effects.skills.inspectThunder(),action:app.session.state.action?{...app.session.state.action}:null,presentation,poseFraction:anim&&clip?anim.time/clip.duration:null,castHandScreen:castHand?screen([castHand.x,castHand.y,castHand.z]):undefined,buffs:{...app.session.state.combat.buffs},shield:app.session.state.player.shield,player:{x:app.session.state.player.x,z:app.session.state.player.z,hp:app.session.state.player.hp},hand,handScreen:hand?screen([hand.x,hand.y,hand.z]):undefined,time:app.session.state.time,playerScreen:screen([app.session.state.player.x,app.world.height(app.session.state.player)+.90,app.session.state.player.z]),groundHeight:app.world.height(app.session.state.player)}};
        },{save,index});
        nativeAudit.push(audit);
        if(index%30===0)console.log('Frame',id,index,'/',frames);
        if (jpg) fs.writeFileSync(path.join(directory,String(index).padStart(3,'0')+'.jpg'),Buffer.from(jpg,'base64'));
      }
      const report = await page.evaluate(() => ({...motionStudy.report(),fire:motionStudy.app.effects.fireSprites.inspect()}));
      if (errors.length) throw Error(errors.join('\n'));
      if (!info.player?.skeletons?.length) throw Error('Missing native player skeleton');
      if (id!=='BASIC_WAR' && !report.events.some(event=>event.type==='skill_release')) throw Error('Missing real release '+id);
      if(!skipWrite.has(id))fs.writeFileSync(path.join(directory,'capture.json'),JSON.stringify({variant,caseId:id,info,presentation,gameHash,reviewInputs,mainURL,errors,nativeAudit,...report},null,2));
      console.log('Captured',variant,id,report.frames,report.stats);
    }
  } finally {
    await browser.close();
  }
}
run().catch(error => {console.error(error);process.exitCode=1;}).finally(()=>server.close());
