/* Correctness gate for optimized movement and painted-world camera framing. */
const {chromium}=require('playwright');
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const args=process.argv.slice(2),arg=(k,d)=>{const i=args.indexOf(`--${k}`);return i<0?d:args[i+1];};
const backend=arg('backend','desktop');if(!['desktop','android'].includes(backend))throw Error('Unknown correctness backend');
const output=path.resolve(arg('out',path.join(__dirname,'../../test-results/performance/world-qa')));fs.mkdirSync(output,{recursive:true});
if(fs.existsSync(path.join(output,'report.json')))throw Error('Refusing to overwrite a correctness report');
const urls=[arg('reference'),arg('url','http://127.0.0.1:7496/')].filter(Boolean);
const reports=[];
(async()=>{
 const browser=backend==='desktop'?await chromium.launch({executablePath:process.env.CHROME_PATH||'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true}):null;let androidSession;
 try{for(const [index,url]of urls.entries()){
  if(backend==='android')androidSession=await require('./android.cjs').openAndroid(arg('serial','emulator-5556'),new URL(url));
  const context=androidSession?.context??await browser.newContext({viewport:{width:844,height:390},deviceScaleFactor:3,isMobile:true,hasTouch:true}),page=await context.newPage(),errors=[];
  if(androidSession)for(const old of context.pages().filter(p=>p!==page))await old.close();
  page.on('pageerror',e=>errors.push(e.message));
  await page.goto(`${url}?view=2d&player=3d&progression=natural`);
  if(androidSession){const cdp=await context.newCDPSession(page),full=await cdp.send('Runtime.evaluate',{expression:'document.documentElement.requestFullscreen()',userGesture:true,awaitPromise:true});if(full.exceptionDetails)throw Error('Native correctness fullscreen failed');await cdp.detach();}
  await page.waitForFunction(()=>!!globalThis.System);
  await page.evaluate(async()=>{const cc=await System.import('cc');globalThis.__qaApp=()=>cc.director.getScene()?.getChildByName('ChapterGame')?.getComponent('ChapterGame');});
  await page.waitForFunction(()=>!!__qaApp()?.actors&&!__qaApp().loading&&!__qaApp().failure,null,{timeout:120000});
  if(androidSession)await androidSession.nativeUi(true);
  await page.evaluate(require('./page-driver.cjs'));
  const rows=[];
  for(const area of args.includes('--animation-only')?[]:['U1-06','S13','S02','S01-T1','H03']){
   await page.evaluate(area=>__perf.setup({area,mode:'idle',family:'BOW'}),area);
   const data=await page.evaluate(async()=>{
    const {app,cc}=__perf;app.enabled=false;__perf.current=null;const w=app.world;
    const {prepareCombatLoadout}=await System.import('chunks:///_virtual/CombatLoadouts.ts');
    // This reference is the pre-optimization movement implementation. Compare
    // against actual BoxCollider world positions, not the navigation metadata.
    const original=(from,delta,radius)=>{const distance=Math.hypot(delta.x,delta.z),steps=Math.max(1,Math.ceil(distance/.15)),p={...from};const blocked=(x,z)=>Math.abs(x)>w.area.width/2-radius||Math.abs(z)>w.area.depth/2-radius||w.colliders.some(c=>{const v=c.node.worldPosition,s=c.size;return Math.abs(x-v.x)<s.x/2+radius&&Math.abs(z-v.z)<s.z/2+radius;});for(let i=0;i<steps;i++){const x=p.x+delta.x/steps,z=p.z+delta.z/steps;if(!blocked(x,p.z))p.x=x;if(!blocked(p.x,z))p.z=z;}return p;};
    let seed=19,cases=0;const random=()=>((seed=seed*16807%2147483647)/2147483647);let maxDelta=0;
    const check=(p,d,r)=>{const a=original(p,d,r),b=w.move(p,d,r);maxDelta=Math.max(maxDelta,Math.abs(a.x-b.x),Math.abs(a.z-b.z));cases++;};
    for(let i=0;i<3000;i++)check({x:(random()-.5)*w.area.width,z:(random()-.5)*w.area.depth},{x:(random()-.5)*3,z:(random()-.5)*3},[.32,.42,.8][i%3]);
    for(const c of w.colliders){const p=c.node.worldPosition,s=c.size;for(const sign of [-1,1])for(const epsilon of [-1e-8,0,1e-8])check({x:p.x+sign*(s.x/2+.32+epsilon),z:p.z},{x:-sign*.2,z:.2},.32);}
    // A late authored obstacle must invalidate the lazy movement snapshot.
    w.obstacle({kind:'performance-qa',x:w.area.spawn.x+1,z:w.area.spawn.z,width:1,depth:1,height:2});
    check(w.area.spawn,{x:1,z:0},.32);
    const originalVisible=(from,to)=>{const startY=w.height(from)+.9,endY=w.height(to)+(typeof to.actor==='string'?1.65:.9),d=new cc.Vec3(to.x-from.x,endY-startY,to.z-from.z),length=d.length();if(length<.001)return true;d.normalize();return !cc.PhysicsSystem.instance.raycastClosest(new cc.geometry.Ray(from.x,startY,from.z,d.x,d.y,d.z),2,length,false);};
    let visibilityCases=0,visibilityMismatches=0;
    for(let i=0;i<600;i++){
     const a={x:(random()-.5)*w.area.width,z:(random()-.5)*w.area.depth},b={x:(random()-.5)*w.area.width,z:(random()-.5)*w.area.depth,...(i%2?{actor:'qa-npc'}:{})};
     if(originalVisible(a,b)!==w.visible(a,b))visibilityMismatches++;visibilityCases++;
     if(originalVisible(a,a)!==w.visible(a,a))visibilityMismatches++;visibilityCases++;
    }
    const camera=[];
    for(const family of ['WAR','BOW','FIR','THU'])for(const zoom of [4.4,8,12]){
     const s=app.session.state;s.equipment.weapon=family==='WAR'?'W01':family==='BOW'?'W07':'W11';prepareCombatLoadout(s.combat,s.equipment.weapon,s.progression,family);
     for(const p of [w.area.spawn,{x:0,z:9},{x:4,z:12}])for(const aiming of [null,'combat0','ultimate']){
      Object.assign(s.player,p);app.manualCameraHeight=zoom;
      app.aiming=aiming;app.aimTarget={x:p.x+5,z:p.z+3};app.combatFocus={target:app.aimTarget,skillId:s.combat.activeSlots[0],rank:1,until:s.time+10};app.positionCamera(1);
      camera.push({family,zoom,aiming,p:{...p},position:{x:app.camera.node.position.x,y:app.camera.node.position.y,z:app.camera.node.position.z},height:app.camera.orthoHeight,rotation:{x:app.camera.node.rotation.x,y:app.camera.node.rotation.y,z:app.camera.node.rotation.z,w:app.camera.node.rotation.w}});
     }
    }
    app.actors.update(app.session,0,false,true);app.hud.update(app.session,app.camera,'','','');
    const mini=app.hud.miniMap,fog=mini.fog.getComponent(cc.Graphics),fogChecks={cases:0,mismatches:0,activationChanges:0,readoutTextChanges:0};
    {
     const {LocalCartography:Chart}=await System.import('chunks:///_virtual/LocalCartography.ts');
     const geometry=()=>{let hash=2166136261,vertices=0,indices=0;for(const d of fog.impl.getRenderDataList()){vertices+=d.vertexStart;indices+=d.indexStart;for(const bytes of [new Uint8Array(d.vData.buffer,d.vData.byteOffset,d.vertexStart*d.stride),new Uint8Array(d.iData.buffer,d.iData.byteOffset,d.indexStart*2)])for(const byte of bytes)hash=Math.imul(hash^byte,16777619);}return [hash>>>0,vertices,indices].join(':');};
     for(const p of [w.area.spawn,{x:w.area.spawn.x+3,z:w.area.spawn.z+3},{x:0,z:0}]){
      Object.assign(app.session.state.player,p);Chart.track(app.session);fog.clear();Chart.drawFog(fog,w.area,mini.scale,0,0,app.session,.25);const native=geometry();
      fog.clear();
      Chart.drawFog(fog,w.area,mini.scale,0,0,app.session,.25);if(geometry()!==native)fogChecks.mismatches++;fogChecks.cases++;
     }
     mini.drawPins(app.session); // Settle the final fixture position before testing stable redraws.
     const descriptor=Object.getOwnPropertyDescriptor(cc.Label.prototype,'string');
     const readoutLabels=[mini.exitName,mini.exitDistance].filter(Boolean),readoutNodes=[mini.exitReadout,mini.taskReadout].filter(Boolean);
     for(const label of readoutLabels)Object.defineProperty(label,'string',{configurable:true,get:descriptor.get,set(value){if(descriptor.get.call(this)!==value)fogChecks.readoutTextChanges++;descriptor.set.call(this,value);}});
     const changed=()=>fogChecks.activationChanges++,event=cc.Node.EventType.ACTIVE_IN_HIERARCHY_CHANGED;
     for(const n of readoutNodes)n.on(event,changed);mini.drawPins(app.session);mini.drawPins(app.session);for(const n of readoutNodes)n.off(event,changed);
     for(const label of readoutLabels)delete label.string;
    }
    const meshes=new Set(cc.director.getScene().getComponentsInChildren(cc.MeshRenderer).map(r=>r.mesh).filter(Boolean));let meshPrimitives=0,meshIndexMismatches=0;
    for(const mesh of meshes)for(let sub=0;sub<mesh.struct.primitives.length;sub++){
     const primitive=mesh.struct.primitives[sub],indices=mesh.readIndices(sub);if(!indices)continue;
     const count=Math.min(...primitive.vertexBundelIndices.map(i=>mesh.struct.vertexBundles[i].view.count));
     for(const index of indices)if(index>=count)meshIndexMismatches++;meshPrimitives++;
    }
    return {area:w.area.id,cases,maxDelta,visibilityCases,visibilityMismatches,camera,fogChecks,meshPrimitives,meshIndexMismatches,warmupNodes:w.root.children.filter(n=>n.name.includes('ShaderWarmup')).length};
   });
   assert.equal(data.maxDelta,0,`collision changed in ${area}`);assert.equal(data.visibilityMismatches,0,`visibility changed in ${area}`);assert.equal(data.warmupNodes,0,`loading shader warmup leaked nodes in ${area}`);assert.equal(data.meshIndexMismatches,0,`mesh index exceeds vertex buffer in ${area}`);
   if(index===urls.length-1){assert.equal(data.fogChecks.mismatches,0,`fog geometry changed in ${area}`);assert.equal(data.fogChecks.activationChanges,0,`stable minimap readouts toggle active state in ${area}`);assert.equal(data.fogChecks.readoutTextChanges,0,`stable minimap readouts rewrite different text in ${area}`);}rows.push(data);
   await page.screenshot({path:path.join(output,`${index}-${area}.png`)});
   await page.evaluate(()=>__perf.app.enabled=true);
  }
  let animation;if(args.includes('--animation')||args.includes('--animation-only')){await page.evaluate(()=>__perf.setup({area:'H12',mode:'idle',family:'BOW'}));animation=await page.evaluate(require('./animation-qa.cjs'),{requireMasked:index===urls.length-1});}
  let native;if(androidSession){await androidSession.nativeUi();const graphics=await androidSession.graphicsLog();assert.deepEqual(graphics.errors,[]);native={environment:androidSession.environment,graphicsErrors:graphics.errors};fs.writeFileSync(path.join(output,`${index}-android-chromium.log`),graphics.log);}
  assert.deepEqual(errors,[]);reports.push({url,rows,errors,animation,native});if(androidSession){await androidSession.close();androidSession=null;}else await context.close();
 }}finally{await androidSession?.close();await browser?.close();}
 if(reports.length===2){const a=reports[0].rows,b=reports[1].rows;for(let i=0;i<a.length;i++)assert.deepEqual(b[i].camera,a[i].camera,`camera changed in ${a[i].area}`);}
 fs.writeFileSync(path.join(output,'report.json'),JSON.stringify({status:'passed',reports},null,2));console.log(`PASS: ${backend} correctness; ${reports.reduce((n,r)=>n+r.rows.reduce((n,a)=>n+a.cases,0),0)} collision cases; ${reports.reduce((n,r)=>n+(r.animation?.samples??0),0)} animation poses`);
})().catch(e=>{fs.writeFileSync(path.join(output,'report.json'),JSON.stringify({status:'failed',error:e.stack,reports},null,2));console.error(e);process.exitCode=1;});
