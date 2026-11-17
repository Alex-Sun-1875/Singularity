// Capture the current Cocos scene with the same actors, simulation and camera in both variants.
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const crypto = require('node:crypto');

const root = path.resolve(__dirname, '../../..');
const cocos = path.join(root, 'src/cocos');
const build = path.join(cocos, 'build/concept-2d');
const cache = path.join(root, 'src/.tmp/thunder-chain-v8');
const {chromium} = require(path.join(cocos, 'node_modules/playwright'));
const options = process.argv.slice(2);
function option(name, fallback) {
  const index = options.indexOf(name);
  return index < 0 ? fallback : options[index + 1];
}
const variant = option('--variant', 'current');
const probe = options.includes('--probe');
const skipWrite = new Set(option('--skip-write','').split(',').filter(Boolean));
const selected = option('--shots', 'BASIC_WAR,THU_01,THU_02,THU_05').split(',');
const formation = [[4.9,.05],[6.4,-1.15],[5.65,1.4],[7.35,.42]];
const shots = {
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
for (const name of ['capture.cjs','refine-modules.cjs','beam-batches.ts','reference-profile.json','approved-thunder-strip.png']) {
  const file=path.join(__dirname,name);
  if(fs.existsSync(file))reviewInputs[name]=crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
}
const main = variant === 'refined'
  ? Buffer.from(require('./refine-modules.cjs').replaceModules(original.toString('utf8'), cocos))
  : original;
const replacements = new Map();
if (variant === 'refined') {
  for (const name of ['fire-pyro-v7', 'fire-low-rolls-v7']) {
    const meta = JSON.parse(fs.readFileSync(path.join(cocos, 'assets/resources/vfx/production', name+'.png.meta'), 'utf8'));
    const directoryURL = '/assets/resources/native/' + meta.uuid.slice(0,2) + '/';
    const folder = path.join(build, directoryURL);
    const file = fs.readdirSync(folder).find(name => name.startsWith(meta.uuid+'.') && name.endsWith('.png'));
    const replacement = path.join(__dirname, '../current-vfx-refinement-v4/assets', name+'.png');
    if (!file || !fs.existsSync(replacement)) throw Error('Missing prepared fire atlas ' + name);
    replacements.set(directoryURL+file, replacement);
  }
}
const mime = {'.js':'text/javascript', '.json':'application/json', '.html':'text/html', '.png':'image/png', '.jpg':'image/jpeg', '.css':'text/css', '.bin':'application/octet-stream', '.wasm':'application/wasm'};
const server = http.createServer((request,response) => {
  const url = decodeURIComponent(new URL(request.url,'http://127.0.0.1').pathname);
  if(url==='/__review/approved-thunder-strip.png'){
    response.setHeader('Content-Type','image/png');
    fs.createReadStream(path.join(__dirname,'approved-thunder-strip.png')).pipe(response);return;
  }
  const filename = path.resolve(build, '.'+(url==='/'?'/index.html':url));
  if (!filename.startsWith(build+path.sep) || !fs.existsSync(filename) || !fs.statSync(filename).isFile()) {
    response.writeHead(404).end();
    return;
  }
  response.setHeader('Content-Type', mime[path.extname(filename)] || 'application/octet-stream');
  if (url === mainURL) response.end(main);
  else fs.createReadStream(replacements.get(url) || filename).pipe(response);
});

async function run() {
  await new Promise(resolve => server.listen(0,'127.0.0.1',resolve));
  const browser = await chromium.launch({headless:true,args:['--enable-webgl','--enable-unsafe-swiftshader','--use-angle=swiftshader','--mute-audio']});
  try {
    const page = await browser.newPage({viewport:{width:960,height:470},deviceScaleFactor:1});
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
    const fixturePath = path.join(__dirname,'../cocos-motion-study-v2/review-fixture.js');
    const fixture = fs.readFileSync(fixturePath,'utf8');
    if (fixture.split('+.13;').length !== 2) throw Error('Recording fixture facing changed');
    await page.addScriptTag({content:fixture.replace('+.13;','+.67;')});
    await page.evaluate(() => installMotionStudy('current'));
    console.log('Ready',variant,gameHash.slice(0,12));
    for (const id of selected) {
      if (!shots[id]) throw Error('Unknown shot '+id);
      const directory = path.join(cache,probe?'probe':'final',variant,id);
      fs.mkdirSync(directory,{recursive:true});
      const info = await page.evaluate(shot => motionStudy.select(shot),{...shots[id],id});
      const presentation = await page.evaluate(async variant => {
        const app=motionStudy.app;
        if (variant==='refined') {
          await app.effects.thunderField.prepareReference();
          // Equipment switches recreate these existing pools. Bind the actual combat camera afterward.
          for (const pool of [app.effects.fireSprites,app.effects.blades,app.effects.thunderContacts]) pool.camera=app.camera;
        }
        return {camera:{position:app.camera.node.worldPosition,forward:app.camera.node.forward,orthoHeight:app.camera.orthoHeight},actorCount:app.actors.inspect().length};
      },variant);
      const frames = Math.round(shots[id].seconds*30);
      const nativeAudit=[];
      console.log('Recording',variant,id,info.renderer,info.origin);
      for (let index=0;index<frames;index++) {
        const save = !skipWrite.has(id) && (!probe || [0,9,12,14,16,18,20,22,25,28,32,36,40,45,50,58,66,78].includes(index));
        const {jpg,audit}=await page.evaluate(({save,index})=>{
          const jpg=motionStudy.next(save),app=motionStudy.app;
          const draws=app.effects.thunderField.reviewStats??[];
          const screen=p=>{const q=app.camera.worldToScreen(new motionStudy.cc.Vec3(...p));return[q.x,470-q.y];};
          return{jpg,audit:{frame:index,draws:draws.map(draw=>({...draw,screenFrom:screen(draw.renderFrom),screenTo:screen(draw.renderTo),screenMid:screen(draw.renderMid)})),field:app.effects.thunderField.inspect()}};
        },{save,index});
        nativeAudit.push(audit);
        if (jpg) fs.writeFileSync(path.join(directory,String(index).padStart(3,'0')+'.jpg'),Buffer.from(jpg,'base64'));
      }
      const report = await page.evaluate(() => ({...motionStudy.report(),fire:motionStudy.app.effects.fireSprites.inspect()}));
      if (errors.length) throw Error(errors.join('\n'));
      if (!info.player?.skeletons?.length) throw Error('Missing native player skeleton');
      if (id!=='BASIC_WAR' && !report.events.some(event=>event.type==='skill_release')) throw Error('Missing real release '+id);
      if(!skipWrite.has(id))fs.writeFileSync(path.join(directory,'capture.json'),JSON.stringify({variant,info,presentation,gameHash,reviewInputs,mainURL,errors,nativeAudit,...report},null,2));
      console.log('Captured',variant,id,report.frames,report.stats);
    }
  } finally {
    await browser.close();
  }
}
run().catch(error => {console.error(error);process.exitCode=1;}).finally(()=>server.close());
