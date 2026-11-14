// Actual built Cocos actors, weapons and combat effects; isolated local profile.
const {chromium}=require('../../../src/cocos/node_modules/playwright');
const fs=require('node:fs'),path=require('node:path');
const label=process.argv.includes('--before')?'before':'after',stills=process.argv.includes('--stills');
const out=path.join(__dirname,'runtime',label);fs.mkdirSync(out,{recursive:true});
const ids=['W01','W02','L01','W07','W08','L02','W11'];
(async()=>{const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true,args:['--enable-unsafe-swiftshader']});try{
 const page=await browser.newPage({viewport:{width:1440,height:900}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('http://127.0.0.1:7469/?view=2d&player=3d&test=max&revision=weapon-contact-v2');await page.waitForFunction(()=>globalThis.System);
 await page.evaluate(async()=>{globalThis.cc=await System.import('cc');globalThis.app=()=>cc.director.getScene()?.getChildByName('ChapterGame')?.getComponent('ChapterGame');});
 await page.waitForFunction(()=>app()?.actors&&!app().loading||app()?.failure,undefined,{timeout:90000});
 await page.evaluate(()=>{
  const a=app();if(a.failure)throw Error(a.failure);a.enabled=false;a.menu='';a.hud.root.active=false;a.manualCameraHeight=2.4;a.positionCamera(1);
  globalThis.heading=d=>{const r=a.camera.node.right,u=a.camera.node.up,t=d*Math.PI/180,k=u.x*u.x+u.z*u.z;return Math.atan2(r.x*Math.sin(t)+u.x*Math.cos(t)/k,r.z*Math.sin(t)+u.z*Math.cos(t)/k);};
  globalThis.step=(d,attack,dt=1/60)=>{
   a.process(a.session.advance(dt,{x:0,z:0,aim:heading(d),attack}));a.actors.update(a.session,dt,false,false,1);
   const p=a.actors.player.active.get('player'),action=a.session.state.action,clip=p.clips[p.state],anim=clip&&p.animation.getState(clip.name);
   // Native sword clips play from the engine clock in normal gameplay. Sample
   // the same clip time explicitly for deterministic slowed capture frames.
   if(anim&&p.state==='attack_sword'&&action){anim.speed=0;anim.time=Math.min(1,action.elapsed/action.duration)*clip.duration;anim.sample();}
   if(anim&&p.state==='idle'){anim.speed=0;anim.time=0;anim.sample();}
   a.effects.update(a.session);a.positionCamera(dt);a.flatWorld.update(a.camera,a.session);
  };
  globalThis.prepare=(id,d)=>{
   a.session.cancelInput();for(let i=0;i<90;i++)step(d,false);a.effects.clear();
   a.session.state.inventory[id]=Math.max(1,a.session.state.inventory[id]??0);
   if(!a.session.equip(id))throw Error('Equip failed '+id);step(d,false);
  };
  const p=a.actors.player.active.get('player');
  globalThis.qaElbow=p.animation.createSocket(a.actors.player.bonePath(p.animation.node,'lowerarm_l'));
  globalThis.qaWrist=p.animation.createSocket(a.actors.player.bonePath(p.animation.node,'hand_l'));
  globalThis.info=()=>{const p=a.actors.player.active.get('player');return {pose:p.state,action:a.session.state.action?.kind,elapsed:a.session.state.action?.elapsed,weapon:p.renderedWeaponId,visibleWeapons:Object.entries(p.weapons).filter(([k,n])=>n.active).map(([k,n])=>({kind:k,position:{...n.worldPosition}})),cameraHeight:a.camera.orthoHeight};};
  globalThis.bowAngle=()=>{
   const p=a.actors.player.active.get('player'),points=[];
   for(const r of p.weapons.bow.getComponentsInChildren(cc.MeshRenderer)){
    if(!r.node.activeInHierarchy)continue;const v=r.mesh?.readAttribute(0,'a_position');if(!v)continue;
    for(let i=0;i<v.length;i+=3){const q=cc.Vec3.transformMat4(new cc.Vec3(),new cc.Vec3(v[i],v[i+1],v[i+2]),r.node.worldMatrix);points.push([q.x,q.y,q.z]);}
   }
   const center=[0,0,0];for(const p of points)for(let j=0;j<3;j++)center[j]+=p[j]/points.length;
   const covariance=Array.from({length:3},()=>[0,0,0]);for(const p of points){const d=p.map((v,i)=>v-center[i]);for(let i=0;i<3;i++)for(let j=0;j<3;j++)covariance[i][j]+=d[i]*d[j];}
   let axis=[.2,1,.1];for(let i=0;i<20;i++){const q=covariance.map(row=>row.reduce((s,v,j)=>s+v*axis[j],0)),n=Math.hypot(...q);axis=q.map(v=>v/n);}
   const forearm=cc.Vec3.subtract(new cc.Vec3(),qaWrist.worldPosition,qaElbow.worldPosition).normalize(),dot=Math.abs(axis[0]*forearm.x+axis[1]*forearm.y+axis[2]*forearm.z);
   return {forearmVsBowLongAxisDegrees:Math.acos(Math.min(1,dot))*180/Math.PI,forearmLength:cc.Vec3.distance(qaWrist.worldPosition,qaElbow.worldPosition)};
  };
 });
 const rows=[];
 if(process.argv.includes('--inspect-variants')){
  const variants=await page.evaluate(ids=>ids.map(id=>{prepare(id,0);const p=app().actors.player.active.get('player');return {id,pose:p.state,variants:Object.values(p.weapons).flatMap(n=>n.getComponentsInChildren(cc.MeshRenderer)).filter(r=>r.node.activeInHierarchy).map(r=>({node:r.node.name,mesh:r.mesh?.uuid,vertices:r.mesh?.readAttribute(0,'a_position')?.length/3}))};}),ids);
  fs.writeFileSync(path.join(__dirname,'runtime','weapon-variants.json'),JSON.stringify(variants,null,2));console.log(JSON.stringify(variants));return;
 }
 if(process.argv.includes('--calibrate-arrow')){
  await page.evaluate(()=>{prepare('W07',0);for(let i=0;i<65;i++)step(0,true);});await page.waitForTimeout(50);
  const calibration=await page.evaluate(()=>{
   const a=app(),p=a.actors.player.active.get('player'),arrow=p.weapons.arrow,points=[];
   for(const r of arrow.getComponentsInChildren(cc.MeshRenderer)){const v=r.mesh?.readAttribute(0,'a_position');if(!v)continue;for(let i=0;i<v.length;i+=3){const q=cc.Vec3.transformMat4(new cc.Vec3(),new cc.Vec3(v[i],v[i+1],v[i+2]),r.node.worldMatrix);points.push([q.x,q.y,q.z]);}}
   const mean=[0,0,0];for(const p of points)for(let i=0;i<3;i++)mean[i]+=p[i]/points.length;
   const m=Array.from({length:3},()=>[0,0,0]);for(const p of points){const d=p.map((v,i)=>v-mean[i]);for(let i=0;i<3;i++)for(let j=0;j<3;j++)m[i][j]+=d[i]*d[j];}
   let axis=[.2,1,.1];for(let i=0;i<20;i++){const q=m.map(row=>row.reduce((s,v,j)=>s+v*axis[j],0)),n=Math.hypot(...q);axis=q.map(v=>v/n);}
   const desired=cc.Vec3.subtract(new cc.Vec3(),p.weapons.bow.worldPosition,arrow.parent.worldPosition).normalize(),actual=new cc.Vec3(...axis);if(cc.Vec3.dot(actual,desired)<0)actual.multiplyScalar(-1);
   const worldDelta=cc.Quat.rotationTo(new cc.Quat(),actual,desired),parent=arrow.parent.worldRotation,local=cc.Quat.multiply(new cc.Quat(),cc.Quat.multiply(new cc.Quat(),cc.Quat.invert(new cc.Quat(),parent),worldDelta),parent);
   const yaw=Math.atan2(desired.x,desired.z),angle=a.session.state.action.angle,error=Math.atan2(Math.sin(yaw-angle),Math.cos(yaw-angle))*180/Math.PI;
   return {arrowGripRotation:[local.x,local.y,local.z,local.w],bowLineYawErrorDegrees:error,oldYawCorrection:p.metadata.cocosBinding.bowAimYawCorrectionDegrees,actual:{...actual},desired:{...desired}};
  });
  fs.writeFileSync(path.join(__dirname,'arrow-axis-calibration.json'),JSON.stringify(calibration,null,2));console.log(JSON.stringify(calibration));return;
 }
 async function shot(file,data){await page.waitForTimeout(24);await page.screenshot({path:path.join(out,file),type:'jpeg',quality:93,clip:{x:250,y:10,width:900,height:820}});rows.push({...data,file,...await page.evaluate(()=>info()),...(stills&&['W07','W08','L02'].includes(data.id)?await page.evaluate(()=>bowAngle()):{})});}
 for(const id of ids){
  if(stills){
   for(const d of [45,135,225,315]){
    await page.evaluate(({id,d})=>{prepare(id,d);if(['W07','W08','L02'].includes(id))for(let i=0;i<65;i++)step(d,true);else{step(d,true);for(let i=0;i<10;i++)step(d,false);}}, {id,d});
    await shot(`${id}-contact-${d}.jpg`,{id,degrees:d,section:'contact'});
   }
  }else{
   let ordinal=0;
   for(const d of [45,225]){
    await page.evaluate(({id,d})=>prepare(id,d),{id,d});
    const bow=['W07','W08','L02'].includes(id);
    // One natural attack plus recovery for each visible direction. Slow
    // output to half speed without changing the underlying combat rules.
    const count=76;
    for(let i=0;i<count;i++){
     await page.evaluate(({d,attack})=>step(d,attack),{d,attack:bow?i<52:i===8});
     await shot(`${id}-${String(ordinal++).padStart(4,'0')}.jpg`,{id,degrees:d,section:bow?(i<52?'draw':'release'):'attack',index:i});
    }
   }
  }
  console.log('Captured '+id+' '+label+(stills?' contact views':' animation'));
 }
 fs.writeFileSync(path.join(out,stills?'stills.json':'frames.json'),JSON.stringify({label,source:'Actual Cocos native hero and props in isolated test profile; inventory only supplemented for presentation of owned asset variants',crop:[250,10,900,820],outputFrameMilliseconds:40,simulationFrameSeconds:1/60,rows,errors},null,2));
 if(errors.length)throw Error(errors.join('\n'));
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
