// Calibrate a native spine socket using the existing hero and actual sword meshes.
const {chromium}=require('../../../src/cocos/node_modules/playwright');
const fs=require('node:fs'),path=require('node:path');
const out=path.join(__dirname,'prototype');fs.mkdirSync(out,{recursive:true});
(async()=>{const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true,args:['--enable-unsafe-swiftshader']});try{
 const page=await browser.newPage({viewport:{width:1440,height:900}});
 await page.goto('http://127.0.0.1:7469/?view=2d&player=3d&test=max&revision=back-socket');await page.waitForFunction(()=>globalThis.System);
 await page.evaluate(async()=>{globalThis.cc=await System.import('cc');globalThis.app=()=>cc.director.getScene()?.getChildByName('ChapterGame')?.getComponent('ChapterGame');});
 await page.waitForFunction(()=>app()?.actors&&!app().loading,undefined,{timeout:90000});
 await page.evaluate(()=>{
  const a=app();a.enabled=false;a.menu='';a.hud.root.active=false;a.manualCameraHeight=2;a.positionCamera(1);
  const actor=a.actors.player.active.get('player'),owner=a.actors.player;
  globalThis.step=(d,id)=>{const r=a.camera.node.right,u=a.camera.node.up,t=d*Math.PI/180,k=u.x*u.x+u.z*u.z,angle=Math.atan2(r.x*Math.sin(t)+u.x*Math.cos(t)/k,r.z*Math.sin(t)+u.z*Math.cos(t)/k);a.session.advance(1/60,{x:0,z:0,aim:angle});a.actors.update(a.session,1/60,false);a.positionCamera(1/60);a.flatWorld.update(a.camera,a.session);};
  globalThis.equip=id=>{a.session.state.inventory[id]=1;if(!a.session.equip(id))throw Error('equip');step(0,id);};
  const bonePath=owner.bonePath(actor.animation.node,'spine_03'),bone=actor.animation.node.getChildByPath(bonePath),socket=actor.animation.createSocket(bonePath);
  globalThis.mount=(id,position,blade)=>{
   const grip=actor.weapons[id==='L01'?'greatsword':'sword'];
   const world=cc.Vec3.transformMat4(new cc.Vec3(),new cc.Vec3(...position),actor.model.worldMatrix),local=cc.Vec3.transformMat4(new cc.Vec3(),world,cc.Mat4.invert(new cc.Mat4(),bone.worldMatrix));
   const y=new cc.Vec3(...blade).normalize(),z=new cc.Vec3(0,0,-1),x=cc.Vec3.cross(new cc.Vec3(),y,z).normalize(),q=cc.Quat.fromAxes(new cc.Quat(),x,y,z),localQ=cc.Quat.multiply(new cc.Quat(),cc.Quat.invert(new cc.Quat(),bone.worldRotation),cc.Quat.multiply(new cc.Quat(),actor.model.worldRotation,q));
   grip.setParent(socket);grip.setPosition(local);grip.setRotation(localQ);
   return {position,blade,localPosition:{...local},localRotation:{...localQ}};
  };
 });
 const rows=[];
 for(const id of ['W01','W02','L01']){
  const mount=await page.evaluate(id=>{equip(id);return mount(id,id==='L01'?[-.22,1.60,-.255]:[-.20,1.55,-.235],id==='L01'?[.34,-.94,0]:[.38,-.925,0]);},id);
  for(const d of [0,90,180,270]){await page.evaluate(d=>step(d),d);await page.waitForTimeout(40);const file=`${id}-${d}.jpg`;await page.screenshot({path:path.join(out,file),type:'jpeg',quality:93,clip:{x:300,y:60,width:800,height:760}});rows.push({id,d,file,mount});}
 }
 fs.writeFileSync(path.join(out,'mounts.json'),JSON.stringify(rows,null,2));console.log('Back socket preview captured');
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
