// One native production timing recording. No preview, effect, profile or damage overrides.
const fs=require('node:fs'),path=require('node:path'),http=require('node:http'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'../../..'),build=path.join(root,'src/cocos/build/concept-2d');
const variant=process.argv.includes('--after')?'after':'before',out=path.join(root,'src/.tmp/warrior-crescent-ground-clearance-v43',variant);fs.mkdirSync(out,{recursive:true});
const {chromium}=require(path.join(root,'src/cocos/node_modules/playwright'));
const main=path.join(build,'assets/main',fs.readdirSync(path.join(build,'assets/main')).find(n=>/^index\..+\.js$/.test(n))),gameHash=crypto.createHash('sha256').update(fs.readFileSync(main)).digest('hex');
const server=http.createServer((req,res)=>{const p=decodeURIComponent(new URL(req.url,'http://localhost').pathname),file=path.resolve(build,'.'+(p==='/'?'/index.html':p));if(!file.startsWith(build+path.sep)||!fs.existsSync(file)||!fs.statSync(file).isFile())return res.writeHead(404).end();const mime={'.js':'text/javascript','.json':'application/json','.html':'text/html','.wasm':'application/wasm','.css':'text/css','.png':'image/png','.jpg':'image/jpeg'}[path.extname(file)];if(mime)res.setHeader('Content-Type',mime);fs.createReadStream(file).pipe(res);});
async function run(){
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 const browser=await chromium.launch({headless:true,args:['--enable-webgl','--use-angle=d3d11','--ignore-gpu-blocklist','--mute-audio','--disable-background-timer-throttling','--disable-renderer-backgrounding']});
 try{
  const page=await browser.newPage({viewport:{width:480,height:235},deviceScaleFactor:1}),errors=[];
  page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
  await page.goto('http://127.0.0.1:'+server.address().port+'/?view=2d&player=3d');
  await page.waitForFunction(()=>globalThis.System,undefined,{timeout:45000});
  await page.evaluate(()=>{globalThis.findChapter=async()=>{const cc=await System.import('cc');function find(n){return n?.getComponent('ChapterGame')||n?.children.map(find).find(Boolean);}return {app:find(cc.director.getScene()),cc};};});
  const deadline=Date.now()+180000;
  while(true){const ready=await page.evaluate(async()=>{const {app,cc}=await findChapter();if(app?.session&&app?.actors&&app.loading){cc.game.resume();cc.director.tick(1/60);}return !!(app?.session&&app.actors&&!app.loading&&app.platform.auth.ready);});if(ready)break;if(Date.now()>deadline)throw Error('Startup timed out');await new Promise(r=>setTimeout(r,250));}
  await page.setViewportSize({width:1280,height:624});
  const setup=await page.evaluate(async()=>{
   const {app,cc}=await findChapter(),{getArea}=await System.import('chunks:///_virtual/WorldData.ts');
   cc.view.resizeWithBrowserSize(true);cc.view.setFrameSize(1280,624);cc.game.resume();app.enabled=false;app.clearInput(false);
   app.session.enter(getArea('S01-T1'),{x:0,z:-7});await app.rebuild();app.enabled=false;
   const session=app.session,state=session.state,p=state.player;
   state.time=10;state.sequence=100;state.seed=73014;state.action=null;state.dialogue=null;state.dice.active=false;state.status='playing';state.enemies=[];state.cooldowns={};state.combat.cooldowns={};state.progression.learned.WAR_01=1;
   session.resetCombatTransient();session.applyCombatLoadout('WAR','W01');p.x=0;p.z=-7;p.hp=p.maxHp;p.focus=p.maxFocus;
   app.menu='';app.hud.clearModal();app.hud.root.active=false;
   await app.effects.prepareEquipment(session);await app.actors.preparePlayerWeapon?.('W01');
   const angle=Math.atan2(app.camera.node.right.x,app.camera.node.right.z)+.67;p.angle=angle;
   app.actors.update(session,0,false,false);app.positionCamera(1);
   const focus=new cc.Vec3(p.x+Math.sin(angle)*1.3,app.world.height(p)+.63,p.z+Math.cos(angle)*1.3);
   app.camera.node.setWorldPosition(focus.clone().subtract(app.camera.node.forward.clone().multiplyScalar(28)));app.camera.orthoHeight=4.6;app.camera.camera?.update(true);app.flatWorld?.update(app.camera,session);
   globalThis.gapStudy={app,cc,state,session,angle,events:[]};cc.director.tick(0);cc.game.pause();
   return {area:state.area,skill:'WAR_01',rank:state.progression.learned.WAR_01,player:[p.x,app.world.height(p),p.z],angle};
  });
  const metrics=[];
  for(let frame=0;frame<48;frame++){
   const result=await page.evaluate(frame=>{
    const {app,cc,state,session,angle,events}=gapStudy;cc.game.resume();
    const process=batch=>{for(const e of batch)if(e.type.startsWith('skill_'))events.push({type:e.type,segment:e.segment,time:state.time,value:e.value});app.process(batch);};
    if(frame===9)process(session.castSkill('WAR_01',{x:state.player.x+Math.sin(angle)*3.9,z:state.player.z+Math.cos(angle)*3.9},angle));
    for(let j=0;j<2;j++){process(session.advance(1/60,{x:0,z:0,aim:angle}));app.actors.update(session,1/60,false,false);app.effects.update(session);cc.director.tick(1/60);}
    app.flatWorld?.update(app.camera,session);
    const layers=app.effects.warrior.layers.filter(l=>l.node.active&&l.phase==='crescent-wave'),summary=[];
    for(const layer of layers){const positions=layer.renderer.mesh.readAttribute(0,'a_position'),uv=layer.renderer.mesh.readAttribute(0,'a_texCoord'),flow=layer.renderer.sharedMaterial.getProperty('flowState');let min=Infinity,below=0,count=0;
     for(let i=0;i<uv.length/2;i++){const u=uv[2*i],v=uv[2*i+1];if(u<.06||u>.94||v<.08||v>.24)continue;const rear=v*v,shrink=1-rear*flow.y*.12,q=new cc.Vec3(positions[3*i]*shrink,positions[3*i+1]+Math.sin(u*10-flow.x*3)*rear*.018*flow.z,positions[3*i+2]*shrink);cc.Vec3.transformMat4(q,q,layer.node.worldMatrix);const clearance=q.y-app.world.height({x:q.x,z:q.z});min=Math.min(min,clearance);if(clearance<0)below++;count++;}
     summary.push({key:layer.key,position:[layer.node.worldPosition.x,layer.node.worldPosition.y,layer.node.worldPosition.z],minimumCrestClearance:min,belowGroundVertices:below,crestVertices:count,dissolve:flow.y,renderReady:!!layer.renderer.model?.subModels?.length});
    }
    const image=cc.game.canvas.toDataURL('image/jpeg',.96).split(',')[1];cc.game.pause();return {image,time:state.time,layers:summary};
   },frame);
   fs.writeFileSync(path.join(out,String(frame).padStart(3,'0')+'.jpg'),Buffer.from(result.image,'base64'));delete result.image;metrics.push({frame,...result});
  }
  const young=metrics.flatMap(f=>f.layers.filter(l=>l.dissolve<.35));if(!young.length)throw Error('No rendered skill crescent');
  const minimumClearance=Math.min(...young.map(l=>l.minimumCrestClearance)),clippedFrames=metrics.filter(f=>f.layers.some(l=>l.belowGroundVertices>0)).length;
  const events=await page.evaluate(()=>gapStudy.events),report={gameHash,variant,setup,minimumClearance,clippedFrames,errors,events,metrics};
  fs.writeFileSync(path.join(out,'capture.json'),JSON.stringify(report,null,2));
  if(errors.length||young.some(l=>!l.renderReady))throw Error('Rendering error');
  if(variant==='after'&&minimumClearance<.015)throw Error('Visible crest still intersects the floor');
  console.log(JSON.stringify({gameHash,variant,setup,minimumClearance,clippedFrames,events:events.map(e=>[e.type,e.segment])}));
 }finally{await browser.close();server.close();}
}
run().catch(e=>{console.error(e);process.exitCode=1;server.close();});
