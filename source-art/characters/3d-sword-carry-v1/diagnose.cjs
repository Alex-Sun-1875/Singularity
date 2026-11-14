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
   if(p.state==='attack_sword'&&action&&animation){animation.speed=0;animation.time=Math.min(1,action.elapsed/action.duration)*clip.duration;animation.sample();}
   a.effects.update(a.session);a.positionCamera(dt);a.flatWorld.update(a.camera,a.session);
  };
  globalThis.prepare=id=>{a.session.cancelInput();for(let i=0;i<150;i++)step();a.effects.clear();a.session.state.inventory[id]=1;if(!a.session.equip(id))throw Error('Cannot equip '+id);step();};
  globalThis.carryInfo=()=>{
   const p=a.actors.player.active.get('player'),id=a.session.state.equipment.weapon,kind=id==='L01'?'greatsword':'sword',binding=p.swordCarry?.grips[kind],n=p.weapons[kind];
   const expected=binding?.stowed?(binding.items[id]?.position??binding.backPosition):binding?.handPosition;
   const hand=binding&&cc.Vec3.transformMat4(new cc.Vec3(),binding.handPosition,binding.handParent.worldMatrix),source=a.actors.player.playerPresentation()?.hand;
   return {id,time:a.session.state.time,pose:p.state,action:a.session.state.action?.kind,stowed:binding?.stowed,node:n?.uuid,parent:n?.parent?.name,visibleSwordRoots:['sword','greatsword'].filter(k=>p.weapons[k]?.activeInHierarchy),heldVisible:binding?.heldModels.activeInHierarchy,backVisible:binding?.backModels.activeInHierarchy,mountError:expected&&cc.Vec3.distance(n.position,expected),handEmitterError:hand&&source?cc.Vec3.distance(hand,source):null,ready:a.actors.player.carryReadiness.ready};
  };
 });

 const rows=[];
 for(const id of ['W01','W02','L01']){
  await page.evaluate(id=>prepare(id),id);await page.waitForTimeout(90);
  rows.push(await page.evaluate(()=>{const p=app().actors.player.active.get('player'),b=p.swordCarry.grips[p.renderedWeaponId==='L01'?'greatsword':'sword'],inv=cc.Mat4.invert(new cc.Mat4(),p.model.worldMatrix),nativeLocal=cc.Vec3.transformMat4(new cc.Vec3(),b.node.worldPosition,inv),blade=cc.Vec3.transformQuat(new cc.Vec3(),new cc.Vec3(0,1,0),cc.Quat.multiply(new cc.Quat(),cc.Quat.invert(new cc.Quat(),p.model.worldRotation),b.node.worldRotation));return {id:p.renderedWeaponId,local:b.node.position,q:b.node.rotation,nativeLocal,blade,socket:p.swordCarry.socket.matrix,bone:app().actors.player.active.get('player').animation.node.getChildByPath(app().actors.player.bonePath(p.animation.node,'spine_03')).worldMatrix};}));
 }
 fs.writeFileSync(path.join(__dirname,'diagnostic.json'),JSON.stringify(rows,null,2));console.log(JSON.stringify(rows));
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
