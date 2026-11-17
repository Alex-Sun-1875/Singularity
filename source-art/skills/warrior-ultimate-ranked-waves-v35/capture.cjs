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
  for(const scene of (process.argv.includes('--scene')?[process.argv[process.argv.indexOf('--scene')+1]]:['training','field'])){
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
   await page.evaluate(({profile,fragment,pixels})=>{window.swooshReferenceProfile=profile;window.swooshFragmentSource=fragment;window.swooshFlowPixels=pixels;},{profile:JSON.parse(fs.readFileSync(path.join(__dirname,'swoosh-profile.json'),'utf8')),fragment:fs.readFileSync(path.join(__dirname,'swoosh.frag'),'utf8'),pixels:Array.from(fs.readFileSync(path.join(__dirname,'swoosh-flow.rgba')))});
   await page.addScriptTag({content:fs.readFileSync(path.join(__dirname,'preview.js'),'utf8')});await page.evaluate(()=>installUltimatePreview());
   const ranks=process.argv.includes('--waves')?[Number(process.argv[process.argv.indexOf('--waves')+1])]:(scene==='training'?[1,2,3]:[3]);
   for(const waveCount of ranks)for(const variant of (process.argv.includes('--proposal-only')?['proposal']:['current','proposal'])){
    const skillRank=[1,3,5][waveCount-1],def={id:'WAR_05',family:'WAR',centre:2.65,height:4.90,targets:[[3.6,.1],[4.1,-.8],[4.3,.9]],seconds:3.6};
    const info=await page.evaluate(async({def,variant,waveCount,skillRank})=>{await motionStudy.select(def);motionStudy.state.progression.learned.WAR_05=skillRank;ultimatePreview.enabled=variant==='proposal';ultimatePreview.waveCount=waveCount;ultimatePreview.phase=null;ultimatePreview.phases=[];ultimatePreview.launches.clear();return motionStudy.app.actors.inspect().find(a=>a.id==='player');},{def,variant,waveCount,skillRank});
    const dir=path.join(root,'src/.tmp/warrior-ultimate-ranked-waves-v35',scene,'rank'+waveCount,variant);fs.mkdirSync(dir,{recursive:true});const metrics=[];
    for(let frame=0;frame<108;frame++){
     const r=await page.evaluate(()=>{
      const image=motionStudy.next(true),{app,state,cc}=motionStudy,pool=app.effects.warrior,actor=(app.actors.player??app.actors).active.get('player'),clip=actor.clips[actor.state],animation=clip&&actor.animation.getState(clip.name);
      const crossAngles=[];for(const h of pool.layers.filter(l=>l.node.active&&l.key.endsWith(':ultimate-cross:horizontal'))){const v=pool.layers.find(l=>l.node.active&&l.key===h.key.replace(/horizontal$/,'vertical'));if(v){const axis=l=>{const x=cc.Vec3.transformQuat(new cc.Vec3(),cc.Vec3.UNIT_X,l.node.worldRotation);return Math.atan2(cc.Vec3.dot(x,app.camera.node.up),cc.Vec3.dot(x,app.camera.node.right))*180/Math.PI;};const d=Math.abs(axis(h)-axis(v))%180;crossAngles.push(180-Math.min(d,180-d));}}
      const downAxes=pool.layers.filter(l=>l.node.active&&l.key.endsWith(':ultimate-downcut')).map(l=>{const x=cc.Vec3.transformQuat(new cc.Vec3(),cc.Vec3.UNIT_X,l.node.worldRotation);return Math.atan2(cc.Vec3.dot(x,app.camera.node.up),cc.Vec3.dot(x,app.camera.node.right))*180/Math.PI;});
      const main=pool.layers.filter(l=>l.node.active&&/:ultimate-downcut:wave:\d+$/.test(l.key)),waveIndex=l=>Number(l.key.split(':').at(-1));
      const waveNormals=main.map(l=>{const n=cc.Vec3.transformQuat(new cc.Vec3(),cc.Vec3.UNIT_X,l.node.worldRotation);return {waveIndex:waveIndex(l),x:n.x,y:n.y,z:n.z};});
      const tipWidths=main.map(l=>{const p=l.renderer.mesh.readAttribute(0,'a_position'),distance=(a,b)=>Math.hypot(p[a*3]-p[b*3],p[a*3+1]-p[b*3+1],p[a*3+2]-p[b*3+2]);return {waveIndex:waveIndex(l),start:distance(0,16),end:distance(64*17,64*17+16)};});
      const swooshMetrics=main.map(l=>{
       const p=l.renderer.mesh.readAttribute(0,'a_position'),v=new cc.Vec3();let minVertexHeight=Infinity,maxVertexHeight=-Infinity,frontZ=-Infinity,bellyHeight=Infinity;
       for(let i=0;i<p.length;i+=3){frontZ=Math.max(frontZ,p[i+2]);v.set(p[i],p[i+1],p[i+2]);cc.Vec3.transformMat4(v,v,l.node.worldMatrix);const height=v.y-pool.ground(v.x,v.z,l.node.worldPosition.y);minVertexHeight=Math.min(minVertexHeight,height);maxVertexHeight=Math.max(maxVertexHeight,height);}
       const tail=new cc.Vec3(p[0],p[1],p[2]);cc.Vec3.transformMat4(tail,tail,l.node.worldMatrix);
       const tipIndex=64*17*3,tip=new cc.Vec3(p[tipIndex],p[tipIndex+1],p[tipIndex+2]);cc.Vec3.transformMat4(tip,tip,l.node.worldMatrix);
       for(let i=35;i<=64;i++){const index=i*17*3;v.set(p[index],p[index+1],p[index+2]);cc.Vec3.transformMat4(v,v,l.node.worldMatrix);bellyHeight=Math.min(bellyHeight,v.y-pool.ground(v.x,v.z,l.node.worldPosition.y));}
       const width=(a,b)=>Math.hypot(p[a*3]-p[b*3],p[a*3+1]-p[b*3+1],p[a*3+2]-p[b*3+2]);
       return {waveIndex:waveIndex(l),tailWorld:[tail.x,tail.y,tail.z],tailHeight:tail.y-pool.ground(tail.x,tail.z,l.node.worldPosition.y),tipWorld:[tip.x,tip.y,tip.z],tipHeight:tip.y-pool.ground(tip.x,tip.z,l.node.worldPosition.y),bellyHeight,tailLocalZ:p[2],frontLocalZ:frontZ,headSectionWidth:width(46*17,46*17+10),minVertexHeight,maxVertexHeight,material:l.renderer.sharedMaterial.name,effect:l.renderer.sharedMaterial.effectAsset.name};
      });
      return {image,phase:ultimatePreview.phase,phases:ultimatePreview.phases,warrior:pool.inspect(),renderReady:pool.layers.filter(l=>l.node.active).every(l=>l.renderer.model?.subModels.length&&l.renderer.model?.worldBounds),crossAngles,downAxes,waveNormals,tipWidths,swooshMetrics,pose:{state:actor.state,time:animation?.time,clipDuration:clip?.duration,hand:app.actors.playerPresentation()?.hand},action:state.action?{id:state.action.skillId,elapsed:state.action.elapsed,duration:state.action.duration}:null};
     });
     fs.writeFileSync(path.join(dir,String(frame).padStart(3,'0')+'.jpg'),Buffer.from(r.image,'base64'));delete r.image;metrics.push({frame,...r});
     if(!r.renderReady||r.warrior.droppedLayers)throw Error('Renderer or pool failure');if(r.waveNormals.some(n=>Math.abs(n.y)>.00001))throw Error('Hook wave is not upright');if(r.tipWidths.some(t=>t.start>1e-5||t.end>1e-5))throw Error('Hook terminal is not pointed');
     if(r.swooshMetrics.some(l=>l.frontLocalZ<=l.tailLocalZ+1||l.minVertexHeight<.06||l.bellyHeight>.20||l.tailHeight<.06||l.tailHeight>.20||l.tipHeight<=l.bellyHeight+.25||l.effect!=='Isolated:RankedPressure:v35'))throw Error('Ranked wave geometry/material failure: '+JSON.stringify({frame,layers:r.swooshMetrics}));
    }
    const report=await page.evaluate(()=>motionStudy.report());
    if(!info.skeletons?.length||!report.clips.includes('attack_sword_3'))throw Error('Native three-clip chain missing');
    if(variant==='proposal'&&!metrics.some(m=>m.swooshMetrics.length))throw Error('Redesigned swoosh never appeared');
    const result={gameHash,scene,variant,skillRank,waveCount,errors,info,...report,metrics};fs.writeFileSync(path.join(dir,'capture.json'),JSON.stringify(result,null,2));
    console.log('Captured',scene,'rank',skillRank,'waves',waveCount,variant,report.frames,'frames',report.clips.join(','),'max layers',Math.max(...metrics.map(m=>m.warrior.active.length)));
   }
   if(errors.length)throw Error('Game console errors');await page.close();
  }
 }finally{await browser.close();server.close();}
}
run().catch(e=>{console.error(e);process.exitCode=1;server.close();});
