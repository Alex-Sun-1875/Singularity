// Actual native model/arrow verification in the existing isolated test profile.
const {chromium}=require('../../../src/cocos/node_modules/playwright');
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const out=path.join(__dirname,'runtime','aim-verification');fs.mkdirSync(out,{recursive:true});
(async()=>{const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true,args:['--enable-unsafe-swiftshader']});try{
 const page=await browser.newPage({viewport:{width:1440,height:900}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto((process.env.WEAPONS_REVIEW_URL??'http://127.0.0.1:7469/')+'?view=2d&player=3d&test=max&revision=weapons-final');await page.waitForFunction(()=>globalThis.System);
 await page.evaluate(async()=>{globalThis.cc=await System.import('cc');globalThis.app=()=>cc.director.getScene()?.getChildByName('ChapterGame')?.getComponent('ChapterGame');});
 await page.waitForFunction(()=>app()?.actors&&!app().loading||app()?.failure,undefined,{timeout:90000});assert.equal(await page.evaluate(()=>app().failure),'');
 const initial=await page.evaluate(()=>{const a=app();a.enabled=false;a.menu='';a.hud.root.active=false;a.manualCameraHeight=2;a.positionCamera(1);if(!a.session.equip('W07'))throw Error('Bow equip failed');return {actors:a.actors.inspect(),paintedWorld:!!a.flatWorld,flatPortrait:a.hud.flatMode,heroInFlatCast:a.actors.cast.active.has('player')};});
 assert.ok(initial.paintedWorld);assert.equal(initial.heroInFlatCast,false);assert.equal(initial.flatPortrait,false);assert.ok(initial.actors.find(a=>a.id==='player').skeletons.every(n=>n===67));
 await page.evaluate(()=>{
  globalThis.angleForScreen=degrees=>{const a=app(),r=a.camera.node.right,u=a.camera.node.up,t=degrees*Math.PI/180,k=u.x*u.x+u.z*u.z;return Math.atan2(r.x*Math.sin(t)+u.x*Math.cos(t)/k,r.z*Math.sin(t)+u.z*Math.cos(t)/k);};
  globalThis.step=(input,dt=1/60)=>{const a=app();a.process(a.session.advance(dt,{x:0,z:0,...input}));a.actors.update(a.session,dt,!!input.x||!!input.z,false,Math.hypot(input.x||0,input.z||0)||1);a.effects.update(a.session);a.positionCamera(dt);a.flatWorld.update(a.camera,a.session);};
  globalThis.inspectArrow=()=>{
   const a=app(),p=a.actors.player.active.get('player'),arrow=p.weapons.arrow,points=[];
   for(const renderer of arrow.getComponentsInChildren(cc.MeshRenderer)){
    const v=renderer.mesh?.readAttribute(0,'a_position');if(!v)continue;
    for(let i=0;i<v.length;i+=3){const q=cc.Vec3.transformMat4(new cc.Vec3(),new cc.Vec3(v[i],v[i+1],v[i+2]),renderer.node.worldMatrix);points.push([q.x,q.y,q.z]);}
   }
   const center=[0,0,0];for(const p of points)for(let j=0;j<3;j++)center[j]+=p[j]/points.length;
   const matrix=Array.from({length:3},()=>[0,0,0]);for(const p of points){const q=p.map((v,j)=>v-center[j]);for(let i=0;i<3;i++)for(let j=0;j<3;j++)matrix[i][j]+=q[i]*q[j];}
   let axis=[1,.5,.3];for(let n=0;n<15;n++){const next=matrix.map(row=>row.reduce((s,v,i)=>s+v*axis[i],0)),norm=Math.hypot(...next);axis=next.map(v=>v/norm);}
   const angle=a.session.state.action?.angle??a.session.state.player.angle,forward=[Math.sin(angle),0,Math.cos(angle)],dot=axis.reduce((sum,v,j)=>sum+v*forward[j],0),angleError=Math.acos(Math.min(1,Math.abs(dot)))*180/Math.PI;
   const sign=dot<0?-1:1,arrowYaw=Math.atan2(axis[0]*sign,axis[2]*sign),yawError=Math.abs(Math.atan2(Math.sin(arrowYaw-angle),Math.cos(arrowYaw-angle)))*180/Math.PI;
   const point=new cc.Vec3();a.camera.worldToScreen(p.root.worldPosition.clone().add(new cc.Vec3(0,.9,0)),point);
   return {angle,yaw:p.root.eulerAngles.y,modelEuler:{...p.model.eulerAngles},axis,angleError,yawError,center,arrowActive:arrow.active,pose:p.state,clip:{x:Math.max(0,Math.min(960,point.x-240)),y:Math.max(0,Math.min(340,900-point.y-320)),width:480,height:560}};
  };
  for(let n=0;n<65;n++)step({aim:angleForScreen(0),attack:true});
 });
 const turns=[];
 for(let degrees=0;degrees<=360;degrees+=5){
  await page.evaluate(d=>step({aim:angleForScreen(d),attack:true}),degrees);await page.waitForTimeout(20);const sample=await page.evaluate(()=>inspectArrow());
  const error=Math.abs(Math.atan2(Math.sin(sample.yaw*Math.PI/180-sample.angle),Math.cos(sample.yaw*Math.PI/180-sample.angle)));assert.ok(error<1e-5);turns.push({screenDegrees:degrees,...sample});
  if(degrees%45===0&&degrees<360){await page.screenshot({path:path.join(out,`aim-${degrees}.jpg`),type:'jpeg',quality:94,clip:sample.clip});}
 }
 const shots=[];
 for(const degrees of [0,45,90,135,180,225,270,315,13]){
  await page.evaluate(d=>{const a=app();a.session.cancelInput();a.effects.clear();for(let n=0;n<65;n++)step({aim:angleForScreen(d),attack:true});},degrees);await page.waitForTimeout(25);
  const frames=[];
  for(let i=0;i<48;i++){
   const sample=await page.evaluate(({d,i})=>{const a=app();step({aim:angleForScreen(i<7?d:d+75),attack:false});const p=a.actors.player.active.get('player'),q=a.session.state.projectiles.find(q=>q.owner==='player'&&q.kind==='arrow'),body=q&&a.effects.bodies.find(b=>b.key===q.id),forward=body&&cc.Vec3.transformQuat(new cc.Vec3(),new cc.Vec3(0,0,1),body.node.worldRotation);return {i,action:a.session.state.action?.kind,lockedAngle:a.session.state.action?.angle,yaw:p.root.eulerAngles.y,height:a.camera.orthoHeight,shot:q&&body?{id:q.id,age:q.age,angle:q.angle,position:{...body.node.worldPosition},forward:{...forward}}:null};},{d:degrees,i});frames.push(sample);
   if(i===2){await page.waitForTimeout(25);await page.screenshot({path:path.join(out,`release-${degrees}.jpg`),type:'jpeg',quality:92});}
  }
  shots.push({screenDegrees:degrees,frames});
 }
 await page.evaluate(()=>{const a=app();a.session.cancelInput();a.menu='';a.modalKey='';a.renderModal();a.hud.root.active=true;});await page.mouse.click(720,450);await page.keyboard.press('b');await page.waitForTimeout(120);await page.screenshot({path:path.join(out,'inventory.jpg'),type:'jpeg',quality:91});
 const preview=await page.evaluate(()=>{const stage=cc.director.getScene().getChildByName('CharacterPreviewStage');return {nativePreview:!!stage,skins:stage?.getComponentsInChildren(cc.SkinnedMeshRenderer).length??0,menu:app().menu};});
 fs.writeFileSync(path.join(out,'report.json'),JSON.stringify({initial,turns,shots,preview,errors},null,2));assert.ok(preview.nativePreview&&preview.skins>0);assert.deepEqual(errors,[]);
 console.log(JSON.stringify({turns:turns.length,maxHeldArrowYawError:Math.max(...turns.map(x=>x.yawError)),authoredArrowPitch:Math.max(...turns.map(x=>x.angleError)),shots:shots.length,preview,errors}));
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
