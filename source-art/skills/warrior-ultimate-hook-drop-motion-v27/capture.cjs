// Capture current compiled Cocos game plus one explicitly isolated VFX proposal override.
const fs=require('node:fs'),path=require('node:path'),http=require('node:http'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'../../..'),cocos=path.join(root,'src/cocos');
const build=path.resolve(root,process.argv[process.argv.indexOf('--build')+1]||'src/.tmp/warrior-ultimate-cross-down-v25-build');
const {chromium}=require(path.join(cocos,'node_modules/playwright'));
const main=path.join(build,'assets/main',fs.readdirSync(path.join(build,'assets/main')).find(n=>/^index\..+\.js$/.test(n)));
const gameHash=crypto.createHash('sha256').update(fs.readFileSync(main)).digest('hex');
const server=http.createServer((req,res)=>{const p=decodeURIComponent(new URL(req.url,'http://localhost').pathname),file=path.resolve(build,'.'+(p==='/'?'/index.html':p));if(!file.startsWith(build+path.sep)||!fs.existsSync(file)||!fs.statSync(file).isFile())return res.writeHead(404).end();const type={'.js':'text/javascript','.json':'application/json','.html':'text/html','.wasm':'application/wasm','.css':'text/css','.png':'image/png','.jpg':'image/jpeg'}[path.extname(file)];if(type)res.setHeader('Content-Type',type);fs.createReadStream(file).pipe(res);});
async function run(){
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 const browser=await chromium.launch({headless:true,args:['--enable-webgl','--use-angle=d3d11','--ignore-gpu-blocklist','--mute-audio','--disable-background-timer-throttling','--disable-renderer-backgrounding']});
 try{
  for(const scene of ['training','field']){
   const page=await browser.newPage({viewport:{width:480,height:235},deviceScaleFactor:1}),errors=[];
   page.on('pageerror',e=>{errors.push(e.message);console.error(e.message);});page.on('console',m=>{if(m.type()==='error'){errors.push(m.text());console.error(m.text().slice(0,200));}});
   await page.goto('http://127.0.0.1:'+server.address().port+'/?view=2d&player=3d&test=max');
   await page.waitForFunction(()=>globalThis.System,undefined,{timeout:45000});
   await page.evaluate(()=>{globalThis.findChapter=async()=>{const cc=await System.import('cc');function find(n){return n?.getComponent('ChapterGame')||n?.children.map(find).find(Boolean);}return {app:find(cc.director.getScene()),cc};};});
   const deadline=Date.now()+180000;
   while(true){const ready=await page.evaluate(async()=>{const {app,cc}=await findChapter();if(app?.session&&app?.actors&&app.loading){cc.game.resume();cc.director.tick(1/60);}return !!(app?.session&&app.actors&&!app.loading&&app.platform.auth.ready);});if(ready)break;if(Date.now()>deadline)throw Error('Game startup timeout');await new Promise(r=>setTimeout(r,300));}
   await page.setViewportSize({width:1280,height:624});await page.evaluate(async()=>{const {cc}=await findChapter();cc.view.resizeWithBrowserSize(true);cc.view.setFrameSize(1280,624);cc.game.resume();cc.director.tick(1/60);});
   await page.addScriptTag({content:fs.readFileSync(path.join(__dirname,'review-fixture.js'),'utf8').replace('+.13;','+.67;')});await page.evaluate(scene=>installMotionStudy(scene==='training'?'training':'current'),scene);
   await page.evaluate(()=>motionStudy.app.effects.prepareEquipment(motionStudy.app.session));
   await page.addScriptTag({content:fs.readFileSync(path.join(__dirname,'preview.js'),'utf8')});await page.evaluate(()=>installUltimatePreview());
   for(const variant of (process.argv.includes('--proposal-only')?['proposal']:['current','proposal'])){
    const def={id:'WAR_05',family:'WAR',centre:2.15,height:4.30,targets:[[3.6,.1],[4.1,-.8],[4.3,.9]],seconds:3};
    const info=await page.evaluate(async({def,variant})=>{await motionStudy.select(def);ultimatePreview.enabled=variant==='proposal';ultimatePreview.phase=null;return motionStudy.app.actors.inspect().find(a=>a.id==='player');},{def,variant});
    const dir=path.join(root,'src/.tmp/warrior-ultimate-hook-drop-v27',scene,variant);fs.mkdirSync(dir,{recursive:true});const metrics=[];
    for(let frame=0;frame<90;frame++){
     const r=await page.evaluate(()=>{
      const image=motionStudy.next(true),{app,state,cc}=motionStudy,pool=app.effects.warrior,actor=(app.actors.player??app.actors).active.get('player'),clip=actor.clips[actor.state],animation=clip&&actor.animation.getState(clip.name);
      const crossAngles=[];for(const h of pool.layers.filter(l=>l.node.active&&l.key.endsWith(':ultimate-cross:horizontal'))){const v=pool.layers.find(l=>l.node.active&&l.key===h.key.replace(/horizontal$/,'vertical'));if(v){const axis=l=>{const x=cc.Vec3.transformQuat(new cc.Vec3(),cc.Vec3.UNIT_X,l.node.worldRotation);return Math.atan2(cc.Vec3.dot(x,app.camera.node.up),cc.Vec3.dot(x,app.camera.node.right))*180/Math.PI;};const d=Math.abs(axis(h)-axis(v))%180;crossAngles.push(180-Math.min(d,180-d));}}
      const downAxes=pool.layers.filter(l=>l.node.active&&l.key.endsWith(':ultimate-downcut')).map(l=>{const x=cc.Vec3.transformQuat(new cc.Vec3(),cc.Vec3.UNIT_X,l.node.worldRotation);return Math.atan2(cc.Vec3.dot(x,app.camera.node.up),cc.Vec3.dot(x,app.camera.node.right))*180/Math.PI;});
      return {image,phase:ultimatePreview.phase,warrior:pool.inspect(),renderReady:pool.layers.filter(l=>l.node.active).every(l=>l.renderer.model?.subModels.length&&l.renderer.model?.worldBounds),crossAngles,downAxes,pose:{state:actor.state,time:animation?.time,clipDuration:clip?.duration,hand:app.actors.playerPresentation()?.hand},action:state.action?{id:state.action.skillId,elapsed:state.action.elapsed,duration:state.action.duration}:null};
     });
     fs.writeFileSync(path.join(dir,String(frame).padStart(3,'0')+'.jpg'),Buffer.from(r.image,'base64'));delete r.image;metrics.push({frame,...r});
     if(!r.renderReady||r.warrior.droppedLayers)throw Error('Renderer or pool failure');if(r.crossAngles.some(a=>Math.abs(a-120)>.03))throw Error('Projected cross angle changed');if(r.downAxes.some(a=>Math.abs(Math.abs(a)-90)>.03))throw Error('Third wave is not vertical');
    }
    const report=await page.evaluate(()=>motionStudy.report());
    if(!info.skeletons?.length||!report.clips.includes('attack_sword_3'))throw Error('Native three-clip chain missing');
    if(variant==='proposal'&&!metrics.some(m=>m.warrior.active.some(l=>l.key.endsWith(':ultimate-downcut'))&&m.crossAngles.length))throw Error('Combined crossing and downcut never appear together');
    const result={gameHash,scene,variant,errors,info,...report,metrics};fs.writeFileSync(path.join(dir,'capture.json'),JSON.stringify(result,null,2));
    console.log('Captured',scene,variant,report.frames,'frames',report.clips.join(','),'max layers',Math.max(...metrics.map(m=>m.warrior.active.length)));
   }
   if(errors.length)throw Error('Game console errors');await page.close();
  }
 }finally{await browser.close();server.close();}
}
run().catch(e=>{console.error(e);process.exitCode=1;server.close();});
