// Actual Cocos carry transitions and screenshots, using an isolated local profile.
const {chromium}=require('../../../src/cocos/node_modules/playwright');
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const out=path.join(__dirname,'runtime');fs.mkdirSync(out,{recursive:true});
(async()=>{const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true,args:['--enable-unsafe-swiftshader']});try{
 const page=await browser.newPage({viewport:{width:1440,height:900}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('http://127.0.0.1:7469/?view=2d&player=3d&test=max&revision=back-design-v1');await page.waitForFunction(()=>globalThis.System);
 await page.evaluate(async()=>{globalThis.cc=await System.import('cc');globalThis.app=()=>cc.director.getScene()?.getChildByName('ChapterGame')?.getComponent('ChapterGame');});
 await page.waitForFunction(()=>app()?.actors&&!app().loading||app()?.failure,undefined,{timeout:90000});
 assert.equal(await page.evaluate(()=>app().failure),'');
 await page.evaluate(()=>{
  const a=app();a.enabled=false;a.menu='';a.hud.root.active=false;a.manualCameraHeight=2;a.positionCamera(1);
  globalThis.heading=d=>{const r=a.camera.node.right,u=a.camera.node.up,t=d*Math.PI/180,k=u.x*u.x+u.z*u.z;return Math.atan2(r.x*Math.sin(t)+u.x*Math.cos(t)/k,r.z*Math.sin(t)+u.z*Math.cos(t)/k);};
  globalThis.step=(d=0,input={},dt=1/30)=>{
   a.process(a.session.advance(dt,{x:0,z:0,aim:heading(d),...input}));const length=Math.hypot(input.x??0,input.z??0);
   a.actors.update(a.session,dt,length>0,false,length||1);
   const p=a.actors.player.active.get('player'),action=a.session.state.action,clip=p.clips[p.state],animation=clip&&p.animation.getState(clip.name);
   // Drive native clips with the same simulation clock for a deterministic
   // recording. Fast-forwarding only game rules would leave a real-time dodge
   // or cross-fade in the next weapon's stills.
   if(animation){const speed=animation.speed;p.qaClock=p.qaState===p.state?(p.qaClock??0)+dt*speed:0;p.qaState=p.state;
    p.animation.pause();animation.time=action?Math.min(1,action.elapsed/action.duration)*clip.duration:p.qaClock%clip.duration;animation.sample();}
   a.world.presentation?.update(a.session);a.effects.update(a.session);a.positionCamera(dt);a.flatWorld.update(a.camera,a.session);
  };
  globalThis.prepare=id=>{a.session.cancelInput();for(let i=0;i<150;i++)step();a.effects.clear();a.session.state.inventory[id]=1;if(!a.session.equip(id))throw Error('Cannot equip '+id);step();};
  globalThis.carryInfo=()=>{
   const p=a.actors.player.active.get('player'),id=a.session.state.equipment.weapon,kind=id==='L01'?'greatsword':'sword',binding=p.swordCarry?.grips[kind],n=p.weapons[kind];
   const expected=binding?.stowed?(binding.items[id]?.position??binding.backPosition):binding?.handPosition;
   const hand=binding&&cc.Vec3.transformMat4(new cc.Vec3(),binding.handPosition,binding.handParent.worldMatrix),source=a.actors.player.playerPresentation()?.hand;
   return {id,time:a.session.state.time,pose:p.state,action:a.session.state.action?.kind,stowed:binding?.stowed,node:n?.uuid,parent:n?.parent?.name,visibleSwordRoots:['sword','greatsword'].filter(k=>p.weapons[k]?.activeInHierarchy),heldVisible:binding?.heldModels.activeInHierarchy,backVisible:binding?.backModels.activeInHierarchy,mountError:expected&&cc.Vec3.distance(n.position,expected),handEmitterError:hand&&source?cc.Vec3.distance(hand,source):null,ready:a.actors.player.carryReadiness.ready};
  };
 });
 const stills=[],frames=[],transitions=[];
 async function capture(id,phase,index){await page.waitForTimeout(22);const name=`${id}-${String(index).padStart(4,'0')}.jpg`;await page.screenshot({path:path.join(out,name),type:'jpeg',quality:93,clip:{x:300,y:40,width:800,height:760}});const info=await page.evaluate(()=>carryInfo());assert.equal(info.visibleSwordRoots.length,1);assert.ok(info.mountError<1e-6);assert.ok(info.handEmitterError<1e-6);frames.push({id,phase,index,file:name,...info});return info;}
 for(const id of ['W01','W02','L01']){
  await page.evaluate(id=>prepare(id),id);const first=await page.evaluate(()=>carryInfo());assert.equal(first.stowed,true);
  for(const d of [0,45,90,135,180,225,270,315]){
   await page.evaluate(d=>{for(let i=0;i<3;i++)step(d);},d);await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));const file=`${id}-stowed-${d}.jpg`;await page.screenshot({path:path.join(out,file),type:'jpeg',quality:94,clip:{x:300,y:40,width:800,height:760}});stills.push({id,degrees:d,file,...await page.evaluate(()=>carryInfo())});
  }
  let index=0;
  for(let i=0;i<36;i++){await page.evaluate(d=>step(d),i*10);assert.equal((await capture(id,'turn',index++)).stowed,true);}
  for(let i=0;i<18;i++){await page.evaluate(()=>{const angle=heading(0);step(0,{x:Math.sin(angle),z:Math.cos(angle)});});assert.equal((await capture(id,'run',index++)).stowed,true);}
  for(let i=0;i<4;i++){await page.evaluate(()=>step());await capture(id,'idle',index++);}
  for(let i=0;i<29;i++){await page.evaluate(attack=>step(0,{attack}),i===0);const info=await capture(id,'attack',index++);assert.equal(info.stowed,false);}
  for(let i=0;i<55;i++){await page.evaluate(()=>step());await capture(id,'settle',index++);}
  const last=await page.evaluate(()=>carryInfo());assert.equal(last.stowed,true);assert.equal(last.node,first.node);transitions.push({id,start:first,end:last});
  await page.evaluate(()=>step(0,{dash:true}));assert.equal((await page.evaluate(()=>carryInfo())).stowed,true);await page.evaluate(()=>{for(let i=0;i<30;i++)step();});
  console.log('Recorded '+id+' back / hand / back');
 }
 // An out-of-combat inventory swap must immediately use the correct back item.
 const pausedSwap=await page.evaluate(()=>{const a=app();if(!a.session.equip('W02'))throw Error('paused equip');a.actors.update(a.session,0,false,true);return carryInfo();});assert.equal(pausedSwap.stowed,true);assert.equal(pausedSwap.visibleSwordRoots.length,1);
 await page.evaluate(()=>{const a=app();a.menu='inventory';a.modalKey='';a.hud.root.active=true;a.renderModal();});await page.waitForTimeout(80);
 await page.screenshot({path:path.join(out,'inventory-front.jpg'),type:'jpeg',quality:93});
 const preview=await page.evaluate(()=>{const stage=cc.director.getScene().getChildByName('CharacterPreviewStage'),model=stage.children[0],cam=cc.director.getScene().getChildByName('CharacterPreviewCamera').getComponent(cc.Camera);model.setRotationFromEuler(0,180,0);cam.node.setPosition(stage.position.x,1.03,stage.position.z+5);cam.node.lookAt(new cc.Vec3(stage.position.x,1.03,stage.position.z));return {skins:stage.getComponentsInChildren(cc.SkinnedMeshRenderer).length};});
 await page.waitForTimeout(70);await page.screenshot({path:path.join(out,'inventory-back.jpg'),type:'jpeg',quality:93});
 fs.writeFileSync(path.join(out,'report.json'),JSON.stringify({stills,frames,transitions,pausedSwap,preview,errors},null,2));assert.deepEqual(errors,[]);console.log(JSON.stringify({stills:stills.length,frames:frames.length,preview,errors}));
 // Default 2D is checked in a separate isolated browser by flat-regression.cjs.
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
