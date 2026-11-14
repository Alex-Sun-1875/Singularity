// Render the real Cocos skinned hero and projectile effects in an isolated profile.
const {chromium}=require('../../../src/cocos/node_modules/playwright');
const fs=require('node:fs'),path=require('node:path');
const out=path.join(__dirname,'runtime','animation');fs.mkdirSync(out,{recursive:true});
(async()=>{
 const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true,args:['--enable-unsafe-swiftshader']});
 try {
  const page=await browser.newPage({viewport:{width:1440,height:900}}),errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  await page.goto('http://127.0.0.1:7469/?view=2d&player=3d&test=max&revision=animation-v1');
  await page.waitForFunction(()=>globalThis.System);
  await page.evaluate(async()=>{globalThis.cc=await System.import('cc');globalThis.app=()=>cc.director.getScene()?.getChildByName('ChapterGame')?.getComponent('ChapterGame');});
  await page.waitForFunction(()=>app()?.actors&&!app().loading||app()?.failure,undefined,{timeout:90000});
  await page.evaluate(()=>{
   const a=app();if(a.failure)throw Error(a.failure);
   a.enabled=false;a.menu='';a.hud.root.active=false;a.manualCameraHeight=2;a.positionCamera(1);
   if(!a.session.equip('W07'))throw Error('Cannot equip bow');
   globalThis.angleForScreen=degrees=>{const r=a.camera.node.right,u=a.camera.node.up,t=degrees*Math.PI/180,k=u.x*u.x+u.z*u.z;return Math.atan2(r.x*Math.sin(t)+u.x*Math.cos(t)/k,r.z*Math.sin(t)+u.z*Math.cos(t)/k);};
   globalThis.advanceFrame=(degrees,attack,steps=2)=>{
    for(let n=0;n<steps;n++){
     a.process(a.session.advance(1/60,{x:0,z:0,aim:angleForScreen(degrees),attack}));
     a.actors.update(a.session,1/60,false,false,1);a.effects.update(a.session);a.positionCamera(1/60);a.flatWorld.update(a.camera,a.session);
    }
   };
   for(let n=0;n<65;n++)advanceFrame(0,true,1);
  });
  const rows=[];
  async function frame(section,degrees,attack,steps=2){
   await page.evaluate(({degrees,attack,steps})=>advanceFrame(degrees,attack,steps),{degrees,attack,steps});
   // Give Cocos one render frame after sampling the actual skeleton and effects.
   await page.waitForTimeout(22);
   const file=`frame-${String(rows.length).padStart(4,'0')}.jpg`;
   await page.screenshot({path:path.join(out,file),type:'jpeg',quality:93,clip:{x:290,y:30,width:820,height:760}});
   rows.push({file,section,screenDegrees:degrees,attack,simulationSeconds:steps/60});
  }
  for(let i=0;i<73;i++)await frame('turn',i*5,true,3);
  console.log('Captured continuous 360-degree turn');
  for(const degrees of [45,225]){
   await page.evaluate(d=>{for(let n=0;n<60;n++)advanceFrame(d,false,1);app().effects.clear();app().session.cancelInput();},degrees);
   for(let i=0;i<30;i++)await frame('draw',degrees,true);
   for(let i=0;i<24;i++)await frame('release',degrees,false);
   console.log(`Captured diagonal draw/release ${degrees}`);
  }
  if(errors.length)throw Error(errors.join('\n'));
  fs.writeFileSync(path.join(out,'frames.json'),JSON.stringify({source:'Actual current Cocos runtime, isolated test=max profile; original model, rig, animations and arrows',viewport:[1440,900],captureClip:[290,30,820,760],playbackFrameMilliseconds:50,shotPlaybackSpeed:2/3,rows,errors},null,2));
  console.log(JSON.stringify({frames:rows.length,errors}));
 } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
