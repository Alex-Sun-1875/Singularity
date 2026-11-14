// Isolated manual recording through the real Cocos game/renderer.
const {chromium}=require('../../../src/cocos/node_modules/playwright');
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const ids=JSON.parse(fs.readFileSync(path.join(__dirname,'designs.json'),'utf8')).map(r=>r.id);
const out=path.join(__dirname,'runtime');fs.mkdirSync(out,{recursive:true});
const selected=process.argv.includes('--ids')?process.argv[process.argv.indexOf('--ids')+1].split(','):ids;

(async()=>{const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true,args:['--enable-unsafe-swiftshader']});try{
 const page=await browser.newPage({viewport:{width:1440,height:900}}),errors=[],requests=[];page.on('pageerror',e=>errors.push(e.message));page.on('requestfailed',r=>requests.push(r.url()));
 await page.goto((process.env.WEAPONS_REVIEW_URL??'http://127.0.0.1:7469/')+'?view=2d&player=3d&test=max&revision=weapons-design-1');await page.waitForFunction(()=>globalThis.System);
 await page.evaluate(async()=>{globalThis.cc=await System.import('cc');globalThis.app=()=>cc.director.getScene()?.getChildByName('ChapterGame')?.getComponent('ChapterGame');});
 await page.waitForFunction(()=>app()?.actors&&!app().loading||app()?.failure,undefined,{timeout:120000});
 assert.equal(await page.evaluate(()=>app().failure),'');
 await page.evaluate(()=>{
  const a=app();a.enabled=false;a.menu='';a.hud.root.active=false;a.manualCameraHeight=2.4;a.positionCamera(1);
  globalThis.heading=d=>{const r=a.camera.node.right,u=a.camera.node.up,t=d*Math.PI/180,k=u.x*u.x+u.z*u.z;return Math.atan2(r.x*Math.sin(t)+u.x*Math.cos(t)/k,r.z*Math.sin(t)+u.z*Math.cos(t)/k);};
  globalThis.step=(d=0,input={},dt=1/30)=>{
   a.process(a.session.advance(dt,{x:0,z:0,aim:heading(d),...input}));const speed=Math.hypot(input.x??0,input.z??0);a.actors.update(a.session,dt,speed>0,false,speed||1);
   const p=a.actors.player.active.get('player'),action=a.session.state.action,clip=p.clips[p.state],anim=clip&&p.animation.getState(clip.name);
   if(anim){const nativeSpeed=anim.speed;p.qaClock=p.qaState===p.state?(p.qaClock??0)+dt*nativeSpeed:0;p.qaState=p.state;p.animation.pause();
    if(p.state!=='attack_bow'&&action)anim.time=Math.min(1,action.elapsed/action.duration)*clip.duration;
    else if(!p.state.startsWith('attack_bow')&&!action)anim.time=p.qaClock%clip.duration;
    // The existing actor already samples the exact native bow draw/release.
    anim.sample();
   }
   a.world.presentation?.update(a.session);a.effects.update(a.session);a.positionCamera(dt);a.flatWorld.update(a.camera,a.session);
  };
  globalThis.prepare=id=>{a.session.cancelInput();for(let i=0;i<155;i++)step();a.effects.clear();a.session.state.inventory[id]=1;if(!a.session.equip(id))throw Error('equip '+id);for(let i=0;i<4;i++)step();};
  globalThis.info=()=>{
   const p=a.actors.player.active.get('player'),id=p.renderedWeaponId,kind=id==='L01'?'greatsword':id.startsWith('W')&&Number(id.slice(1))>=7&&Number(id.slice(1))<=10||['DU2-04','DE02','L02'].includes(id)?'bow':['W11','W12','W13','W14','DR2-03','DU1-04'].includes(id)?'staff':'sword',b=p.swordCarry.grips[kind];
   const visible=Object.entries(p.weapons).filter(([k,n])=>k!=='arrow'&&n.activeInHierarchy).map(([k,n])=>k);
   const variants=Object.values(p.weapons).flatMap(n=>n.getComponentsInChildren(cc.MeshRenderer)).filter(r=>r.node.activeInHierarchy).map(r=>({node:r.node.name,mesh:r.mesh?.uuid,shapes:r.mesh?.struct.morph?.targetNames??[]}));
   const expected=b.stowed?(b.items[id]?.position??b.backPosition):b.handPosition;
   return {id,kind,pose:p.state,action:a.session.state.action?.kind,stowed:b.stowed,visible,variants,mountError:cc.Vec3.distance(b.node.position,expected),quiver:!!p.swordCarry.quiver.node.activeInHierarchy,camera:a.camera.orthoHeight,held:b.heldModels.activeInHierarchy,back:b.backModels.activeInHierarchy,gripPosition:{...b.node.position}};
  };
 });
 const stills=[],frames=[],transitions=[];
 async function record(file,id,phase,index){await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(resolve)));await page.screenshot({path:path.join(out,file),type:'jpeg',quality:94,clip:{x:270,y:30,width:900,height:820}});const data=await page.evaluate(()=>info());assert.equal(data.visible.length,1);assert.ok(data.variants.length>0);assert.ok(data.mountError<1e-6);if(data.kind==='bow')assert.equal(data.quiver,true);else assert.equal(data.quiver,false);return {id,phase,index,file,...data};}
 for(const id of selected){
  await page.evaluate(id=>prepare(id),id);assert.equal((await page.evaluate(()=>info())).stowed,true);
  for(const d of [0,90,180,270]){
   await page.evaluate(d=>{for(let i=0;i<3;i++)step(d);},d);
   stills.push(await record(`${id}-stowed-${d}.jpg`,id,'stowed',d));
  }
  const bow=(await page.evaluate(()=>info())).kind==='bow';let index=0;
  // All 24 weapons get a full authored attack and recovery, at a diagonal angle.
  for(let i=0;i<58;i++){
   await page.evaluate(({attack})=>step(45,{attack}),{attack:bow?i<30:i===4});
   frames.push(await record(`${id}-${String(index).padStart(4,'0')}.jpg`,id,bow?(i<30?'draw':'release'):'attack',index++));
  }
  // End with the real readiness timer returning the weapon to its back mount.
  for(let i=0;i<90;i++)await page.evaluate(()=>step(45));
  const end=await page.evaluate(()=>info());assert.equal(end.stowed,true);transitions.push(end);
  console.log('Reviewed '+id+' held / attack / stowed');
 }
 if(process.argv.includes('--merge')){const previous=JSON.parse(fs.readFileSync(path.join(out,'report.json'),'utf8'));stills.push(...previous.stills.filter(x=>!selected.includes(x.id)));frames.push(...previous.frames.filter(x=>!selected.includes(x.id)));transitions.push(...previous.transitions.filter(x=>!selected.includes(x.id)));}
 const result={source:'Actual final Cocos build; local isolated test profile',ids,stills,frames,transitions,errors,requests};fs.writeFileSync(path.join(out,'report.json'),JSON.stringify(result,null,2));assert.deepEqual(errors,[]);console.log(JSON.stringify({stills:stills.length,frames:frames.length,errors,requests}));
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
