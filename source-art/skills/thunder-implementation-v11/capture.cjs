// Capture the current Cocos scene with the same actors, simulation and camera in both variants.
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const crypto = require('node:crypto');

const root = path.resolve(__dirname, '../../..');
const cocos = path.join(root, 'src/cocos');
const build = path.join(cocos, 'build/concept-2d');
const cache = path.join(root, 'src/.tmp/thunder-implementation-v11');
const {chromium} = require(path.join(cocos, 'node_modules/playwright'));
const options = process.argv.slice(2);
function option(name, fallback) {
  const index = options.indexOf(name);
  return index < 0 ? fallback : options[index + 1];
}
const variant = 'implemented';
const probe = options.includes('--probe');
const take = option('--take','final');
const seconds = Number(option('--seconds','0'));
if(!/^[a-z0-9-]+$/i.test(take)||!Number.isFinite(seconds)||seconds!==0&&(seconds<1.6||seconds>4.5))throw Error('Invalid review capture options');
const skipWrite = new Set(option('--skip-write','').split(',').filter(Boolean));
const selected = option('--shots', 'THU_01,CHAIN_R5,NETWORK_R5').split(',');
const formation = [[5.2,0],[6.5,-1.6],[6.5,1.6],[7.9,-.9],[7.9,1.1],[9.1,-2.4],[9.1,0],[9.1,2.4],[3.7,-1.9],[3.7,1.9],[5.2,-3.2],[5.2,3.2]];
const shots = {
  NETWORK_R1:{skillId:'THU_05',family:'THU',rank:1,centre:4.3,height:4.9,targets:formation,seconds:3},
  NETWORK_R5:{skillId:'THU_05',family:'THU',rank:5,centre:4.3,height:4.9,targets:formation,seconds:4},
  CHAIN_R5:{skillId:'THU_02',family:'THU',rank:5,centre:4.3,height:4.9,targets:formation,seconds:4},
  BASIC_WAR: {family:'WAR', centre:1.0, height:2.35, targets:[[1.65,.04],[2.50,.20]], seconds:1.95},
  THU_01: {family:'THU', centre:3.0, height:3.10, targets:[[5.3,.05],[6.6,.05]], seconds:1.90},
  THU_02: {family:'THU', centre:3.1, height:3.10, targets:formation, seconds:1.90},
  THU_05: {family:'THU', centre:3.1, height:3.45, targets:formation, seconds:2.55},
  FIR_01: {family:'FIR', centre:2.9, height:3.05, targets:[[5.8,.03],[6.15,.7]], seconds:1.90},
  FIR_02: {family:'FIR', centre:2.7, height:3.85, targets:[[4.7,.10],[5.85,-.85],[5.3,1.35]], seconds:2.30},
  FIR_05: {family:'FIR', centre:3.2, height:3.6, targets:formation, seconds:3.25},
};
const mainDirectory = path.join(build, 'assets/main');
const mainName = fs.readdirSync(mainDirectory).find(name => /^index\..+\.js$/.test(name));
const mainURL = '/assets/main/' + mainName;
const original = fs.readFileSync(path.join(mainDirectory, mainName));
const gameHash = crypto.createHash('sha256').update(original).digest('hex');
const reviewInputs = {};
for (const name of ['capture.cjs','crowd-fixture.js']) {
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
  const browser = await chromium.launch({headless:true,args:['--enable-webgl','--enable-unsafe-swiftshader','--use-angle=swiftshader','--mute-audio']});
  try {
    const page = await browser.newPage({viewport:{width:1280,height:626},deviceScaleFactor:1});
    const errors = [];
    page.on('pageerror', error => { errors.push(error.message); console.error(error.message); });
    await page.goto('http://127.0.0.1:'+server.address().port+'/?view=3d&player=3d&test=max',{waitUntil:'load'});
    await page.waitForFunction(() => globalThis.System,undefined,{timeout:45000});
    await page.evaluate(async () => {
      const cc = await System.import('cc');
      globalThis.findCurrentChapter = () => {
        function find(node) { return node?.getComponent('ChapterGame') || node?.children.map(find).find(Boolean); }
        return find(cc.director.getScene());
      };
    });
    await page.waitForFunction(() => {
      const app=findCurrentChapter();
      return app?.session && app?.actors && !app.loading && app.platform.auth.ready;
    },undefined,{timeout:180000});
    const fixturePath = path.join(__dirname,'crowd-fixture.js');
    const fixture = fs.readFileSync(fixturePath,'utf8');
    if (fixture.split('+.13;').length !== 2) throw Error('Recording fixture facing changed');
    await page.addScriptTag({content:fixture.replace('+.13;','+.67;')});
    await page.evaluate(positions=>{globalThis.reviewCrowdPositions=positions;},formation);
    await page.evaluate(() => installMotionStudy('current'));
    console.log('Ready',variant,gameHash.slice(0,12));
    for (const id of selected) {
      if (!shots[id]) throw Error('Unknown shot '+id);
      const directory = path.join(cache,probe?'probe':take,variant,id);
      fs.mkdirSync(directory,{recursive:true});
      const info = await page.evaluate(shot => motionStudy.select(shot),{...shots[id],id:shots[id].skillId??id});
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
          const draws=app.effects.thunderField.inspectBeams();
          const screen=p=>{const q=app.camera.worldToScreen(new motionStudy.cc.Vec3(...p));return[q.x,motionStudy.cc.game.canvas.height-q.y];};
          return{jpg,audit:{frame:index,draws:draws.map(draw=>({...draw,screenFrom:screen(draw.renderFrom),screenTo:screen(draw.renderTo),screenMid:screen(draw.renderMid),screenPath:draw.renderPath.map(screen)})),field:app.effects.thunderField.inspect(),ground:app.effects.groundThunder.inspect(),patterns:app.effects.skills.inspectThunder(),action:app.session.state.action?.kind??null}};
        },{save,index});
        nativeAudit.push(audit);
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
