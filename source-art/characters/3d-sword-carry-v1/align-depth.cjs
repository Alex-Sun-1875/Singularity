// Visual calibration only; production uses the manifest values after review.
const {chromium}=require('../../../src/cocos/node_modules/playwright');
const fs=require('node:fs'),path=require('node:path');
(async()=>{const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true,args:['--enable-unsafe-swiftshader']});try{
 const page=await browser.newPage({viewport:{width:1440,height:900}});
 await page.goto('http://127.0.0.1:7469/?view=2d&player=3d&test=max');await page.waitForFunction(()=>globalThis.System);
 await page.evaluate(async()=>{globalThis.cc=await System.import('cc');globalThis.app=()=>cc.director.getScene()?.getChildByName('ChapterGame')?.getComponent('ChapterGame');});
 await page.waitForFunction(()=>app()?.actors&&!app().loading,undefined,{timeout:90000});
 await page.evaluate(()=>{const a=app();a.enabled=false;a.menu='';a.hud.root.active=false;a.manualCameraHeight=2;a.session.state.inventory.W01=1;if(!a.session.equip('W01'))throw Error('equip W01');a.actors.update(a.session,1/30,false);a.positionCamera(1);
  const p=a.actors.player.active.get('player'),idle=p.animation.getState(p.clips.idle.name);idle.speed=0;idle.time=1/30;idle.sample();idle.time=0;idle.sample();globalThis.calibration={bone:p.animation.node.getChildByPath(a.actors.player.bonePath(p.animation.node,'spine_03')).worldMatrix.clone(),socket:p.swordCarry.socket.worldMatrix.clone(),model:p.model.worldMatrix.clone()};
  globalThis.pose=(z,d)=>{const p=a.actors.player.active.get('player'),o=a.actors.player,b=p.swordCarry.grips.sword,definition=p.metadata.cocosBinding.swordBackCarry.items.W01;
   const bone=p.animation.node.getChildByPath(o.bonePath(p.animation.node,'spine_03'));
   const world=cc.Vec3.transformMat4(new cc.Vec3(),new cc.Vec3(definition.position[0],definition.position[1],z),calibration.model);
   b.items.W01.position=cc.Vec3.transformMat4(new cc.Vec3(),world,cc.Mat4.invert(new cc.Mat4(),calibration.socket));
   const y=new cc.Vec3(...definition.blade),n=new cc.Vec3(...definition.normal),x=cc.Vec3.cross(new cc.Vec3(),y,n).normalize(),q=cc.Quat.fromAxes(new cc.Quat(),x,y,n),socketQ=cc.Mat4.getRotation(new cc.Quat(),calibration.socket),modelQ=cc.Mat4.getRotation(new cc.Quat(),calibration.model);
   b.items.W01.rotation=cc.Quat.multiply(new cc.Quat(),cc.Quat.invert(new cc.Quat(),socketQ),cc.Quat.multiply(new cc.Quat(),modelQ,q));b.item='';
   const r=a.camera.node.right,u=a.camera.node.up,t=d*Math.PI/180,k=u.x*u.x+u.z*u.z,angle=Math.atan2(r.x*Math.sin(t)+u.x*Math.cos(t)/k,r.z*Math.sin(t)+u.z*Math.cos(t)/k);
   a.session.advance(1/30,{x:0,z:0,aim:angle});a.actors.update(a.session,1/30,false);idle.speed=0;idle.time=1/30;idle.sample();idle.time=0;idle.sample();a.positionCamera(1);a.flatWorld.update(a.camera,a.session);
  };
 });
 const out=path.join(__dirname,'depth-calibration');fs.mkdirSync(out,{recursive:true});
 fs.writeFileSync(path.join(out,'matrices.json'),JSON.stringify(await page.evaluate(()=>calibration),null,2));
 for(const z of [-.24,-.26,-.28,-.3])for(const d of [0,90,180,270]){await page.evaluate(([z,d])=>pose(z,d),[z,d]);await page.waitForTimeout(75);await page.screenshot({path:path.join(out,`${z}-${d}.jpg`),type:'jpeg',quality:94,clip:{x:440,y:180,width:480,height:520}});}
 console.log('Depth views saved');
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
