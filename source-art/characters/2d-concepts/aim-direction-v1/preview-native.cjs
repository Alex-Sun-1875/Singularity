// Read-only reuse assessment of the project's retained native 3D actor.
const {chromium}=require('../../../../src/cocos/node_modules/playwright');
const fs=require('node:fs'),path=require('node:path');
const out=path.join(__dirname,'native-preview');fs.mkdirSync(out,{recursive:true});
(async()=>{const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true,args:['--enable-unsafe-swiftshader']});try{
 const page=await browser.newPage({viewport:{width:1280,height:900}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('http://127.0.0.1:7469/?view=3d&test=max&revision=rotation-review');await page.waitForFunction(()=>globalThis.System);
 await page.evaluate(async()=>{globalThis.cc=await System.import('cc');globalThis.app=()=>cc.director.getScene()?.getChildByName('ChapterGame')?.getComponent('ChapterGame');});
 await page.waitForFunction(()=>app()?.actors&&!app().loading||app()?.failure,undefined,{timeout:90000});
 const ready=await page.evaluate(()=>{const a=app();if(a.failure)throw Error(a.failure);a.enabled=false;a.menu='qa';a.hud.root.active=false;a.manualCameraHeight=2;a.positionCamera(1);if(!a.session.equip('W07'))throw Error('Equip failed');return a.actors.inspect().find(a=>a.id==='player');});
 const samples=[];
 for(let i=0;i<8;i++){
  const sample=await page.evaluate(i=>{const a=app(),g=a.session,r=a.camera.node.right,u=a.camera.node.up,theta=i*Math.PI/4,v={x:r.x*Math.sin(theta)+u.x*Math.cos(theta),z:r.z*Math.sin(theta)+u.z*Math.cos(theta)},angle=Math.atan2(v.x,v.z);for(let n=0;n<60;n++){g.advance(1/60,{x:0,z:0,aim:angle,attack:true});a.actors.update(g,1/60,false,false);}a.effects.update(g);a.positionCamera(1);const p=a.actors.active.get('player'),point=new cc.Vec3();a.camera.worldToScreen(p.root.worldPosition.clone().add(new cc.Vec3(0,1,0)),point);return {screenAngle:i*45,worldAngle:angle,yaw:p.root.eulerAngles.y,clip:{x:Math.max(0,Math.min(860,point.x-210)),y:Math.max(0,Math.min(350,900-point.y-300)),width:420,height:550}};},i);
  await page.waitForTimeout(70);const file=`native-bow-${i*45}.jpg`;await page.screenshot({path:path.join(out,file),type:'jpeg',quality:93,clip:sample.clip});samples.push({...sample,file});
 }
 fs.writeFileSync(path.join(out,'report.json'),JSON.stringify({scope:'existing native 3D reuse preview only, no user profile writes or asset changes',ready,samples,errors},null,2));console.log(JSON.stringify({ready,samples:samples.length,errors}));
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
