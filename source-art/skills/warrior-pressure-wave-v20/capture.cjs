// Real compiled Cocos game; no module, texture or animation overrides.
const fs=require('node:fs'),path=require('node:path'),http=require('node:http'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'../../..'),cocos=path.join(root,'src/cocos'),build=process.argv.includes('--build')?path.resolve(process.argv[process.argv.indexOf('--build')+1]):path.join(cocos,'build/concept-2d');
const {chromium}=require(path.join(cocos,'node_modules/playwright')),probe=process.argv.includes('--probe'),training=process.argv.includes('--training');
const mainDir=path.join(build,'assets/main'),mainName=fs.readdirSync(mainDir).find(n=>/^index\..+\.js$/.test(n)),main=fs.readFileSync(path.join(mainDir,mainName)),gameHash=crypto.createHash('sha256').update(main).digest('hex');
if(!main.includes(Buffer.from('WarriorSkillEffects'))||!main.includes(Buffer.from('warrior-pressure-wave-v2')))throw Error('Pressure-wave integration missing from compiled game');
const mime={'.js':'text/javascript','.json':'application/json','.html':'text/html','.png':'image/png','.jpg':'image/jpeg','.css':'text/css','.bin':'application/octet-stream','.wasm':'application/wasm'};
const server=http.createServer((req,res)=>{const url=decodeURIComponent(new URL(req.url,'http://127.0.0.1').pathname),file=path.resolve(build,'.'+(url==='/'?'/index.html':url));if(!file.startsWith(build+path.sep)||!fs.existsSync(file)||!fs.statSync(file).isFile()){res.writeHead(404).end();return;}res.setHeader('Content-Type',mime[path.extname(file)]||'application/octet-stream');fs.createReadStream(file).pipe(res);});
const shots={
 BASIC_WAR:{family:'WAR',centre:1.05,height:2.65,targets:[[1.65,.04],[2.5,.2]],seconds:1.95},
 WAR_01:{family:'WAR',centre:1.8,height:3,targets:[[3.7,.02]],seconds:2.4},
 WAR_02:{family:'WAR',centre:2.4,height:3.3,targets:[[3.4,.38],[4.3,1.1]],seconds:1.8},
 WAR_03:{family:'WAR',centre:.75,height:2.4,targets:[[1.2,0]],seconds:3.6,retaliate:true},
 WAR_04:{family:'WAR',centre:.15,height:2.9,targets:[[2,0],[-1.1,1.65],[-1.1,-1.65]],seconds:2.3},
 WAR_05:{family:'WAR',centre:2.2,height:3.8,targets:[[3.6,.1],[4.1,-.8],[4.3,.9]],seconds:2.25},
 WAR_P1:{family:'WAR',centre:1.4,height:2.6,targets:[[2.74,.02]],seconds:2.25,castSkill:'WAR_01',passive:'WAR_P1'},
 WAR_P2:{family:'WAR',centre:.75,height:2.4,targets:[[1.2,0]],seconds:3.6,castSkill:'WAR_03',passive:'WAR_P2',retaliate:true}
};
async function run(){
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 const browser=await chromium.launch({headless:true,args:['--enable-webgl','--use-angle=d3d11','--ignore-gpu-blocklist','--mute-audio','--disable-background-timer-throttling','--disable-renderer-backgrounding']});
 try{
  const page=await browser.newPage({viewport:{width:480,height:235},deviceScaleFactor:1}),errors=[],consoleErrors=[];
  page.on('pageerror',e=>{errors.push(e.message);console.error(e.message);});page.on('console',m=>{if(m.type()==='error'){consoleErrors.push(m.text());console.error(m.text().slice(0,200));}});
  await page.goto('http://127.0.0.1:'+server.address().port+'/?view=2d&player=3d&test=max',{waitUntil:'load'});
  await page.waitForFunction(()=>globalThis.System,undefined,{timeout:45000});
  await page.evaluate(async()=>{const cc=await System.import('cc');globalThis.findCurrentChapter=()=>{function find(n){return n?.getComponent('ChapterGame')||n?.children.map(find).find(Boolean);}return find(cc.director.getScene());};});
  const deadline=Date.now()+180000;
  while(true){const ready=await page.evaluate(async()=>{const a=findCurrentChapter(),cc=await System.import('cc');if(a?.session&&a?.actors&&a.loading){cc.game.resume();cc.director.tick(1/60);}return !!(a?.session&&a?.actors&&!a.loading&&a.platform.auth.ready);});if(ready)break;if(Date.now()>deadline)throw Error('Game startup timeout');await new Promise(r=>setTimeout(r,500));}
  await page.setViewportSize({width:960,height:470});await page.evaluate(async()=>{const cc=await System.import('cc');cc.view.resizeWithBrowserSize(true);cc.view.setFrameSize(960,470);cc.game.resume();cc.director.tick(1/60);});
  await page.addScriptTag({content:fs.readFileSync(path.join(__dirname,'review-fixture.js'),'utf8').replace('+.13;','+.67;')});await page.evaluate(setup=>installMotionStudy(setup),training?'training':'current');
  console.log('Ready actual warrior integration',gameHash.slice(0,12));
  if(process.argv.includes('--hud-only')){
   await page.evaluate(def=>motionStudy.select(def),{...shots.WAR_04,id:'WAR_04'});
   await page.setViewportSize({width:844,height:390});
   await page.evaluate(()=>{const {app,cc}=motionStudy;cc.view.setFrameSize(844,390);app.hud.root.active=true;app.enabled=true;cc.game.resume();});
   await page.waitForFunction(()=>{const {app}=motionStudy;return app.hud.actionIcons.get('combat3')?.spriteFrame&&app.hud.iconPaths.get('combat3')==='rpg-war-04';});
   await page.waitForTimeout(300);
   const hud=await page.evaluate(()=>{const {app,cc}=motionStudy,sprite=app.hud.actionIcons.get('combat3'),frame=sprite.spriteFrame,texture=frame.texture,canvas=document.createElement('canvas');canvas.width=texture.width;canvas.height=texture.height;canvas.getContext('2d').drawImage(texture.image.data,0,0);cc.game.pause();return {family:app.session.state.combat.family,skill:app.session.state.combat.activeSlots[3],icon:app.hud.iconPaths.get('combat3'),texture: texture._uuid,rect:frame.rect,size:[texture.width,texture.height],atlas:canvas.toDataURL('image/png').split(',')[1]};});
   if(hud.skill!=='WAR_04'||hud.size[0]!==1024||hud.size[1]!==512||Math.abs(hud.rect.x-268.032)>.01||Math.abs(hud.rect.y-268.032)>.01)throw Error('HUD whirlwind atlas binding mismatch '+JSON.stringify({...hud,atlas:undefined}));
   fs.writeFileSync(path.join(__dirname,'hud-icon-runtime-atlas.png'),Buffer.from(hud.atlas,'base64'));delete hud.atlas;
   await page.screenshot({path:path.join(__dirname,'hud-icon-runtime-844.png')});
   fs.writeFileSync(path.join(__dirname,'hud-icon-runtime.json'),JSON.stringify({gameHash,errors,consoleErrors,...hud},null,2));
   if(errors.length||consoleErrors.length)throw Error('HUD runtime error');console.log('HUD whirlwind verified',hud);return;
  }
  for(const [id,def]of Object.entries(shots).filter(([id])=>!process.argv.includes('--shot')||id===process.argv[process.argv.indexOf('--shot')+1])){
   const dir=path.join(root,'src/.tmp/warrior-pressure-wave-v20',training?'training':'field',probe?'probe':'final',id);fs.mkdirSync(dir,{recursive:true});
   const info=await page.evaluate(def=>motionStudy.select(def),{...def,id}),metrics=[];
   for(let frame=0;frame<Math.round(def.seconds*30);frame++){
    const result=await page.evaluate(save=>{const image=motionStudy.next(save),{app,state}=motionStudy,pool=app.effects.warrior,active=pool.layers.filter(l=>l.node.active),crossings=[];for(const h of active.filter(l=>l.key.endsWith(':horizontal'))){const v=active.find(l=>l.key===h.key.replace(/:horizontal$/,':vertical'));if(v){const cc=motionStudy.cc,axis=l=>{const x=cc.Vec3.transformQuat(new cc.Vec3(),cc.Vec3.UNIT_X,l.node.worldRotation);return Math.atan2(cc.Vec3.dot(x,app.camera.node.up),cc.Vec3.dot(x,app.camera.node.right))*180/Math.PI;},d=Math.abs(axis(h)-axis(v))%180;crossings.push(180-Math.min(d,180-d));}}return {image,warrior:pool.inspect(),shield:app.effects.shields.inspect(),crossings,action:state.action?{id:state.action.skillId,elapsed:state.action.elapsed,duration:state.action.duration}:null};},!probe||[0,9,14,18,20,22,25,28,32,36,40,45,50,58,66,78,82].includes(frame));
    result.renderReady=await page.evaluate(()=>motionStudy.app.effects.warrior.layers.filter(l=>l.node.active).map(l=>({key:l.key,subModels:l.renderer.model?.subModels.length??0,bounds:!!l.renderer.model?.worldBounds})));
    if(result.renderReady.some(l=>!l.subModels||!l.bounds))throw Error('Active effect is not submitted to the renderer: '+JSON.stringify(result.renderReady));
    if(result.image)fs.writeFileSync(path.join(dir,String(frame).padStart(3,'0')+'.jpg'),Buffer.from(result.image,'base64'));delete result.image;metrics.push({frame,...result});
    if(process.argv.includes('--diagnose')&&id==='WAR_04'&&frame===25){
     const debug=await page.evaluate(()=>{const {app,cc}=motionStudy,pool=app.effects.warrior,layers=pool.layers.filter(l=>l.node.active&&l.phase==='spin-band'),snap=()=>cc.game.canvas.toDataURL('image/jpeg',.96).split(',')[1];
      const data=layers.map(l=>({key:l.key,enabled:l.renderer.enabled,active:l.node.activeInHierarchy,position:l.node.worldPosition,scale:l.node.worldScale,rotation:l.node.worldRotation,colour:l.renderer.sharedMaterial.getProperty('mainColor'),texture:{width:l.renderer.sharedMaterial.getProperty('mainTexture')?.width,height:l.renderer.sharedMaterial.getProperty('mainTexture')?.height},defines:l.renderer.sharedMaterial.passes[0].defines,positionHead:Array.from(l.renderer.mesh.readAttribute(0,'a_position')??[]).slice(0,12),colourHead:Array.from(l.renderer.mesh.readAttribute(0,'a_color')??[]).slice(0,12)}));
      for(const [i,l]of layers.entries()){const model=l.renderer.model??l.renderer._model,positions=l.renderer.mesh.readAttribute(0,'a_position'),colours=l.renderer.mesh.readAttribute(0,'a_color');data[i].bounds={world:model?.worldBounds,local:model?.modelBounds,enabled:model?.enabled,subModels:model?.subModels?.length};data[i].mesh={struct:l.renderer.mesh.struct,vertexCount:positions?.length,colourMax:colours?Math.max(...Array.from(colours).filter((_,i)=>i%4===3)):0,positionsMiddle:positions?Array.from(positions).slice(900,918):[]};}
      const saved=layers.map(l=>l.renderer.sharedMaterial);for(const l of layers){l.renderer.enabled=true;l.renderer.setSharedMaterial(pool.material(1,false,true),0);}cc.director.tick(0);const wave=snap();
      const first=layers[0],newNode=new cc.Node('DiagnosticNewRenderer');newNode.layer=first.node.layer;pool.root.addChild(newNode);newNode.setWorldPosition(first.node.worldPosition);newNode.setWorldRotation(first.node.worldRotation);newNode.setWorldScale(first.node.worldScale);const renderer=newNode.addComponent(cc.MeshRenderer);renderer.mesh=first.renderer.mesh;renderer.setSharedMaterial(pool.material(1,false,true),0);cc.director.tick(0);const fresh=snap();renderer.mesh=app.world.mesh('cylinder');cc.director.tick(0);const cylinder=snap();newNode.destroy();
      for(const [i,l]of layers.entries()){l.renderer.setSharedMaterial(saved[i],0);saved[i].setProperty('mainColor',new cc.Vec4(1,1,1,1));}cc.director.tick(0);const vector=snap();return {data,wave,vector,fresh,cylinder};});
     for(const name of ['wave','vector','fresh','cylinder']){fs.writeFileSync(path.join(dir,'diagnostic-'+name+'.jpg'),Buffer.from(debug[name],'base64'));delete debug[name];}fs.writeFileSync(path.join(dir,'diagnostic.json'),JSON.stringify(debug,null,2));
    }
   }
   const report=await page.evaluate(()=>motionStudy.report());if(!info.player?.skeletons?.length)throw Error('Native player missing');if(id!=='BASIC_WAR'&&!report.events.some(e=>e.type==='skill_release'))throw Error('Real cast missing '+id);
   fs.writeFileSync(path.join(dir,'capture.json'),JSON.stringify({info,gameHash,errors,consoleErrors,...report,metrics},null,2));
   if(id==='WAR_04'&&new Set(report.events.filter(e=>e.type==='skill_hit').map(e=>e.segment)).size!==3){console.error(JSON.stringify(report));throw Error('Whirlwind real three-segment contacts missing');}
   if(id==='WAR_01'&&report.events.filter(e=>e.type==='skill_hit').length!==2)throw Error('Enlarged reach lost the follow-up cut');
   if(id==='WAR_02'&&new Set(report.events.filter(e=>e.type==='skill_hit').map(e=>e.target)).size!==2)throw Error('Enlarged landing cross missed its outer target');
   if(metrics.some(m=>m.warrior.droppedLayers))throw Error('Warrior effect pool overflow');if(metrics.some(m=>m.crossings.some(a=>Math.abs(a-120)>.03)))throw Error('Cross angle changed');
   fs.writeFileSync(path.join(dir,'capture.json'),JSON.stringify({info,gameHash,errors,consoleErrors,...report,metrics},null,2));console.log('Captured',id,report.frames,'hits',report.events.filter(e=>e.type==='skill_hit').length,'max layers',Math.max(...metrics.map(m=>m.warrior.active.length)));
  }
  const lifecycle=await page.evaluate(async()=>{await motionStudy.select({...{id:'WAR_04',family:'WAR',centre:.15,height:2.9,targets:[[2,0],[-1.1,1.65]],seconds:2.3}});for(let i=0;i<24;i++)motionStudy.next(false);const {app,state}=motionStudy,before=JSON.stringify(state.combat),activeBefore=app.effects.warrior.inspect().active.length;app.effects.clear(true);app.effects.update(app.session);const resumed=app.effects.warrior.inspect(),sameCore=before===JSON.stringify(state.combat);state.action=null;app.effects.update(app.session);const cancelled=app.effects.warrior.inspect().active.length;app.effects.clear();return {activeBefore,activeResumed:resumed.active.length,sameCore,cancelled,cleared:app.effects.warrior.inspect().active.length};});
  if(!lifecycle.sameCore||!lifecycle.activeBefore||!lifecycle.activeResumed||lifecycle.cancelled||lifecycle.cleared)throw Error('Whirlwind lifecycle failed');
  fs.writeFileSync(path.join(__dirname,'runtime-lifecycle-'+(training?'training':'field')+'.json'),JSON.stringify(lifecycle,null,2));fs.writeFileSync(path.join(__dirname,'runtime-log-'+(training?'training':'field')+'.json'),JSON.stringify({gameHash,errors,consoleErrors},null,2));
  if(errors.length||consoleErrors.length)throw Error('Game console errors');
  await page.setViewportSize({width:844,height:390});await page.evaluate(async()=>{const {app,cc}=motionStudy;cc.view.setFrameSize(844,390);app.hud.root.active=true;app.enabled=true;cc.game.resume();});await page.waitForTimeout(300);await page.screenshot({path:path.join(__dirname,'runtime-hud-'+(training?'training':'field')+'-844.png')});await page.evaluate(()=>{motionStudy.app.enabled=false;motionStudy.cc.game.pause();});
 }finally{await browser.close();}
}
run().catch(e=>{console.error(e);process.exitCode=1;}).finally(()=>server.close());
